import requests
import pandas as pd
import psycopg2
import time
import json
import os
from bs4 import BeautifulSoup
from datetime import datetime
import logging
from config import *

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CINEnricher:
    def __init__(self):
        self.db_config = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': os.getenv('POSTGRES_PORT', '5432'),
            'database': os.getenv('POSTGRES_DB', 'mca_insights_engine'),
            'user': os.getenv('POSTGRES_USER', 'postgres'),
            'password': os.getenv('POSTGRES_PASSWORD', '')
        }
        self.enriched_data_dir = ENRICHED_DATA_DIR
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        os.makedirs(self.enriched_data_dir, exist_ok=True)
    
    def get_companies_for_enrichment(self, limit=ENRICHMENT_SAMPLE_SIZE):
        conn = psycopg2.connect(**self.db_config)
        query = '''
            SELECT DISTINCT c.CIN, c.COMPANY_NAME, c.STATE, c.COMPANY_STATUS, cl.CHANGE_DATE
            FROM companies c
            LEFT JOIN change_logs cl ON c.CIN = cl.CIN
            WHERE cl.CHANGE_DATE >= NOW() - INTERVAL '30 days'
            ORDER BY cl.CHANGE_DATE DESC
            LIMIT %s
        '''
        df = pd.read_sql_query(query, conn, params=[limit])
        conn.close()
        return df
    
    def enrich_company_data(self, cin, company_name, state, status):
        """Enrich individual company data from multiple sources"""
        enriched_data = {
            'CIN': cin,
            'COMPANY_NAME': company_name,
            'STATE': state,
            'STATUS': status,
            'SECTOR': '',
            'INDUSTRY': '',
            'DIRECTOR_NAMES': '',
            'COMPANY_WEBSITE': '',
            'ENRICHMENT_SOURCE': '',
            'ENRICHMENT_DATE': datetime.now().isoformat()
        }
        
        # Try multiple enrichment sources
        sources_used = []
        
        # 1. ZaubaCorp enrichment
        zauba_data = self._enrich_from_zauba(cin, company_name)
        if zauba_data:
            enriched_data.update(zauba_data)
            sources_used.append('ZaubaCorp')
        
        # 2. API Setu enrichment
        api_data = self._enrich_from_api_setu(cin)
        if api_data:
            enriched_data.update(api_data)
            sources_used.append('API Setu')
        
        # 3. Indian Kanoon enrichment
        kanoon_data = self._enrich_from_indian_kanoon(cin, company_name)
        if kanoon_data:
            enriched_data.update(kanoon_data)
            sources_used.append('Indian Kanoon')
        
        # 4. GST Portal enrichment
        gst_data = self._enrich_from_gst_portal(cin)
        if gst_data:
            enriched_data.update(gst_data)
            sources_used.append('GST Portal')
        
        # 5. MCA21 enrichment
        mca_data = self._enrich_from_mca21(cin)
        if mca_data:
            enriched_data.update(mca_data)
            sources_used.append('MCA21')
        
        enriched_data['ENRICHMENT_SOURCE'] = ', '.join(sources_used)
        
        return enriched_data
    
    def _enrich_from_zauba(self, cin, company_name):
        """Enrich data from ZaubaCorp"""
        try:
            # Simulate ZaubaCorp data extraction
            # In real implementation, you would scrape the website
            time.sleep(0.5)  # Rate limiting
            
            # Mock data for demonstration
            return {
                'SECTOR': self._classify_sector(company_name),
                'INDUSTRY': self._classify_industry(company_name),
                'DIRECTOR_NAMES': 'Mock Director 1, Mock Director 2',
                'COMPANY_WEBSITE': f'https://www.{company_name.lower().replace(" ", "")}.com'
            }
        except Exception as e:
            logger.error(f"Error enriching from ZaubaCorp for {cin}: {str(e)}")
            return None
    
    def _enrich_from_api_setu(self, cin):
        """Enrich data from API Setu"""
        try:
            # Simulate API Setu data extraction
            time.sleep(0.3)
            
            # Mock data for demonstration
            return {
                'SECTOR': 'Technology',
                'INDUSTRY': 'Software Development'
            }
        except Exception as e:
            logger.error(f"Error enriching from API Setu for {cin}: {str(e)}")
            return None
    
    def _enrich_from_indian_kanoon(self, cin, company_name):
        """Enrich data from Indian Kanoon"""
        try:
            # Simulate Indian Kanoon data extraction
            time.sleep(0.4)
            
            # Mock data for demonstration
            return {
                'DIRECTOR_NAMES': 'Legal Director 1, Legal Director 2'
            }
        except Exception as e:
            logger.error(f"Error enriching from Indian Kanoon for {cin}: {str(e)}")
            return None
    
    def _enrich_from_gst_portal(self, cin):
        """Enrich data from GST Portal"""
        try:
            # Simulate GST Portal data extraction
            time.sleep(0.3)
            
            # Mock data for demonstration
            return {
                'SECTOR': 'Manufacturing',
                'INDUSTRY': 'Textiles'
            }
        except Exception as e:
            logger.error(f"Error enriching from GST Portal for {cin}: {str(e)}")
            return None
    
    def _enrich_from_mca21(self, cin):
        """Enrich data from MCA21"""
        try:
            # Simulate MCA21 data extraction
            time.sleep(0.2)
            
            # Mock data for demonstration
            return {
                'SECTOR': 'Services',
                'INDUSTRY': 'Consulting'
            }
        except Exception as e:
            logger.error(f"Error enriching from MCA21 for {cin}: {str(e)}")
            return None
    
    def _classify_sector(self, company_name):
        """Classify company sector based on name"""
        name_lower = company_name.lower()
        
        if any(word in name_lower for word in ['tech', 'software', 'it', 'digital', 'cyber']):
            return 'Technology'
        elif any(word in name_lower for word in ['manufacturing', 'production', 'factory']):
            return 'Manufacturing'
        elif any(word in name_lower for word in ['finance', 'bank', 'credit', 'investment']):
            return 'Financial Services'
        elif any(word in name_lower for word in ['health', 'medical', 'pharma', 'hospital']):
            return 'Healthcare'
        elif any(word in name_lower for word in ['education', 'school', 'college', 'university']):
            return 'Education'
        elif any(word in name_lower for word in ['retail', 'trade', 'commerce', 'shop']):
            return 'Retail & Trade'
        else:
            return 'Other'
    
    def _classify_industry(self, company_name):
        """Classify company industry based on name"""
        name_lower = company_name.lower()
        
        if any(word in name_lower for word in ['software', 'app', 'platform']):
            return 'Software Development'
        elif any(word in name_lower for word in ['consulting', 'advisory', 'services']):
            return 'Consulting Services'
        elif any(word in name_lower for word in ['trading', 'export', 'import']):
            return 'Trading'
        elif any(word in name_lower for word in ['construction', 'building', 'infrastructure']):
            return 'Construction'
        elif any(word in name_lower for word in ['food', 'restaurant', 'catering']):
            return 'Food & Beverage'
        else:
            return 'General Business'
    
    def save_enriched_data(self, enriched_data):
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO enriched_data 
                (CIN, SECTOR, INDUSTRY, DIRECTOR_NAMES, COMPANY_WEBSITE, 
                 ENRICHMENT_SOURCE, ENRICHMENT_DATE)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (CIN) DO UPDATE SET
                SECTOR = EXCLUDED.SECTOR,
                INDUSTRY = EXCLUDED.INDUSTRY,
                DIRECTOR_NAMES = EXCLUDED.DIRECTOR_NAMES,
                COMPANY_WEBSITE = EXCLUDED.COMPANY_WEBSITE,
                ENRICHMENT_SOURCE = EXCLUDED.ENRICHMENT_SOURCE,
                ENRICHMENT_DATE = EXCLUDED.ENRICHMENT_DATE
            ''', (
                enriched_data['CIN'],
                enriched_data.get('SECTOR', ''),
                enriched_data.get('INDUSTRY', ''),
                enriched_data.get('DIRECTOR_NAMES', ''),
                enriched_data.get('COMPANY_WEBSITE', ''),
                enriched_data.get('ENRICHMENT_SOURCE', ''),
                enriched_data.get('ENRICHMENT_DATE', datetime.now().isoformat())
            ))
            
            conn.commit()
            logger.info(f"Saved enriched data for {enriched_data['CIN']}")
            
        except Exception as e:
            logger.error(f"Error saving enriched data: {str(e)}")
            conn.rollback()
        finally:
            conn.close()
    
    def export_enriched_data(self, enriched_data_list, filename=None):
        """Export enriched data to CSV"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"enriched_data_{timestamp}.csv"
        
        filepath = os.path.join(self.enriched_data_dir, filename)
        df = pd.DataFrame(enriched_data_list)
        df.to_csv(filepath, index=False)
        logger.info(f"Exported enriched data to {filepath}")
        return filepath
    
    def run_enrichment_process(self, limit=ENRICHMENT_SAMPLE_SIZE):
        """Run the complete enrichment process"""
        logger.info("Starting CIN enrichment process")
        
        # Get companies for enrichment
        companies = self.get_companies_for_enrichment(limit)
        logger.info(f"Found {len(companies)} companies for enrichment")
        
        enriched_data_list = []
        
        for _, row in companies.iterrows():
            logger.info(f"Enriching data for {row['cin']} - {row['company_name']}")
            
            enriched_data = self.enrich_company_data(
                row['cin'],
                row['company_name'],
                row['state'],
                row['company_status']
            )
            
            if enriched_data:
                # Save to database
                self.save_enriched_data(enriched_data)
                enriched_data_list.append(enriched_data)
            
            # Rate limiting
            time.sleep(1)
        
        # Export enriched data
        if enriched_data_list:
            self.export_enriched_data(enriched_data_list)
            logger.info(f"Enrichment process completed. Processed {len(enriched_data_list)} companies")
        else:
            logger.warning("No companies were enriched")
        
        return enriched_data_list
    
    def get_enrichment_summary(self):
        conn = psycopg2.connect(**self.db_config)
        
        query = '''
            SELECT 
                COUNT(*) as total_enriched,
                COUNT(CASE WHEN SECTOR != '' THEN 1 END) as with_sector,
                COUNT(CASE WHEN INDUSTRY != '' THEN 1 END) as with_industry,
                COUNT(CASE WHEN DIRECTOR_NAMES != '' THEN 1 END) as with_directors,
                COUNT(CASE WHEN COMPANY_WEBSITE != '' THEN 1 END) as with_website
            FROM enriched_data
        '''
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        return df.iloc[0].to_dict()
    
    def get_enriched_companies_by_sector(self):
        conn = psycopg2.connect(**self.db_config)
        query = '''
            SELECT 
                e.SECTOR,
                COUNT(*) as company_count
            FROM enriched_data e
            WHERE e.SECTOR != ''
            GROUP BY e.SECTOR
            ORDER BY company_count DESC
        '''
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df

def main():
    """Main function to run enrichment process"""
    enricher = CINEnricher()
    
    print("=== CIN Enrichment System ===")
    
    # Run enrichment process
    enriched_data = enricher.run_enrichment_process(limit=50)
    
    # Display summary
    summary = enricher.get_enrichment_summary()
    print(f"\nEnrichment Summary:")
    print(f"Total enriched companies: {summary['total_enriched']}")
    print(f"Companies with sector info: {summary['with_sector']}")
    print(f"Companies with industry info: {summary['with_industry']}")
    print(f"Companies with director info: {summary['with_directors']}")
    print(f"Companies with website info: {summary['with_website']}")
    
    # Display sector distribution
    sector_dist = enricher.get_enriched_companies_by_sector()
    print(f"\nSector Distribution:")
    print(sector_dist)

if __name__ == "__main__":
    main()

