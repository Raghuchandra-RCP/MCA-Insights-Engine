import argparse
import sys
import os
from datetime import datetime
from data_integration import MCADataIntegrator
from change_detection import ChangeDetector
from cin_enrichment import CINEnricher
from ai_insights import AIInsightsEngine
from config import *

def main():
    parser = argparse.ArgumentParser(description='MCA Insights Engine')
    parser.add_argument('command', choices=[
        'integrate', 'detect-changes', 'enrich', 'ai-summary', 'ai-chat', 
        'dashboard', 'api-server', 'full-pipeline', 'process-real-data'
    ], help='Command to execute')
    
    parser.add_argument('--data-dir', default='data/raw', help='Directory containing raw data files')
    parser.add_argument('--sample-size', type=int, default=100, help='Sample size for enrichment')
    parser.add_argument('--date', default=datetime.now().strftime('%Y-%m-%d'), help='Date for operations')
    parser.add_argument('--query', help='Query for AI chat')
    parser.add_argument('--port', type=int, default=8501, help='Port for dashboard')
    parser.add_argument('--api-port', type=int, default=5000, help='Port for API server')
    
    args = parser.parse_args()
    
    print(f"MCA Insights Engine - {args.command.upper()}")
    print("=" * 50)
    
    try:
        if args.command == 'integrate':
            run_data_integration(args.data_dir)
        elif args.command == 'detect-changes':
            run_change_detection()
        elif args.command == 'enrich':
            run_enrichment(args.sample_size)
        elif args.command == 'ai-summary':
            run_ai_summary(args.date)
        elif args.command == 'ai-chat':
            run_ai_chat(args.query)
        elif args.command == 'dashboard':
            run_flask_dashboard(args.port)
        elif args.command == 'api-server':
            run_api_server(args.api_port)
        elif args.command == 'full-pipeline':
            run_full_pipeline(args.data_dir, args.sample_size)
        elif args.command == 'process-real-data':
            run_real_data_processing()
        
        print("Operation completed successfully!")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

def run_data_integration(data_dir):
    print("Starting data integration...")
    
    integrator = MCADataIntegrator()
    
    csv_files = []
    if os.path.exists(data_dir):
        for file in os.listdir(data_dir):
            if file.endswith('.csv'):
                state_name = file.replace('.csv', '').replace('_', ' ').title()
                csv_files[state_name] = os.path.join(data_dir, file)
    
    if not csv_files:
        print(f"No CSV files found in {data_dir}")
        return
    
    master_data = integrator.consolidate_data(csv_files)
    
    if master_data is not None:
        integrator.save_to_database(master_data)
        integrator.export_processed_data(master_data)
        print(f"Processed {len(master_data)} companies")
    else:
        print("No data to process")

def run_change_detection():
    print("Starting change detection...")
    
    detector = ChangeDetector()
    summary = detector.get_changes_summary()
    
    print(f"Change Summary:")
    print(f"  - Total changes: {summary['total_changes']}")
    print(f"  - New incorporations: {summary['new_incorporations']}")
    print(f"  - Deregistrations: {summary['deregistrations']}")
    print(f"  - Status changes: {summary['status_changes']}")
    print(f"  - Capital changes: {summary['capital_changes']}")

def run_enrichment(sample_size):
    print(f"Starting data enrichment (sample size: {sample_size})...")
    
    enricher = CINEnricher()
    enriched_data = enricher.run_enrichment_process(sample_size)
    
    if enriched_data:
        print(f"Enriched {len(enriched_data)} companies")
        summary = enricher.get_enrichment_summary()
        print(f"Enrichment Summary:")
        print(f"  - Total enriched: {summary['total_enriched']}")
        print(f"  - With sector info: {summary['with_sector']}")
        print(f"  - With industry info: {summary['with_industry']}")
        print(f"  - With director info: {summary['with_directors']}")
        print(f"  - With website info: {summary['with_website']}")
    else:
        print("No companies were enriched")

def run_ai_summary(date):
    print(f"Generating AI summary for {date}...")
    
    ai_engine = AIInsightsEngine()
    summary = ai_engine.generate_daily_summary(date)
    
    print("Daily Summary Generated:")
    print("-" * 40)
    print(summary)
    print("-" * 40)

def run_ai_chat(query):
    if not query:
        query = input("Enter your question: ")
    
    print(f"Processing query: {query}")
    
    ai_engine = AIInsightsEngine()
    response = ai_engine.chat_with_data(query)
    
    print(f"Response: {response}")

def run_flask_dashboard(port):
    print(f"Starting Flask dashboard on port {port}...")
    
    from flask_dashboard import app
    app.run(host='0.0.0.0', port=port, debug=False)

def run_api_server(port):
    print(f"Starting API server on port {port}...")
    
    from api_server import app
    app.run(host='0.0.0.0', port=port, debug=False)

def run_real_data_processing():
    print("Processing real MCA data from 5 states...")
    
    from mca_data_processor import MCADataProcessor
    
    processor = MCADataProcessor()
    processor.run_full_processing()
    
    print("\nReal MCA data processing completed!")
    print("\nYou can now run:")
    print("  - Dashboard: python main.py dashboard")
    print("  - API Server: python main.py api-server")

def run_full_pipeline(data_dir, sample_size):
    print("Running full MCA Insights Engine pipeline...")
    
    print("\n1. Data Integration")
    run_data_integration(data_dir)
    
    print("\n2. Change Detection")
    run_change_detection()
    
    print("\n3. Data Enrichment")
    run_enrichment(sample_size)
    
    print("\n4. AI Summary Generation")
    run_ai_summary(datetime.now().strftime('%Y-%m-%d'))
    
    print("\nFull pipeline completed successfully!")
    print("\nYou can now run:")
    print("  - Dashboard: python main.py dashboard")
    print("  - API Server: python main.py api-server")

if __name__ == "__main__":
    main()
