import os
import sys
import pandas as pd
import psycopg2
import json
import random
from datetime import datetime, timedelta
from pathlib import Path
import logging
from postgresql_config import postgres_config
from change_detection import ChangeDetector
from cin_enrichment import CINEnricher
from ai_insights import AIInsightsEngine

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('daily_update.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DailyUpdateSimulator:
    def __init__(self):
        self.db_config = {
            'host': 'localhost',
            'port': '5432',
            'database': 'mca_insights_engine',
            'user': 'postgres',
            'password': 'rcp@2004'
        }
        
        self.snapshots_dir = Path("data/snapshots")
        self.change_logs_dir = Path("data/change_logs")
        self.reports_dir = Path("reports")
        
        for directory in [self.snapshots_dir, self.change_logs_dir, self.reports_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        self.detector = ChangeDetector()
        self.enricher = CINEnricher()
        self.ai_engine = AIInsightsEngine()
    
    def create_daily_snapshot(self):
        logger.info("Creating daily snapshot...")
        
        try:
            conn = psycopg2.connect(**self.db_config)
            
            query = "SELECT * FROM companies ORDER BY CIN"
            df = pd.read_sql_query(query, conn)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            snapshot_file = self.snapshots_dir / f"snapshot_{timestamp}.csv"
            df.to_csv(snapshot_file, index=False)
            
            conn.close()
            
            logger.info(f"Daily snapshot saved: {snapshot_file}")
            return snapshot_file
            
        except Exception as e:
            logger.error(f"Error creating snapshot: {str(e)}")
            return None
    
    def simulate_company_changes(self):
        logger.info("Simulating company changes...")
        
        changes = []
        
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            cursor.execute("SELECT CIN, COMPANY_NAME, COMPANY_STATUS, AUTHORIZED_CAPITAL, PAIDUP_CAPITAL FROM companies")
            companies = cursor.fetchall()
            
            for company in companies:
                cin, name, status, auth_capital, paid_capital = company
                
                if random.random() < 0.05:
                    changes.append({
                        'CIN': cin,
                        'CHANGE_TYPE': 'New Incorporation',
                        'FIELD_CHANGED': 'ALL',
                        'OLD_VALUE': 'N/A',
                        'NEW_VALUE': 'New Company',
                        'CHANGE_DATE': datetime.now()
                    })
                
                elif random.random() < 0.10:
                    old_status = status
                    new_status = random.choice(['Active', 'Under Process', 'Strike Off', 'Amalgamated'])
                    if new_status != old_status:
                        changes.append({
                            'CIN': cin,
                            'CHANGE_TYPE': 'Status Change',
                            'FIELD_CHANGED': 'COMPANY_STATUS',
                            'OLD_VALUE': old_status,
                            'NEW_VALUE': new_status,
                            'CHANGE_DATE': datetime.now()
                        })
                        
                        cursor.execute(
                            "UPDATE companies SET COMPANY_STATUS = %s, LAST_UPDATED = %s WHERE CIN = %s",
                            (new_status, datetime.now(), cin)
                        )
                
                elif random.random() < 0.08:
                    old_capital = float(auth_capital)
                    change_factor = random.uniform(0.8, 1.5)
                    new_capital = old_capital * change_factor
                    
                    changes.append({
                        'CIN': cin,
                        'CHANGE_TYPE': 'Capital Change',
                        'FIELD_CHANGED': 'AUTHORIZED_CAPITAL',
                        'OLD_VALUE': str(old_capital),
                        'NEW_VALUE': str(new_capital),
                        'CHANGE_DATE': datetime.now()
                    })
                    
                    cursor.execute(
                        "UPDATE companies SET AUTHORIZED_CAPITAL = %s, LAST_UPDATED = %s WHERE CIN = %s",
                        (new_capital, datetime.now(), cin)
                    )
                
                elif random.random() < 0.03:
                    changes.append({
                        'CIN': cin,
                        'CHANGE_TYPE': 'Deregistration',
                        'FIELD_CHANGED': 'COMPANY_STATUS',
                        'OLD_VALUE': status,
                        'NEW_VALUE': 'Strike Off',
                        'CHANGE_DATE': datetime.now()
                    })
                    
                    cursor.execute(
                        "UPDATE companies SET COMPANY_STATUS = 'Strike Off', LAST_UPDATED = %s WHERE CIN = %s",
                        (datetime.now(), cin)
                    )
            
            for change in changes:
                cursor.execute("""
                    INSERT INTO change_logs (CIN, CHANGE_TYPE, FIELD_CHANGED, OLD_VALUE, NEW_VALUE, CHANGE_DATE)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    change['CIN'], change['CHANGE_TYPE'], change['FIELD_CHANGED'],
                    change['OLD_VALUE'], change['NEW_VALUE'], change['CHANGE_DATE']
                ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"Simulated {len(changes)} company changes")
            return changes
            
        except Exception as e:
            logger.error(f"Error simulating changes: {str(e)}")
            return []
    
    def detect_changes_from_snapshots(self):
        logger.info("Detecting changes from snapshots...")
        
        try:
            snapshot_files = sorted(self.snapshots_dir.glob("snapshot_*.csv"))
            
            if len(snapshot_files) < 2:
                logger.warning("Need at least 2 snapshots to detect changes")
                return []
            
            current_snapshot = snapshot_files[-1]
            previous_snapshot = snapshot_files[-2]
            
            logger.info(f"Comparing {previous_snapshot.name} with {current_snapshot.name}")
            
            current_df = pd.read_csv(current_snapshot)
            previous_df = pd.read_csv(previous_snapshot)
            
            current_df.set_index('cin', inplace=True)
            previous_df.set_index('cin', inplace=True)
            
            changes = []
            
            new_companies = set(current_df.index) - set(previous_df.index)
            for cin in new_companies:
                changes.append({
                    'CIN': cin,
                    'CHANGE_TYPE': 'New Incorporation',
                    'FIELD_CHANGED': 'ALL',
                    'OLD_VALUE': 'N/A',
                    'NEW_VALUE': 'New Company',
                    'CHANGE_DATE': datetime.now()
                })
            
            deregistered = set(previous_df.index) - set(current_df.index)
            for cin in deregistered:
                changes.append({
                    'CIN': cin,
                    'CHANGE_TYPE': 'Deregistration',
                    'FIELD_CHANGED': 'COMPANY_STATUS',
                    'OLD_VALUE': 'Active',
                    'NEW_VALUE': 'Strike Off',
                    'CHANGE_DATE': datetime.now()
                })
            
            common_cins = set(current_df.index) & set(previous_df.index)
            for cin in common_cins:
                current_row = current_df.loc[cin]
                previous_row = previous_df.loc[cin]
                
                fields_to_check = ['company_status', 'authorized_capital', 'paidup_capital', 'company_class']
                
                for field in fields_to_check:
                    if field in current_row and field in previous_row:
                        if current_row[field] != previous_row[field]:
                            change_type = self._get_change_type(field)
                            changes.append({
                                'CIN': cin,
                                'CHANGE_TYPE': change_type,
                                'FIELD_CHANGED': field,
                                'OLD_VALUE': str(previous_row[field]),
                                'NEW_VALUE': str(current_row[field]),
                                'CHANGE_DATE': datetime.now()
                            })
            
            logger.info(f"Detected {len(changes)} changes from snapshot comparison")
            return changes
            
        except Exception as e:
            logger.error(f"Error detecting changes from snapshots: {str(e)}")
            return []
    
    def _get_change_type(self, field):
        field_mapping = {
            'company_status': 'Status Change',
            'authorized_capital': 'Capital Change',
            'paidup_capital': 'Capital Change',
            'company_class': 'Classification Change'
        }
        return field_mapping.get(field, 'Field Update')
    
    def save_changes_to_files(self, changes):
        if not changes:
            logger.info("No changes to save")
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        csv_file = self.change_logs_dir / f"changes_{timestamp}.csv"
        df = pd.DataFrame(changes)
        df.to_csv(csv_file, index=False)
        
        json_file = self.change_logs_dir / f"changes_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump(changes, f, indent=2, default=str)
        
        logger.info(f"Changes saved to {csv_file} and {json_file}")
    
    def generate_daily_report(self, changes):
        logger.info("Generating daily report...")
        
        try:
            change_counts = {}
            for change in changes:
                change_type = change['CHANGE_TYPE']
                change_counts[change_type] = change_counts.get(change_type, 0) + 1
            
            report = f"""
# Daily MCA Data Update Report - {datetime.now().strftime('%Y-%m-%d')}

## Summary
- Total Changes Detected: {len(changes)}
- Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Change Breakdown
"""
            
            for change_type, count in change_counts.items():
                report += f"- {change_type}: {count} companies\n"
            
            report += f"""
## Recent Changes
"""
            
            for change in changes[-10:]:
                report += f"- {change['CIN']}: {change['CHANGE_TYPE']} - {change['FIELD_CHANGED']}\n"
            
            report_file = self.reports_dir / f"daily_report_{datetime.now().strftime('%Y%m%d')}.txt"
            with open(report_file, 'w') as f:
                f.write(report)
            
            logger.info(f"Daily report saved: {report_file}")
            
            try:
                ai_summary = self.ai_engine.generate_daily_summary()
                ai_report_file = self.reports_dir / f"ai_summary_{datetime.now().strftime('%Y%m%d')}.txt"
                with open(ai_report_file, 'w') as f:
                    f.write(ai_summary)
                logger.info(f"AI summary saved: {ai_report_file}")
            except Exception as e:
                logger.warning(f"AI summary generation failed: {str(e)}")
            
        except Exception as e:
            logger.error(f"Error generating daily report: {str(e)}")
    
    def run_daily_update(self):
        logger.info("=" * 60)
        logger.info("STARTING DAILY MCA DATA UPDATE")
        logger.info("=" * 60)
        
        try:
            snapshot_file = self.create_daily_snapshot()
            if not snapshot_file:
                logger.error("Failed to create snapshot")
                return False
            
            simulated_changes = self.simulate_company_changes()
            detected_changes = self.detect_changes_from_snapshots()
            
            all_changes = simulated_changes + detected_changes
            
            self.save_changes_to_files(all_changes)
            self.generate_daily_report(all_changes)
            
            if all_changes:
                logger.info("Running enrichment for changed companies...")
                try:
                    changed_cins = list(set([change['CIN'] for change in all_changes]))
                    self.enricher.run_enrichment_process(limit=len(changed_cins))
                except Exception as e:
                    logger.warning(f"Enrichment failed: {str(e)}")
            
            logger.info("=" * 60)
            logger.info("DAILY UPDATE COMPLETED SUCCESSFULLY")
            logger.info(f"Total changes processed: {len(all_changes)}")
            logger.info("=" * 60)
            
            return True
            
        except Exception as e:
            logger.error(f"Daily update failed: {str(e)}")
            return False

def main():
    simulator = DailyUpdateSimulator()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "snapshot":
            simulator.create_daily_snapshot()
        elif command == "simulate":
            simulator.simulate_company_changes()
        elif command == "detect":
            simulator.detect_changes_from_snapshots()
        elif command == "report":
            changes = simulator.detect_changes_from_snapshots()
            simulator.generate_daily_report(changes)
        else:
            print("Available commands: snapshot, simulate, detect, report, full")
    else:
        simulator.run_daily_update()

if __name__ == "__main__":
    main()