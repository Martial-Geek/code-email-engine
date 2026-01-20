@echo off
REM Distribution packaging script for Windows
REM Creates a portable package ready to ship to users

echo.
echo ========================================
echo  Creating Distribution Package
echo ========================================
echo.

REM Check if executable exists
if not exist "dist\ColdEmailEngine.exe" (
    echo ERROR: ColdEmailEngine.exe not found!
    echo Please run build.bat first to create the executable
    echo.
    pause
    exit /b 1
)

REM Create distribution folder
set DIST_NAME=ColdEmailEngine_Portable
if exist "%DIST_NAME%" (
    echo Removing old distribution folder...
    rmdir /s /q "%DIST_NAME%"
)

echo Creating %DIST_NAME% folder...
mkdir "%DIST_NAME%"

REM Copy executable
echo Copying executable...
copy "dist\ColdEmailEngine.exe" "%DIST_NAME%\"

REM Copy data folder structure
echo Setting up data folders...
if exist "data" (
    xcopy "data" "%DIST_NAME%\data\" /E /I /Y >nul
) else (
    mkdir "%DIST_NAME%\data\raw"
    mkdir "%DIST_NAME%\data\cleaned"
    mkdir "%DIST_NAME%\data\enriched"
    mkdir "%DIST_NAME%\data\scored"
    mkdir "%DIST_NAME%\data\emails"
    mkdir "%DIST_NAME%\data\final"
)

REM Copy documentation
echo Copying documentation...
if exist "USAGE.txt" copy "USAGE.txt" "%DIST_NAME%\"
if exist "QUICK_START.txt" copy "QUICK_START.txt" "%DIST_NAME%\"
if exist "launcher.py" copy "launcher.py" "%DIST_NAME%\"

REM Create README for distribution
(
    echo # Cold Email Outreach Engine
    echo.
    echo This is a portable version ready to use.
    echo.
    echo ## Quick Start
    echo.
    echo 1. Place your CSV file in the data/raw folder
    echo 2. Double-click ColdEmailEngine.exe
    echo 3. Enter your filename
    echo.
    echo OR run from command line:
    echo ```
    echo ColdEmailEngine.exe leads.csv
    echo ColdEmailEngine.exe leads.csv --skip-ai
    echo ```
    echo.
    echo See QUICK_START.txt or USAGE.txt for detailed instructions
    echo.
) > "%DIST_NAME%\README.txt"

echo.
echo ========================================
echo  Distribution Package Created!
echo ========================================
echo.
echo Package location: %DIST_NAME%\
echo.
echo Contents:
echo   - ColdEmailEngine.exe
echo   - data\ (folder structure)
echo   - USAGE.txt (detailed guide)
echo   - QUICK_START.txt (quick reference)
echo   - launcher.py (optional interactive UI)
echo   - README.txt (this file)
echo.
echo You can now:
echo   1. Zip this folder to distribute
echo   2. Or copy to a USB drive
echo   3. Or email to users
echo.
echo Users just need to:
echo   1. Extract the folder
echo   2. Put CSV in data/raw/
echo   3. Double-click ColdEmailEngine.exe
echo.
pause
