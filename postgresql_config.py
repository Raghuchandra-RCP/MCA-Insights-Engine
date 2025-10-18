"""
PostgreSQL Configuration for MCA Insights Engine
Handles database connection and operations for PostgreSQL
"""

import psycopg2
import pandas as pd
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class PostgreSQLConfig:
    def __init__(self):
        self.host = os.getenv('POSTGRES_HOST', 'localhost')
        self.port = os.getenv('POSTGRES_PORT', '5432')
        self.database = os.getenv('POSTGRES_DB', 'mca_insights_engine')
        self.user = os.getenv('POSTGRES_USER', 'postgres')
        self.password = os.getenv('POSTGRES_PASSWORD', '')
        
        self.connection_string = f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
        self.engine = create_engine(self.connection_string)
    
    def get_connection(self):
        """Get PostgreSQL connection"""
        try:
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
            return conn
        except Exception as e:
            logger.error(f"Error connecting to PostgreSQL: {str(e)}")
            raise
    
    def get_engine(self):
        """Get SQLAlchemy engine"""
        return self.engine
    
    def test_connection(self):
        """Test database connection"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            cursor.close()
            conn.close()
            logger.info(f"PostgreSQL connection successful. Version: {version[0]}")
            return True
        except Exception as e:
            logger.error(f"PostgreSQL connection failed: {str(e)}")
            return False
    
    def create_tables(self):
        """Create required tables in PostgreSQL"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS companies (
                    CIN VARCHAR(50) PRIMARY KEY,
                    COMPANY_NAME VARCHAR(500),
                    COMPANY_CLASS VARCHAR(100),
                    DATE_OF_INCORPORATION DATE,
                    AUTHORIZED_CAPITAL DECIMAL(15,2),
                    PAIDUP_CAPITAL DECIMAL(15,2),
                    COMPANY_STATUS VARCHAR(100),
                    PRINCIPAL_BUSINESS_ACTIVITY TEXT,
                    REGISTERED_OFFICE_ADDRESS TEXT,
                    ROC_CODE VARCHAR(20),
                    STATE VARCHAR(100),
                    LAST_UPDATED TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS change_logs (
                    id SERIAL PRIMARY KEY,
                    CIN VARCHAR(50),
                    CHANGE_TYPE VARCHAR(100),
                    FIELD_CHANGED VARCHAR(100),
                    OLD_VALUE TEXT,
                    NEW_VALUE TEXT,
                    CHANGE_DATE TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (CIN) REFERENCES companies (CIN)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS enriched_data (
                    CIN VARCHAR(50) PRIMARY KEY,
                    SECTOR VARCHAR(100),
                    INDUSTRY VARCHAR(100),
                    DIRECTOR_NAMES TEXT,
                    COMPANY_WEBSITE VARCHAR(500),
                    ENRICHMENT_SOURCE VARCHAR(200),
                    ENRICHMENT_DATE TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (CIN) REFERENCES companies (CIN)
                )
            ''')
            
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_companies_state ON companies(STATE)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_companies_status ON companies(COMPANY_STATUS)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_change_logs_cin ON change_logs(CIN)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_change_logs_date ON change_logs(CHANGE_DATE)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_enriched_sector ON enriched_data(SECTOR)')
            
            conn.commit()
            logger.info("PostgreSQL tables created successfully")
            
        except Exception as e:
            logger.error(f"Error creating tables: {str(e)}")
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()
    
    def execute_query(self, query, params=None):
        """Execute a query and return results"""
        conn = self.get_connection()
        try:
            df = pd.read_sql_query(query, conn, params=params)
            return df
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            raise
        finally:
            conn.close()
    
    def execute_insert(self, query, params):
        """Execute an insert query"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount
        except Exception as e:
            logger.error(f"Error executing insert: {str(e)}")
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()

# Global instance
postgres_config = PostgreSQLConfig()
