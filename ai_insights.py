import pandas as pd
import psycopg2
import json
import os
from datetime import datetime, timedelta
import logging
from config import *
import openai
from typing import List, Dict, Any
from postgresql_config import postgres_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIInsightsEngine:
    def __init__(self):
        self.openai_api_key = os.getenv('OPENAI_API_KEY', '')
        self.ai_model = "gpt-3.5-turbo"
        
        if self.openai_api_key:
            try:
                # Check if OpenAI has OpenAI class (newer versions)
                if hasattr(openai, 'OpenAI'):
                    self.client = openai.OpenAI(api_key=self.openai_api_key)
                else:
                    # Fallback to old OpenAI client
                    openai.api_key = self.openai_api_key
                    self.client = openai
            except Exception as e:
                logger.warning(f"OpenAI client initialization failed: {str(e)}")
                self.client = None
        else:
            logger.warning("OpenAI API key not found. AI features will be limited.")
            self.client = None
    
    def generate_daily_summary(self, date=None):
        """Generate automated daily summary report"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        changes_summary = self._get_daily_changes_summary(date)
        company_stats = self._get_company_statistics()
        summary_text = self._create_summary_text(changes_summary, company_stats, date)
        self._save_daily_summary(summary_text, date)
        
        return summary_text
    
    def _get_daily_changes_summary(self, date):
        """Get summary of changes for a specific date"""
        conn = postgres_config.get_connection()
        
        query = '''
            SELECT 
                CHANGE_TYPE,
                COUNT(*) as count
            FROM change_logs 
            WHERE DATE(CHANGE_DATE) = %s
            GROUP BY CHANGE_TYPE
        '''
        
        df = pd.read_sql_query(query, conn, params=[date])
        conn.close()
        
        return df.to_dict('records')
    
    def _get_company_statistics(self):
        """Get overall company statistics"""
        conn = postgres_config.get_connection()
        
        # Total companies
        total_query = "SELECT COUNT(*) as total FROM companies"
        total_result = pd.read_sql_query(total_query, conn)
        
        # Companies by status
        status_query = '''
            SELECT COMPANY_STATUS, COUNT(*) as count 
            FROM companies 
            GROUP BY COMPANY_STATUS
        '''
        status_result = pd.read_sql_query(status_query, conn)
        
        # Companies by state
        state_query = '''
            SELECT STATE, COUNT(*) as count 
            FROM companies 
            GROUP BY STATE
            ORDER BY count DESC
            LIMIT 5
        '''
        state_result = pd.read_sql_query(state_query, conn)
        
        conn.close()
        
        return {
            'total_companies': total_result.iloc[0]['total'],
            'by_status': status_result.to_dict('records'),
            'by_state': state_result.to_dict('records')
        }
    
    def _create_summary_text(self, changes_summary, company_stats, date):
        if self.openai_api_key and self.client:
            return self._create_ai_summary(changes_summary, company_stats, date)
        else:
            return self._create_rule_based_summary(changes_summary, company_stats, date)
    
    def _create_ai_summary(self, changes_summary, company_stats, date):
        try:
            prompt = f"""
            Generate a professional daily summary report for MCA (Ministry of Corporate Affairs) data changes on {date}.
            
            Changes Summary:
            {json.dumps(changes_summary, indent=2)}
            
            Company Statistics:
            Total Companies: {company_stats['total_companies']}
            Status Distribution: {json.dumps(company_stats['by_status'], indent=2)}
            Top States: {json.dumps(company_stats['by_state'], indent=2)}
            
            Please create a concise, professional summary highlighting:
            1. Key changes and their impact
            2. Notable trends or patterns
            3. Important statistics
            4. Any significant developments
            
            Format the response as a structured report with clear sections.
            """
            
            if self.client:
                response = self.client.chat.completions.create(
                    model=self.ai_model,
                    messages=[
                        {"role": "system", "content": "You are a data analyst specializing in corporate data insights. Create clear, professional reports."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1000,
                    temperature=0.7
                )
                return response.choices[0].message.content
            else:
                return self._create_rule_based_summary(changes_summary, company_stats, date)
            
        except Exception as e:
            logger.error(f"Error generating AI summary: {str(e)}")
            return self._create_rule_based_summary(changes_summary, company_stats, date)
    
    def _create_rule_based_summary(self, changes_summary, company_stats, date):
        """Create summary using rule-based approach"""
        summary = f"""
# Daily MCA Data Summary - {date}

## Overview
This report provides an automated summary of changes in the MCA company database.

## Key Changes
"""
        
        if changes_summary:
            for change in changes_summary:
                change_type = change.get('CHANGE_TYPE', change.get('change_type', 'Unknown'))
                count = change.get('count', 0)
                summary += f"- {change_type}: {count} companies\n"
        else:
            summary += "- No changes recorded for this date\n"
        
        summary += f"""
## Company Statistics
- Total Companies in Database: {company_stats['total_companies']:,}

### Status Distribution
"""
        for status in company_stats['by_status']:
            status_name = status.get('COMPANY_STATUS', status.get('company_status', 'Unknown'))
            count = status.get('count', 0)
            summary += f"- {status_name}: {count:,} companies\n"
        
        summary += f"""
### Top States by Company Count
"""
        for state in company_stats['by_state']:
            state_name = state.get('STATE', state.get('state', 'Unknown'))
            count = state.get('count', 0)
            summary += f"- {state_name}: {count:,} companies\n"
        
        summary += f"""
## Analysis
The data shows the current state of corporate registrations and changes in the MCA database.
This automated summary is generated daily to track corporate activity and regulatory compliance.

---
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return summary
    
    def _save_daily_summary(self, summary_text, date):
        """Save daily summary to file"""
        os.makedirs("reports", exist_ok=True)
        
        # Save as text file
        txt_filename = f"reports/daily_summary_{date}.txt"
        with open(txt_filename, 'w', encoding='utf-8') as f:
            f.write(summary_text)
        
        # Save as JSON file
        json_filename = f"reports/daily_summary_{date}.json"
        summary_data = {
            'date': date,
            'summary': summary_text,
            'generated_at': datetime.now().isoformat()
        }
        
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Daily summary saved for {date}")
    
    def chat_with_data(self, user_query: str) -> str:
        if self.openai_api_key and self.client:
            return self._process_ai_query(user_query)
        else:
            return self._process_rule_based_query(user_query)
    
    def _process_ai_query(self, user_query: str) -> str:
        try:
            relevant_data = self._extract_relevant_data(user_query)
            
            prompt = f"""
            You are a data analyst assistant for MCA (Ministry of Corporate Affairs) data.
            Answer the user's question based on the provided data.
            
            User Query: {user_query}
            
            Relevant Data:
            {json.dumps(relevant_data, indent=2)}
            
            Provide a clear, helpful answer. If the data doesn't contain enough information,
            suggest what additional information might be helpful.
            """
            
            if self.client:
                response = self.client.chat.completions.create(
                    model=self.ai_model,
                    messages=[
                        {"role": "system", "content": "You are a helpful data analyst assistant specializing in corporate data insights."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=500,
                    temperature=0.7
                )
                return response.choices[0].message.content
            else:
                return self._process_rule_based_query(user_query)
            
        except Exception as e:
            logger.error(f"Error processing AI query: {str(e)}")
            return self._process_rule_based_query(user_query)
    
    def _process_rule_based_query(self, user_query: str) -> str:
        """Process query using rule-based approach"""
        query_lower = user_query.lower()
        
        if "new incorporations" in query_lower or "new companies" in query_lower:
            return self._get_new_incorporations_info()
        elif "struck off" in query_lower or "deregistered" in query_lower:
            return self._get_deregistrations_info()
        elif "maharashtra" in query_lower:
            return self._get_state_info("Maharashtra")
        elif "gujarat" in query_lower:
            return self._get_state_info("Gujarat")
        elif "delhi" in query_lower:
            return self._get_state_info("Delhi")
        elif "tamil nadu" in query_lower:
            return self._get_state_info("Tamil Nadu")
        elif "karnataka" in query_lower:
            return self._get_state_info("Karnataka")
        elif "manufacturing" in query_lower:
            return self._get_sector_info("Manufacturing")
        elif "technology" in query_lower:
            return self._get_sector_info("Technology")
        elif "total companies" in query_lower or "how many companies" in query_lower:
            return self._get_total_companies_info()
        else:
            return "I can help you with information about MCA company data. Try asking about:\n- New incorporations\n- Companies by state (Maharashtra, Gujarat, Delhi, Tamil Nadu, Karnataka)\n- Companies by sector (Manufacturing, Technology, etc.)\n- Total company count\n- Deregistrations"
    
    def _extract_relevant_data(self, query: str) -> Dict[str, Any]:
        """Extract relevant data based on query"""
        query_lower = query.lower()
        relevant_data = {}
        
        # Get basic statistics
        conn = postgres_config.get_connection()
        
        if "new incorporations" in query_lower:
            query_sql = '''
                SELECT COUNT(*) as count 
                FROM change_logs 
                WHERE CHANGE_TYPE = 'New Incorporation'
                AND DATE(CHANGE_DATE) >= date('now', '-30 days')
            '''
            result = pd.read_sql_query(query_sql, conn)
            relevant_data['new_incorporations_30_days'] = result.iloc[0]['count']
        
        if any(state in query_lower for state in ["maharashtra", "gujarat", "delhi", "tamil nadu", "karnataka"]):
            state_query = '''
                SELECT STATE, COUNT(*) as count 
                FROM companies 
                GROUP BY STATE
            '''
            result = pd.read_sql_query(state_query, conn)
            relevant_data['companies_by_state'] = result.to_dict('records')
        
        conn.close()
        return relevant_data
    
    def _get_new_incorporations_info(self) -> str:
        """Get information about new incorporations"""
        conn = postgres_config.get_connection()
        query = '''
            SELECT COUNT(*) as count 
            FROM change_logs 
            WHERE CHANGE_TYPE = 'New Incorporation'
            AND DATE(CHANGE_DATE) >= date('now', '-30 days')
        '''
        result = pd.read_sql_query(query, conn)
        conn.close()
        
        count = result.iloc[0]['count']
        return f"There have been {count} new company incorporations in the last 30 days."
    
    def _get_deregistrations_info(self) -> str:
        """Get information about deregistrations"""
        conn = postgres_config.get_connection()
        query = '''
            SELECT COUNT(*) as count 
            FROM change_logs 
            WHERE CHANGE_TYPE = 'Deregistration'
            AND DATE(CHANGE_DATE) >= date('now', '-30 days')
        '''
        result = pd.read_sql_query(query, conn)
        conn.close()
        
        count = result.iloc[0]['count']
        return f"There have been {count} company deregistrations in the last 30 days."
    
    def _get_state_info(self, state: str) -> str:
        """Get information about companies in a specific state"""
        conn = postgres_config.get_connection()
        query = '''
            SELECT COUNT(*) as count 
            FROM companies 
            WHERE STATE = %s
        '''
        result = pd.read_sql_query(query, conn, params=[state])
        conn.close()
        
        count = result.iloc[0]['count']
        return f"There are {count:,} companies registered in {state}."
    
    def _get_sector_info(self, sector: str) -> str:
        """Get information about companies in a specific sector"""
        conn = postgres_config.get_connection()
        query = '''
            SELECT COUNT(*) as count 
            FROM enriched_data 
            WHERE SECTOR = %s
        '''
        result = pd.read_sql_query(query, conn, params=[sector])
        conn.close()
        
        count = result.iloc[0]['count']
        return f"There are {count} companies in the {sector} sector (based on enriched data)."
    
    def _get_total_companies_info(self) -> str:
        """Get total companies information"""
        conn = postgres_config.get_connection()
        query = "SELECT COUNT(*) as count FROM companies"
        result = pd.read_sql_query(query, conn)
        conn.close()
        
        count = result.iloc[0]['count']
        return f"There are {count:,} companies in the MCA database."
    
    def get_insights_dashboard_data(self) -> Dict[str, Any]:
        """Get data for insights dashboard"""
        conn = postgres_config.get_connection()
        
        # Recent changes
        recent_changes_query = '''
            SELECT cl.*, c.COMPANY_NAME, c.STATE 
            FROM change_logs cl
            LEFT JOIN companies c ON cl.CIN = c.CIN
            ORDER BY cl.CHANGE_DATE DESC
            LIMIT 10
        '''
        recent_changes = pd.read_sql_query(recent_changes_query, conn)
        
        # Change trends
        trend_query = '''
            SELECT 
                DATE(CHANGE_DATE) as date,
                CHANGE_TYPE,
                COUNT(*) as count
            FROM change_logs 
            WHERE DATE(CHANGE_DATE) >= date('now', '-30 days')
            GROUP BY DATE(CHANGE_DATE), CHANGE_TYPE
            ORDER BY date DESC
        '''
        change_trends = pd.read_sql_query(trend_query, conn)
        
        # Company distribution
        distribution_query = '''
            SELECT STATE, COUNT(*) as count 
            FROM companies 
            GROUP BY STATE
            ORDER BY count DESC
        '''
        company_distribution = pd.read_sql_query(distribution_query, conn)
        
        conn.close()
        
        return {
            'recent_changes': recent_changes.to_dict('records'),
            'change_trends': change_trends.to_dict('records'),
            'company_distribution': company_distribution.to_dict('records')
        }

def main():
    """Main function to demonstrate AI insights"""
    ai_engine = AIInsightsEngine()
    
    print("=== AI Insights Engine ===")
    
    # Generate daily summary
    summary = ai_engine.generate_daily_summary()
    print("Daily Summary Generated:")
    print(summary)
    
    # Test conversational queries
    test_queries = [
        "How many new companies were incorporated recently?",
        "Show me companies in Maharashtra",
        "What's the total number of companies?",
        "Tell me about manufacturing companies"
    ]
    
    print("\n=== Chat with Data ===")
    for query in test_queries:
        print(f"\nQ: {query}")
        answer = ai_engine.chat_with_data(query)
        print(f"A: {answer}")

if __name__ == "__main__":
    main()
