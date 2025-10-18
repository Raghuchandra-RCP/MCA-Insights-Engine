#!/bin/bash

echo "========================================"
echo "  MCA Insights Engine - Quick Setup"
echo "========================================"
echo

echo "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 is not installed"
    echo "Please install Python 3.11+ from https://python.org"
    exit 1
fi

echo "Python found! Checking version..."
python3 --version

echo
echo "Installing required packages..."
pip3 install -r requirements-simple.txt

echo
echo "Setting up database..."
python3 data_integration.py

echo
echo "Populating database with sample data..."
python3 mca_data_processor.py

echo
echo "Starting MCA Insights Engine..."
echo
echo "========================================"
echo "  Application will be available at:"
echo "  http://localhost:5000"
echo "========================================"
echo
echo "Press Ctrl+C to stop the application"
echo

python3 flask_dashboard.py
