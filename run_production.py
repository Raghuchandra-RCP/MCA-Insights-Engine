#!/usr/bin/env python3
"""
Production startup script for MCA Insights Engine
"""

import os
import sys
import logging
from flask_dashboard import app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/mca_insights.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    
    logger.info(f"Starting MCA Insights Engine on {host}:{port}")
    
    # Run with Gunicorn in production
    if os.environ.get('FLASK_ENV') == 'production':
        import gunicorn.app.wsgiapp as wsgi
        sys.argv = [
            'gunicorn',
            '--bind', f'{host}:{port}',
            '--workers', '4',
            '--timeout', '30',
            '--access-logfile', '-',
            '--error-logfile', '-',
            'flask_dashboard:app'
        ]
        wsgi.run()
    else:
        # Development mode
        app.run(host=host, port=port, debug=True)
