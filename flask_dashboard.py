from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_cors import CORS
import pandas as pd
import json
import os
from datetime import datetime, timedelta
import logging
from dotenv import load_dotenv
from data_integration import MCADataIntegrator
from change_detection import ChangeDetector
from cin_enrichment import CINEnricher
from ai_insights import AIInsightsEngine
from postgresql_config import postgres_config
from config import *

# Load environment variables
load_dotenv()

# Configure logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/mca_insights.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'mca_insights_secret_key_2024')
app.config['SESSION_COOKIE_SECURE'] = os.getenv('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Security headers
@app.after_request
def after_request(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    if os.getenv('FLASK_ENV') == 'production':
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

CORS(app)

# Initialize components
integrator = MCADataIntegrator()
detector = ChangeDetector()
enricher = CINEnricher()
ai_engine = AIInsightsEngine()

def validate_input(data, field_type='string', max_length=255):
    """Validate and sanitize input data"""
    if not data:
        return None
    
    if field_type == 'string':
        # Remove any potentially dangerous characters
        sanitized = str(data).strip()[:max_length]
        # Basic SQL injection prevention
        dangerous_chars = [';', '--', '/*', '*/', 'xp_', 'sp_']
        for char in dangerous_chars:
            if char in sanitized.lower():
                raise ValueError(f"Invalid input detected: {char}")
        return sanitized
    
    elif field_type == 'int':
        try:
            return int(data)
        except (ValueError, TypeError):
            raise ValueError("Invalid integer input")
    
    elif field_type == 'date':
        try:
            return datetime.strptime(str(data), '%Y-%m-%d').date()
        except ValueError:
            raise ValueError("Invalid date format. Use YYYY-MM-DD")
    
    return data

def validate_search_params(search_term=None, state=None, status=None, year=None, limit=100):
    """Validate search parameters"""
    try:
        validated_params = {}
        
        if search_term:
            validated_params['search_term'] = validate_input(search_term, 'string', 100)
        
        if state:
            validated_params['state'] = validate_input(state, 'string', 50)
        
        if status:
            validated_params['status'] = validate_input(status, 'string', 50)
        
        if year:
            validated_params['year'] = validate_input(year, 'int')
        
        validated_params['limit'] = min(validate_input(limit, 'int'), 1000)  # Max 1000 results
        
        return validated_params
    except ValueError as e:
        raise ValueError(f"Invalid search parameters: {str(e)}")

def get_database_connection():
    """Get PostgreSQL database connection"""
    return postgres_config.get_connection()

def get_database_engine():
    """Get SQLAlchemy engine for pandas operations"""
    return postgres_config.get_engine()

@app.route('/')
def index():
    """Main dashboard page"""
    try:
        # Get basic statistics
        stats = get_dashboard_statistics()
        
        # Get recent changes
        recent_changes = get_recent_changes(limit=10)
        
        # Get company distribution by state
        state_distribution = get_company_distribution_by_state()
        
        # Get company distribution by status
        status_distribution = get_company_distribution_by_status()
        
        return render_template('index.html', 
                             stats=stats,
                             recent_changes=recent_changes,
                             state_distribution=state_distribution,
                             status_distribution=status_distribution)
    except Exception as e:
        logger.error(f"Error in index route: {str(e)}")
        flash('Error loading dashboard data', 'error')
        return render_template('index.html', 
                             stats={},
                             recent_changes=[],
                             state_distribution=[],
                             status_distribution=[])

@app.route('/search')
def search():
    """Company search page"""
    try:
        # Validate and sanitize input parameters
        search_term = validate_input(request.args.get('q', ''), 'string', 100)
        state_filter = validate_input(request.args.get('state', ''), 'string', 50)
        status_filter = validate_input(request.args.get('status', ''), 'string', 50)
        year_filter = validate_input(request.args.get('year', ''), 'string', 10)
        
        # Get filter options
        states = get_available_states()
        statuses = get_available_statuses()
        years = get_available_years()
        
        # Search companies with validated parameters
        companies = search_companies(search_term, state_filter, status_filter, year_filter)
        
        return render_template('search.html',
                             companies=companies,
                             search_term=search_term,
                             state_filter=state_filter,
                             status_filter=status_filter,
                             year_filter=year_filter,
                             states=states,
                             statuses=statuses,
                             years=years)
    except ValueError as e:
        logger.warning(f"Invalid search parameters: {str(e)}")
        flash(f'Invalid search parameters: {str(e)}', 'error')
        return redirect(url_for('search'))
    except Exception as e:
        logger.error(f"Error in search route: {str(e)}")
        flash('An error occurred while searching. Please try again.', 'error')
        return redirect(url_for('search'))

@app.route('/company/<cin>')
def company_details(cin):
    """Company details page"""
    try:
        company = get_company_by_cin(cin)
        if not company:
            flash('Company not found', 'error')
            return redirect(url_for('search'))
        
        changes = get_company_changes(cin)
        enriched_data = get_company_enriched_data(cin)
        
        return render_template('company_details.html',
                             company=company,
                             changes=changes,
                             enriched_data=enriched_data)
    except Exception as e:
        logger.error(f"Error in company_details route: {str(e)}")
        flash('Error loading company details', 'error')
        return redirect(url_for('search'))

@app.route('/changes')
def changes():
    """Change analysis page"""
    date_from = request.args.get('date_from', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))
    change_type = request.args.get('change_type', '')
    
    changes_data = get_changes_data(date_from, date_to, change_type)
    change_summary = get_change_summary(date_from, date_to)
    change_trends = get_change_trends(date_from, date_to)
    
    return render_template('changes.html',
                         changes_data=changes_data,
                         change_summary=change_summary,
                         change_trends=change_trends,
                         date_from=date_from,
                         date_to=date_to,
                         change_type=change_type)

@app.route('/enrichment')
def enrichment():
    """Data enrichment page"""
    enrichment_stats = get_enrichment_statistics()
    enriched_companies = get_enriched_companies()
    sector_distribution = get_sector_distribution()
    
    return render_template('enrichment.html',
                         enrichment_stats=enrichment_stats,
                         enriched_companies=enriched_companies,
                         sector_distribution=sector_distribution)

@app.route('/reports')
def reports():
    """Reports page"""
    reports_list = get_available_reports()
    return render_template('reports.html', reports=reports_list)

@app.route('/api/search_company', methods=['GET', 'POST'])
def api_search_company():
    """API endpoint for company search"""
    try:
        if request.method == 'POST':
            data = request.get_json()
            search_term = data.get('search_term', '')
            state = data.get('state', '')
            status = data.get('status', '')
            year = data.get('year', '')
            limit = data.get('limit', 100)
        else:
            search_term = request.args.get('search_term', '')
            state = request.args.get('state', '')
            status = request.args.get('status', '')
            year = request.args.get('year', '')
            limit = int(request.args.get('limit', 100))
        
        companies = search_companies(search_term, state, status, year, limit)
        
        return jsonify({
            "success": True,
            "count": len(companies),
            "results": companies
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/ai/chat', methods=['POST'])
def api_ai_chat():
    """API endpoint for AI chat"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        
        if not query:
            return jsonify({
                "success": False,
                "error": "Query is required"
            }), 400
        
        response = ai_engine.chat_with_data(query)
        
        return jsonify({
            "success": True,
            "query": query,
            "response": response
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/ai/summary', methods=['GET', 'POST'])
def api_ai_summary():
    """API endpoint for AI summary generation"""
    try:
        if request.method == 'POST':
            data = request.get_json()
            date = data.get('date', datetime.now().strftime('%Y-%m-%d'))
        else:
            date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        
        summary = ai_engine.generate_daily_summary(date)
        
        return jsonify({
            "success": True,
            "date": date,
            "summary": summary
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

def get_dashboard_statistics():
    """Get dashboard statistics"""
    try:
        engine = get_database_engine()
        
        total_query = "SELECT COUNT(*) as total FROM companies"
        total_result = pd.read_sql_query(total_query, engine)
        total_companies = total_result.iloc[0]['total']
        
        active_query = "SELECT COUNT(*) as active FROM companies WHERE COMPANY_STATUS = 'Active'"
        active_result = pd.read_sql_query(active_query, engine)
        active_companies = active_result.iloc[0]['active']
        
        recent_changes_query = """
            SELECT COUNT(*) as changes 
            FROM change_logs 
            WHERE CHANGE_DATE >= NOW() - INTERVAL '7 days'
        """
        recent_result = pd.read_sql_query(recent_changes_query, engine)
        recent_changes = recent_result.iloc[0]['changes']
        
        enriched_query = "SELECT COUNT(*) as enriched FROM enriched_data"
        enriched_result = pd.read_sql_query(enriched_query, engine)
        enriched_companies = enriched_result.iloc[0]['enriched']
        
        inactive_query = "SELECT COUNT(*) as inactive FROM companies WHERE COMPANY_STATUS != 'Active'"
        inactive_result = pd.read_sql_query(inactive_query, engine)
        inactive_companies = inactive_result.iloc[0]['inactive']
        
        return {
            'total_companies': total_companies,
            'active_companies': active_companies,
            'inactive_companies': inactive_companies,
            'recent_changes': recent_changes,
            'enriched_companies': enriched_companies
        }
    except Exception as e:
        logger.error(f"Error getting dashboard statistics: {str(e)}")
        return {}

def get_recent_changes(limit=10):
    """Get recent changes"""
    try:
        engine = get_database_engine()
        query = """
            SELECT cl.*, c.COMPANY_NAME, c.STATE 
            FROM change_logs cl
            LEFT JOIN companies c ON cl.CIN = c.CIN
            ORDER BY cl.CHANGE_DATE DESC
            LIMIT %s
        """
        df = pd.read_sql_query(query, engine, params=[limit])
        return df.to_dict('records')
    except Exception as e:
        logger.error(f"Error getting recent changes: {str(e)}")
        return []

def get_company_distribution_by_state():
    """Get company distribution by state"""
    try:
        engine = get_database_engine()
        query = "SELECT STATE, COUNT(*) as count FROM companies GROUP BY STATE ORDER BY count DESC"
        df = pd.read_sql_query(query, engine)
        return df.to_dict('records')
    except Exception as e:
        logger.error(f"Error getting state distribution: {str(e)}")
        return []

def get_company_distribution_by_status():
    """Get company distribution by status"""
    try:
        engine = get_database_engine()
        query = "SELECT COMPANY_STATUS, COUNT(*) as count FROM companies GROUP BY COMPANY_STATUS ORDER BY count DESC"
        df = pd.read_sql_query(query, engine)
        return df.to_dict('records')
    except Exception as e:
        logger.error(f"Error getting status distribution: {str(e)}")
        return []

def search_companies(search_term='', state='', status='', year='', limit=100):
    """Search companies with filters"""
    try:
        engine = get_database_engine()
        
        query = "SELECT * FROM companies WHERE 1=1"
        params = []
        
        if search_term:
            query += " AND (CIN ILIKE %s OR COMPANY_NAME ILIKE %s)"
            params.extend([f"%{search_term}%", f"%{search_term}%"])
        
        if state:
            query += " AND STATE = %s"
            params.append(state)
        
        if status:
            query += " AND COMPANY_STATUS = %s"
            params.append(status)
        
        if year and year.isdigit():
            query += " AND EXTRACT(YEAR FROM DATE_OF_INCORPORATION) = %s"
            params.append(int(year))
        
        query += f" ORDER BY LAST_UPDATED DESC LIMIT {limit}"
        
        df = pd.read_sql_query(query, engine, params=params if params else None)
        return df.to_dict('records')
    except Exception as e:
        logger.error(f"Error searching companies: {str(e)}")
        return []

def get_available_states():
    """Get available states"""
    try:
        engine = get_database_engine()
        query = "SELECT DISTINCT STATE FROM companies ORDER BY STATE"
        df = pd.read_sql_query(query, engine)
        return [row['state'] for row in df.to_dict('records')]
    except Exception as e:
        logger.error(f"Error getting states: {str(e)}")
        return []

def get_available_statuses():
    """Get available statuses"""
    try:
        engine = get_database_engine()
        query = "SELECT DISTINCT COMPANY_STATUS FROM companies ORDER BY COMPANY_STATUS"
        df = pd.read_sql_query(query, engine)
        return [row['company_status'] for row in df.to_dict('records')]
    except Exception as e:
        logger.error(f"Error getting statuses: {str(e)}")
        return []

def get_available_years():
    """Get available years"""
    try:
        engine = get_database_engine()
        query = """
            SELECT DISTINCT EXTRACT(YEAR FROM DATE_OF_INCORPORATION) as year 
            FROM companies 
            WHERE DATE_OF_INCORPORATION IS NOT NULL 
            ORDER BY year DESC
        """
        df = pd.read_sql_query(query, engine)
        return [int(row['year']) for row in df.to_dict('records') if row['year']]
    except Exception as e:
        logger.error(f"Error getting years: {str(e)}")
        return []

def get_company_by_cin(cin):
    """Get company by CIN"""
    try:
        conn = get_database_connection()
        query = "SELECT * FROM companies WHERE CIN = %s"
        df = pd.read_sql_query(query, conn, params=[cin])
        conn.close()
        return df.iloc[0].to_dict() if not df.empty else None
    except Exception as e:
        logger.error(f"Error getting company by CIN: {str(e)}")
        return None

def get_company_changes(cin):
    """Get company changes"""
    try:
        conn = get_database_connection()
        query = "SELECT * FROM change_logs WHERE CIN = %s ORDER BY CHANGE_DATE DESC"
        df = pd.read_sql_query(query, conn, params=[cin])
        conn.close()
        return df.to_dict('records')
    except Exception as e:
        logger.error(f"Error getting company changes: {str(e)}")
        return []

def get_company_enriched_data(cin):
    """Get company enriched data"""
    try:
        conn = get_database_connection()
        query = "SELECT * FROM enriched_data WHERE CIN = %s"
        df = pd.read_sql_query(query, conn, params=[cin])
        conn.close()
        return df.iloc[0].to_dict() if not df.empty else {}
    except Exception as e:
        logger.error(f"Error getting enriched data: {str(e)}")
        return {}

def get_changes_data(date_from, date_to, change_type=''):
    """Get changes data"""
    try:
        conn = get_database_connection()
        
        query = """
            SELECT cl.*, c.COMPANY_NAME, c.STATE 
            FROM change_logs cl
            LEFT JOIN companies c ON cl.CIN = c.CIN
            WHERE DATE(cl.CHANGE_DATE) BETWEEN %s AND %s
        """
        params = [date_from, date_to]
        
        if change_type:
            query += " AND cl.CHANGE_TYPE = %s"
            params.append(change_type)
        
        query += " ORDER BY cl.CHANGE_DATE DESC"
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df.to_dict('records')
    except Exception as e:
        logger.error(f"Error getting changes data: {str(e)}")
        return []

def get_change_summary(date_from, date_to):
    """Get change summary"""
    try:
        conn = get_database_connection()
        
        query = """
            SELECT 
                CHANGE_TYPE,
                COUNT(*) as count
            FROM change_logs 
            WHERE DATE(CHANGE_DATE) BETWEEN %s AND %s
            GROUP BY CHANGE_TYPE
        """
        df = pd.read_sql_query(query, conn, params=[date_from, date_to])
        conn.close()
        return df.to_dict('records')
    except Exception as e:
        logger.error(f"Error getting change summary: {str(e)}")
        return []

def get_change_trends(date_from, date_to):
    """Get change trends"""
    try:
        conn = get_database_connection()
        
        query = """
            SELECT 
                DATE(CHANGE_DATE) as date,
                CHANGE_TYPE,
                COUNT(*) as count
            FROM change_logs 
            WHERE DATE(CHANGE_DATE) BETWEEN %s AND %s
            GROUP BY DATE(CHANGE_DATE), CHANGE_TYPE
            ORDER BY date DESC
        """
        df = pd.read_sql_query(query, conn, params=[date_from, date_to])
        conn.close()
        return df.to_dict('records')
    except Exception as e:
        logger.error(f"Error getting change trends: {str(e)}")
        return []

def get_enrichment_statistics():
    """Get enrichment statistics"""
    try:
        conn = get_database_connection()
        
        query = """
            SELECT 
                COUNT(*) as total_enriched,
                COUNT(CASE WHEN SECTOR != '' THEN 1 END) as with_sector,
                COUNT(CASE WHEN INDUSTRY != '' THEN 1 END) as with_industry,
                COUNT(CASE WHEN DIRECTOR_NAMES != '' THEN 1 END) as with_directors,
                COUNT(CASE WHEN COMPANY_WEBSITE != '' THEN 1 END) as with_website
            FROM enriched_data
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df.iloc[0].to_dict() if not df.empty else {}
    except Exception as e:
        logger.error(f"Error getting enrichment statistics: {str(e)}")
        return {}

def get_enriched_companies():
    """Get enriched companies"""
    try:
        conn = get_database_connection()
        query = """
            SELECT e.*, c.COMPANY_NAME, c.STATE, c.COMPANY_STATUS
            FROM enriched_data e
            LEFT JOIN companies c ON e.CIN = c.CIN
            ORDER BY e.ENRICHMENT_DATE DESC
            LIMIT 50
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df.to_dict('records')
    except Exception as e:
        logger.error(f"Error getting enriched companies: {str(e)}")
        return []

def get_sector_distribution():
    """Get sector distribution"""
    try:
        conn = get_database_connection()
        query = """
            SELECT SECTOR, COUNT(*) as count 
            FROM enriched_data 
            WHERE SECTOR != ''
            GROUP BY SECTOR
            ORDER BY count DESC
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df.to_dict('records')
    except Exception as e:
        logger.error(f"Error getting sector distribution: {str(e)}")
        return []

def get_available_reports():
    """Get available reports"""
    reports_dir = "reports"
    reports = []
    
    if os.path.exists(reports_dir):
        for file in os.listdir(reports_dir):
            if file.endswith(('.txt', '.json')):
                file_path = os.path.join(reports_dir, file)
                file_stat = os.stat(file_path)
                reports.append({
                    'name': file,
                    'path': file_path,
                    'size': file_stat.st_size,
                    'modified': datetime.fromtimestamp(file_stat.st_mtime)
                })
    
    return sorted(reports, key=lambda x: x['modified'], reverse=True)

if __name__ == '__main__':
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    os.makedirs('reports', exist_ok=True)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
