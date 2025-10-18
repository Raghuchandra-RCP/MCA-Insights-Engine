import pandas as pd
import numpy as np
import os
from datetime import datetime
import logging
from config import *
from postgresql_config import postgres_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCADataIntegrator:
    def __init__(self):
        self.raw_data_dir = RAW_DATA_DIR
        self.processed_data_dir = PROCESSED_DATA_DIR
        self.postgres = postgres_config
        self.create_directories()
        self.init_database()
    
    def create_directories(self):
        """Create necessary directories if they don't exist"""
        for directory in [self.raw_data_dir, self.processed_data_dir, CHANGE_LOGS_DIR, ENRICHED_DATA_DIR]:
            os.makedirs(directory, exist_ok=True)
    
    def init_database(self):
        """Initialize PostgreSQL database with required tables"""
        try:
            if not self.postgres.test_connection():
                raise Exception("Cannot connect to PostgreSQL database")
            
            self.postgres.create_tables()
            logger.info("PostgreSQL database initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
            raise
    
    def load_state_data(self, state_name, file_path):
        """Load and clean data from a single state CSV file"""
        try:
            df = pd.read_csv(file_path)
            logger.info(f"Loaded {len(df)} records from {state_name}")
            
            df.columns = df.columns.str.upper().str.strip()
            
            df['STATE'] = state_name
            
            df = self.clean_dataframe(df)
            
            return df
            
        except Exception as e:
            logger.error(f"Error loading data for {state_name}: {str(e)}")
            return None
    
    def clean_dataframe(self, df):
        """Clean and normalize dataframe"""
        # Handle missing values
        df = df.fillna('')
        
        # Clean CIN - remove extra spaces and convert to uppercase
        if 'CIN' in df.columns:
            df['CIN'] = df['CIN'].astype(str).str.strip().str.upper()
        
        # Clean company name
        if 'COMPANY_NAME' in df.columns:
            df['COMPANY_NAME'] = df['COMPANY_NAME'].astype(str).str.strip()
        
        # Clean numeric columns
        numeric_columns = ['AUTHORIZED_CAPITAL', 'PAIDUP_CAPITAL']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Clean date column
        if 'DATE_OF_INCORPORATION' in df.columns:
            df['DATE_OF_INCORPORATION'] = pd.to_datetime(
                df['DATE_OF_INCORPORATION'], 
                errors='coerce'
            ).dt.strftime('%Y-%m-%d')
        
        # Remove duplicates based on CIN
        df = df.drop_duplicates(subset=['CIN'], keep='last')
        
        return df
    
    def consolidate_data(self, state_files):
        """Consolidate data from multiple state files"""
        consolidated_data = []
        
        for state, file_path in state_files.items():
            if os.path.exists(file_path):
                df = self.load_state_data(state, file_path)
                if df is not None:
                    consolidated_data.append(df)
                    logger.info(f"Processed {state}: {len(df)} records")
            else:
                logger.warning(f"File not found: {file_path}")
        
        if consolidated_data:
            master_df = pd.concat(consolidated_data, ignore_index=True)
            logger.info(f"Consolidated data: {len(master_df)} total records")
            return master_df
        else:
            logger.error("No data files found to consolidate")
            return None
    
    def save_to_database(self, df):
        """Save consolidated data to database"""
        try:
            # Use pandas to_sql with PostgreSQL
            df.to_sql('companies', self.postgres.get_engine(), if_exists='replace', index=False, method='multi')
            logger.info(f"Saved {len(df)} records to PostgreSQL database")
        except Exception as e:
            logger.error(f"Error saving to database: {str(e)}")
            raise
    
    def export_processed_data(self, df, filename="master_companies.csv"):
        """Export processed data to CSV"""
        filepath = os.path.join(self.processed_data_dir, filename)
        df.to_csv(filepath, index=False)
        logger.info(f"Exported processed data to {filepath}")
        return filepath
    
    def get_company_count_by_state(self):
        """Get company count by state from database"""
        query = "SELECT STATE, COUNT(*) as COUNT FROM companies GROUP BY STATE"
        df = self.postgres.execute_query(query)
        return df
    
    def get_company_count_by_status(self):
        """Get company count by status from database"""
        query = "SELECT COMPANY_STATUS, COUNT(*) as COUNT FROM companies GROUP BY COMPANY_STATUS"
        df = self.postgres.execute_query(query)
        return df

def main():
    """Main function to run data integration"""
    integrator = MCADataIntegrator()
    
    # Example usage - you would replace this with actual file paths
    state_files = {
        "Maharashtra": "data/raw/maharashtra_companies.csv",
        "Gujarat": "data/raw/gujarat_companies.csv",
        "Delhi": "data/raw/delhi_companies.csv",
        "Tamil Nadu": "data/raw/tamil_nadu_companies.csv",
        "Karnataka": "data/raw/karnataka_companies.csv"
    }
    
    # Consolidate data
    master_data = integrator.consolidate_data(state_files)
    
    if master_data is not None:
        # Save to database
        integrator.save_to_database(master_data)
        
        # Export processed data
        integrator.export_processed_data(master_data)
        
        # Display statistics
        print("\n=== Data Integration Summary ===")
        print(f"Total companies processed: {len(master_data)}")
        print("\nCompanies by State:")
        print(integrator.get_company_count_by_state())
        print("\nCompanies by Status:")
        print(integrator.get_company_count_by_status())

if __name__ == "__main__":
    main()
