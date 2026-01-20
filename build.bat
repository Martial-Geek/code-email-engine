@echo off
REM Build script for Cold Email Outreach Engine

echo.
echo ========================================
echo  Building Cold Email Engine Executable
echo ========================================
echo.

REM Check if PyInstaller is installed
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

REM Build the executable
echo Building executable... This may take a minute.
pyinstaller cold_email_app.spec --noconfirm

echo.
echo ========================================
echo  Build Complete!
echo ========================================
echo.
echo Your executable is at:
echo   dist\ColdEmailEngine.exe
echo.
echo To use it:
echo   1. Copy ColdEmailEngine.exe to a new folder
echo   2. Copy the 'data' folder to that same location
echo   3. Run ColdEmailEngine.exe from command line
echo.
echo Usage examples:
echo   ColdEmailEngine.exe leads.csv
echo   ColdEmailEngine.exe leads.csv --skip-ai
echo.
pause
