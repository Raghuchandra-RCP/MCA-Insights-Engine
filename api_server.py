
from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
from datetime import datetime, timedelta
import json
import os
from data_integration import MCADataIntegrator
from change_detection import ChangeDetector
from cin_enrichment import CINEnricher
from ai_insights import AIInsightsEngine
from postgresql_config import postgres_config
from config import *

app = Flask(__name__)
CORS(app)

integrator = MCADataIntegrator()
detector = ChangeDetector()
enricher = CINEnricher()
ai_engine = AIInsightsEngine()

def get_database_connection():
    return postgres_config.get_connection()

@app.route('/')
def home():
    return jsonify({
        "message": "MCA Insights Engine API",
        "version": "1.0.0",
        "endpoints": {
            "search_company": "/search_company",
            "get_company_details": "/company/<cin>",
            "get_changes": "/changes",
            "get_statistics": "/statistics",
            "get_enriched_data": "/enriched",
            "ai_chat": "/ai/chat",
            "generate_summary": "/ai/summary"
        }
    })

@app.route('/search_company', methods=['GET', 'POST'])
def search_company():
    try:
        if request.method == 'POST':
            data = request.get_json()
            search_term = data.get('search_term', '')
            state = data.get('state', '')
            status = data.get('status', '')
            limit = data.get('limit', 100)
        else:
            search_term = request.args.get('search_term', '')
            state = request.args.get('state', '')
            status = request.args.get('status', '')
            limit = int(request.args.get('limit', 100))
        
        conn = get_database_connection()
        
        # Build query
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
        
        query += f" ORDER BY LAST_UPDATED DESC LIMIT {limit}"
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        # Convert to JSON - handle int64 serialization
        results = df.to_dict('records')
        
        # Convert numpy int64 to Python int for JSON serialization
        for result in results:
            for key, value in result.items():
                if hasattr(value, 'item'):  # numpy scalar
                    result[key] = value.item()
        
        return jsonify({
            "success": True,
            "count": len(results),
            "results": results
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/company/<cin>')
def get_company_details(cin):
    """Get detailed information for a specific company by CIN"""
    try:
        conn = get_database_connection()
        
        company_query = "SELECT * FROM companies WHERE CIN = %s"
        company_df = pd.read_sql_query(company_query, conn, params=[cin])
        
        if company_df.empty:
            return jsonify({
                "success": False,
                "error": "Company not found"
            }), 404
        
        company = company_df.iloc[0].to_dict()
        
        changes_query = "SELECT * FROM change_logs WHERE CIN = %s ORDER BY CHANGE_DATE DESC"
        changes_df = pd.read_sql_query(changes_query, conn, params=[cin])
        changes = changes_df.to_dict('records')
        
        enriched_query = "SELECT * FROM enriched_data WHERE CIN = %s"
        enriched_df = pd.read_sql_query(enriched_query, conn, params=[cin])
        enriched = enriched_df.iloc[0].to_dict() if not enriched_df.empty else {}
        
        conn.close()
        
        return jsonify({
            "success": True,
            "company": company,
            "changes": changes,
            "enriched_data": enriched
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/changes')
def get_changes():
    """Get change logs with optional filtering"""
    try:
        change_type = request.args.get('change_type', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        limit = int(request.args.get('limit', 100))
        
        conn = get_database_connection()
        
        query = """
            SELECT cl.*, c.COMPANY_NAME, c.STATE 
            FROM change_logs cl
            LEFT JOIN companies c ON cl.CIN = c.CIN
            WHERE 1=1
        """
        params = []
        
        if change_type:
            query += " AND cl.CHANGE_TYPE = %s"
            params.append(change_type)
        
        if date_from:
            query += " AND DATE(cl.CHANGE_DATE) >= %s"
            params.append(date_from)
        
        if date_to:
            query += " AND DATE(cl.CHANGE_DATE) <= %s"
            params.append(date_to)
        
        query += f" ORDER BY cl.CHANGE_DATE DESC LIMIT {limit}"
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        results = df.to_dict('records')
        
        return jsonify({
            "success": True,
            "count": len(results),
            "results": results
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/statistics')
def get_statistics():
    """Get overall statistics about the MCA data"""
    try:
        conn = get_database_connection()
        
        total_query = "SELECT COUNT(*) as total FROM companies"
        total_result = pd.read_sql_query(total_query, conn)
        total_companies = total_result.iloc[0]['total']
        
        status_query = "SELECT COMPANY_STATUS, COUNT(*) as count FROM companies GROUP BY COMPANY_STATUS"
        status_df = pd.read_sql_query(status_query, conn)
        status_distribution = status_df.to_dict('records')
        
        state_query = "SELECT STATE, COUNT(*) as count FROM companies GROUP BY STATE ORDER BY count DESC"
        state_df = pd.read_sql_query(state_query, conn)
        state_distribution = state_df.to_dict('records')
        
        recent_changes_query = """
            SELECT COUNT(*) as count 
            FROM change_logs 
            WHERE CHANGE_DATE >= NOW() - INTERVAL '7 days'
        """
        recent_changes_result = pd.read_sql_query(recent_changes_query, conn)
        recent_changes = recent_changes_result.iloc[0]['count']
        
        enriched_query = "SELECT COUNT(*) as count FROM enriched_data"
        enriched_result = pd.read_sql_query(enriched_query, conn)
        enriched_count = enriched_result.iloc[0]['count']
        
        conn.close()
        
        return jsonify({
            "success": True,
            "statistics": {
                "total_companies": int(total_companies),
                "recent_changes_7_days": int(recent_changes),
                "enriched_companies": int(enriched_count),
                "status_distribution": status_distribution,
                "state_distribution": state_distribution
            }
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/enriched')
def get_enriched_data():
    """Get enriched company data"""
    try:
        sector = request.args.get('sector', '')
        limit = int(request.args.get('limit', 100))
        
        conn = get_database_connection()
        
        query = """
            SELECT e.*, c.COMPANY_NAME, c.STATE, c.COMPANY_STATUS
            FROM enriched_data e
            LEFT JOIN companies c ON e.CIN = c.CIN
            WHERE 1=1
        """
        params = []
        
        if sector:
            query += " AND e.SECTOR = %s"
            params.append(sector)
        
        query += f" ORDER BY e.ENRICHMENT_DATE DESC LIMIT {limit}"
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        results = df.to_dict('records')
        
        return jsonify({
            "success": True,
            "count": len(results),
            "results": results
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/ai/chat', methods=['POST'])
def ai_chat():
    """AI chat endpoint for conversational queries"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        
        if not query:
            return jsonify({
                "success": False,
                "error": "Query is required"
            }), 400
        
        # Get AI response
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

@app.route('/ai/summary', methods=['GET', 'POST'])
def generate_summary():
    """Generate AI-powered daily summary"""
    try:
        if request.method == 'POST':
            data = request.get_json()
            date = data.get('date', datetime.now().strftime('%Y-%m-%d'))
        else:
            date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        
        # Generate summary
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

@app.route('/data/upload', methods=['POST'])
def upload_data():
    """Upload and process new MCA data files"""
    try:
        if 'file' not in request.files:
            return jsonify({
                "success": False,
                "error": "No file provided"
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                "success": False,
                "error": "No file selected"
            }), 400
        
        # Save uploaded file
        filename = file.filename
        filepath = os.path.join(RAW_DATA_DIR, filename)
        os.makedirs(RAW_DATA_DIR, exist_ok=True)
        file.save(filepath)
        
        # Process the file
        df = pd.read_csv(filepath)
        df = integrator.clean_dataframe(df)
        
        # Detect changes
        changes = detector.simulate_daily_update(filepath)
        
        return jsonify({
            "success": True,
            "message": f"File {filename} processed successfully",
            "records_processed": len(df),
            "changes_detected": len(changes)
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/enrichment/run', methods=['POST'])
def run_enrichment():
    """Run data enrichment process"""
    try:
        data = request.get_json()
        sample_size = data.get('sample_size', ENRICHMENT_SAMPLE_SIZE)
        
        # Run enrichment
        enriched_data = enricher.run_enrichment_process(sample_size)
        
        return jsonify({
            "success": True,
            "message": "Enrichment process completed",
            "companies_processed": len(enriched_data)
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        conn = get_database_connection()
        conn.close()
        
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": "connected"
        })
        
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        "success": False,
        "error": "Endpoint not found"
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        "success": False,
        "error": "Internal server error"
    }), 500

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs(RAW_DATA_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
    os.makedirs(CHANGE_LOGS_DIR, exist_ok=True)
    os.makedirs(ENRICHED_DATA_DIR, exist_ok=True)
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)
