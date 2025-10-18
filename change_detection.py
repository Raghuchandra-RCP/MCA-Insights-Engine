import pandas as pd
import sqlite3
import json
import os
from datetime import datetime, timedelta
import logging
from config import *

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChangeDetector:
    def __init__(self, db_path=DATABASE_PATH):
        self.db_path = db_path
        self.change_logs_dir = CHANGE_LOGS_DIR
        os.makedirs(self.change_logs_dir, exist_ok=True)
    
    def detect_changes(self, new_data, previous_data=None):
        """
        Detect changes between new and previous datasets
        """
        changes = []
        
        if previous_data is None:
            for _, row in new_data.iterrows():
                changes.append({
                    'CIN': row['CIN'],
                    'CHANGE_TYPE': CHANGE_TYPES['NEW_INCORPORATION'],
                    'FIELD_CHANGED': 'ALL',
                    'OLD_VALUE': 'N/A',
                    'NEW_VALUE': 'New Company',
                    'CHANGE_DATE': datetime.now()
                })
        else:
            new_dict = {row['CIN']: row for _, row in new_data.iterrows()}
            prev_dict = {row['CIN']: row for _, row in previous_data.iterrows()}
            
            new_cins = set(new_dict.keys()) - set(prev_dict.keys())
            for cin in new_cins:
                changes.append({
                    'CIN': cin,
                    'CHANGE_TYPE': CHANGE_TYPES['NEW_INCORPORATION'],
                    'FIELD_CHANGED': 'ALL',
                    'OLD_VALUE': 'N/A',
                    'NEW_VALUE': 'New Company',
                    'CHANGE_DATE': datetime.now()
                })
            
            deregistered_cins = set(prev_dict.keys()) - set(new_dict.keys())
            for cin in deregistered_cins:
                changes.append({
                    'CIN': cin,
                    'CHANGE_TYPE': CHANGE_TYPES['DEREGISTRATION'],
                    'FIELD_CHANGED': 'STATUS',
                    'OLD_VALUE': prev_dict[cin].get('COMPANY_STATUS', ''),
                    'NEW_VALUE': 'Deregistered',
                    'CHANGE_DATE': datetime.now()
                })
            
            common_cins = set(new_dict.keys()) & set(prev_dict.keys())
            for cin in common_cins:
                new_row = new_dict[cin]
                prev_row = prev_dict[cin]
                
                field_changes = self._detect_field_changes(prev_row, new_row)
                changes.extend(field_changes)
        
        return changes
    
    def _detect_field_changes(self, prev_row, new_row):
        """Detect changes in individual fields"""
        changes = []
        
        # Fields to monitor for changes
        fields_to_check = [
            'COMPANY_STATUS',
            'AUTHORIZED_CAPITAL',
            'PAIDUP_CAPITAL',
            'COMPANY_CLASS',
            'PRINCIPAL_BUSINESS_ACTIVITY',
            'REGISTERED_OFFICE_ADDRESS'
        ]
        
        for field in fields_to_check:
            old_value = prev_row.get(field, '')
            new_value = new_row.get(field, '')
            
            if str(old_value) != str(new_value):
                change_type = self._get_change_type(field, old_value, new_value)
                changes.append({
                    'CIN': new_row['CIN'],
                    'CHANGE_TYPE': change_type,
                    'FIELD_CHANGED': field,
                    'OLD_VALUE': str(old_value),
                    'NEW_VALUE': str(new_value),
                    'CHANGE_DATE': datetime.now()
                })
        
        return changes
    
    def _get_change_type(self, field, old_value, new_value):
        """Determine the type of change based on field and values"""
        if field == 'COMPANY_STATUS':
            return CHANGE_TYPES['STATUS_CHANGE']
        elif field in ['AUTHORIZED_CAPITAL', 'PAIDUP_CAPITAL']:
            return CHANGE_TYPES['CAPITAL_CHANGE']
        elif field == 'REGISTERED_OFFICE_ADDRESS':
            return CHANGE_TYPES['ADDRESS_CHANGE']
        elif field == 'PRINCIPAL_BUSINESS_ACTIVITY':
            return CHANGE_TYPES['ACTIVITY_CHANGE']
        else:
            return 'FIELD_UPDATE'
    
    def save_changes_to_database(self, changes):
        """Save detected changes to database"""
        if not changes:
            logger.info("No changes detected")
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            for change in changes:
                cursor.execute('''
                    INSERT INTO change_logs 
                    (CIN, CHANGE_TYPE, FIELD_CHANGED, OLD_VALUE, NEW_VALUE, CHANGE_DATE)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    change['CIN'],
                    change['CHANGE_TYPE'],
                    change['FIELD_CHANGED'],
                    change['OLD_VALUE'],
                    change['NEW_VALUE'],
                    change['CHANGE_DATE']
                ))
            
            conn.commit()
            logger.info(f"Saved {len(changes)} changes to database")
            
        except Exception as e:
            logger.error(f"Error saving changes to database: {str(e)}")
            conn.rollback()
        finally:
            conn.close()
    
    def export_changes_to_csv(self, changes, filename=None):
        """Export changes to CSV file"""
        if not changes:
            logger.info("No changes to export")
            return None
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"change_log_{timestamp}.csv"
        
        filepath = os.path.join(self.change_logs_dir, filename)
        df = pd.DataFrame(changes)
        df.to_csv(filepath, index=False)
        logger.info(f"Exported changes to {filepath}")
        return filepath
    
    def export_changes_to_json(self, changes, filename=None):
        """Export changes to JSON file"""
        if not changes:
            logger.info("No changes to export")
            return None
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"change_log_{timestamp}.json"
        
        filepath = os.path.join(self.change_logs_dir, filename)
        
        # Convert datetime objects to strings for JSON serialization
        json_changes = []
        for change in changes:
            json_change = change.copy()
            json_change['CHANGE_DATE'] = change['CHANGE_DATE'].isoformat()
            json_changes.append(json_change)
        
        with open(filepath, 'w') as f:
            json.dump(json_changes, f, indent=2)
        
        logger.info(f"Exported changes to {filepath}")
        return filepath
    
    def get_changes_summary(self, date_from=None, date_to=None):
        """Get summary of changes for a date range"""
        conn = sqlite3.connect(self.db_path)
        
        query = "SELECT * FROM change_logs WHERE 1=1"
        params = []
        
        if date_from:
            query += " AND DATE(CHANGE_DATE) >= ?"
            params.append(date_from)
        
        if date_to:
            query += " AND DATE(CHANGE_DATE) <= ?"
            params.append(date_to)
        
        query += " ORDER BY CHANGE_DATE DESC"
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        if df.empty:
            return {
                'total_changes': 0,
                'new_incorporations': 0,
                'deregistrations': 0,
                'status_changes': 0,
                'capital_changes': 0,
                'other_changes': 0
            }
        
        summary = {
            'total_changes': len(df),
            'new_incorporations': len(df[df['CHANGE_TYPE'] == CHANGE_TYPES['NEW_INCORPORATION']]),
            'deregistrations': len(df[df['CHANGE_TYPE'] == CHANGE_TYPES['DEREGISTRATION']]),
            'status_changes': len(df[df['CHANGE_TYPE'] == CHANGE_TYPES['STATUS_CHANGE']]),
            'capital_changes': len(df[df['CHANGE_TYPE'] == CHANGE_TYPES['CAPITAL_CHANGE']]),
            'other_changes': len(df[~df['CHANGE_TYPE'].isin([
                CHANGE_TYPES['NEW_INCORPORATION'],
                CHANGE_TYPES['DEREGISTRATION'],
                CHANGE_TYPES['STATUS_CHANGE'],
                CHANGE_TYPES['CAPITAL_CHANGE']
            ])])
        }
        
        return summary
    
    def get_recent_changes(self, limit=100):
        """Get recent changes from database"""
        conn = sqlite3.connect(self.db_path)
        query = '''
            SELECT cl.*, c.COMPANY_NAME, c.STATE 
            FROM change_logs cl
            LEFT JOIN companies c ON cl.CIN = c.CIN
            ORDER BY cl.CHANGE_DATE DESC
            LIMIT ?
        '''
        df = pd.read_sql_query(query, conn, params=[limit])
        conn.close()
        return df
    
    def simulate_daily_update(self, new_data_file):
        """
        Simulate a daily update by comparing with previous day's data
        """
        # Load new data
        new_data = pd.read_csv(new_data_file)
        new_data = self._clean_dataframe(new_data)
        
        # Get previous day's data from database
        conn = sqlite3.connect(self.db_path)
        query = "SELECT * FROM companies"
        previous_data = pd.read_sql_query(query, conn)
        conn.close()
        
        # Detect changes
        changes = self.detect_changes(new_data, previous_data)
        
        # Save changes
        if changes:
            self.save_changes_to_database(changes)
            self.export_changes_to_csv(changes)
            self.export_changes_to_json(changes)
        
        # Update master database with new data
        self._update_master_database(new_data)
        
        return changes
    
    def _clean_dataframe(self, df):
        """Clean dataframe for change detection"""
        # Standardize column names
        df.columns = df.columns.str.upper().str.strip()
        
        # Clean CIN
        if 'CIN' in df.columns:
            df['CIN'] = df['CIN'].astype(str).str.strip().str.upper()
        
        # Clean numeric columns
        numeric_columns = ['AUTHORIZED_CAPITAL', 'PAIDUP_CAPITAL']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        return df
    
    def _update_master_database(self, new_data):
        """Update master database with new data"""
        conn = sqlite3.connect(self.db_path)
        
        try:
            for _, row in new_data.iterrows():
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO companies 
                    (CIN, COMPANY_NAME, COMPANY_CLASS, DATE_OF_INCORPORATION,
                     AUTHORIZED_CAPITAL, PAIDUP_CAPITAL, COMPANY_STATUS,
                     PRINCIPAL_BUSINESS_ACTIVITY, REGISTERED_OFFICE_ADDRESS,
                     ROC_CODE, STATE, LAST_UPDATED)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    row.get('CIN', ''),
                    row.get('COMPANY_NAME', ''),
                    row.get('COMPANY_CLASS', ''),
                    row.get('DATE_OF_INCORPORATION', ''),
                    row.get('AUTHORIZED_CAPITAL', 0),
                    row.get('PAIDUP_CAPITAL', 0),
                    row.get('COMPANY_STATUS', ''),
                    row.get('PRINCIPAL_BUSINESS_ACTIVITY', ''),
                    row.get('REGISTERED_OFFICE_ADDRESS', ''),
                    row.get('ROC_CODE', ''),
                    row.get('STATE', ''),
                    datetime.now()
                ))
            
            conn.commit()
            logger.info("Updated master database with new data")
            
        except Exception as e:
            logger.error(f"Error updating master database: {str(e)}")
            conn.rollback()
        finally:
            conn.close()

def main():
    """Main function to demonstrate change detection"""
    detector = ChangeDetector()
    
    # Example usage
    print("=== Change Detection System ===")
    
    # Get recent changes summary
    summary = detector.get_changes_summary()
    print(f"Total changes: {summary['total_changes']}")
    print(f"New incorporations: {summary['new_incorporations']}")
    print(f"Deregistrations: {summary['deregistrations']}")
    print(f"Status changes: {summary['status_changes']}")
    print(f"Capital changes: {summary['capital_changes']}")

if __name__ == "__main__":
    main()

