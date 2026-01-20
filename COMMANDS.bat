@echo off
REM Quick reference script - shows all available commands
echo.
echo ================================================================================
echo                    COLD EMAIL ENGINE - COMMAND REFERENCE
echo ================================================================================
echo.
echo BUILDING THE EXECUTABLE (First time only):
echo.
echo   Double-click: build.bat
echo   Or command:   pyinstaller cold_email_app.spec --noconfirm
echo.
echo   Creates: dist/ColdEmailEngine.exe
echo.
echo ================================================================================
echo.
echo USING THE EXECUTABLE:
echo.
echo   FULL PIPELINE (with AI personalization):
echo   ColdEmailEngine.exe leads.csv
echo.
echo   FAST VERSION (skip AI - 5x faster):
echo   ColdEmailEngine.exe leads.csv --skip-ai
echo.
echo   INTERACTIVE MENU (no command line needed):
echo   python launcher.py
echo.
echo ================================================================================
echo.
echo CREATING DISTRIBUTION PACKAGE:
echo.
echo   Double-click: package_distribution.bat
echo   Creates: ColdEmailEngine_Portable/ folder
echo   Ready to ship to users!
echo.
echo ================================================================================
echo.
echo DOCUMENTATION:
echo.
echo   START_HERE.txt             - Read this first!
echo   QUICK_START.txt            - 1-page quick reference
echo   USAGE.txt                  - Complete user guide
echo   COMPLETE_WORKFLOW.txt      - Detailed walkthrough
echo   BUILD.md                   - Build instructions
echo.
echo ================================================================================
echo.
pause
