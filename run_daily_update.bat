@echo off
echo ========================================
echo MCA Insights Engine - Daily Update
echo ========================================
echo.
echo Starting daily MCA data update...
echo Time: %date% %time%
echo.

cd /d "%~dp0"

echo [1/4] Creating daily snapshot...
python daily_update_simulator.py snapshot
if %errorlevel% neq 0 (
    echo ERROR: Failed to create snapshot
    pause
    exit /b 1
)

echo.
echo [2/4] Simulating company changes...
python daily_update_simulator.py simulate
if %errorlevel% neq 0 (
    echo ERROR: Failed to simulate changes
    pause
    exit /b 1
)

echo.
echo [3/4] Detecting changes from snapshots...
python daily_update_simulator.py detect
if %errorlevel% neq 0 (
    echo ERROR: Failed to detect changes
    pause
    exit /b 1
)

echo.
echo [4/4] Generating daily report...
python daily_update_simulator.py report
if %errorlevel% neq 0 (
    echo ERROR: Failed to generate report
    pause
    exit /b 1
)

echo.
echo ========================================
echo Daily Update Completed Successfully!
echo ========================================
echo.
echo Check the following directories for results:
echo - data\snapshots\     (Daily snapshots)
echo - data\change_logs\   (Change records)
echo - reports\            (Daily reports)
echo.
echo Time: %date% %time%
echo.
pause