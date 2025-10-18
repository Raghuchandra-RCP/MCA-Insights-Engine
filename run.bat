@echo off
echo ========================================
echo   MCA Insights Engine - Quick Setup
echo ========================================
echo.

echo Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.11+ from https://python.org
    pause
    exit /b 1
)

echo Python found! Checking version...
python -c "import sys; print('Python version:', sys.version)"

echo.
echo Installing required packages...
pip install -r requirements-simple.txt

echo.
echo Setting up database...
python data_integration.py

echo.
echo Populating database with sample data...
python mca_data_processor.py

echo.
echo Starting MCA Insights Engine...
echo.
echo ========================================
echo   Application will be available at:
echo   http://localhost:5000
echo ========================================
echo.
echo Press Ctrl+C to stop the application
echo.

python flask_dashboard.py

pause
