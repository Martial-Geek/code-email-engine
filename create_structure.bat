@echo off
echo Creating Website Intelligence Scraper folder structure...

:: Create main directories
mkdir src\scrapers\metrics 2>nul
mkdir src\scrapers\analyzers 2>nul
mkdir src\scrapers\models 2>nul
mkdir src\scrapers\exporters 2>nul
mkdir src\scrapers\reports 2>nul

:: Create __init__.py files
type nul > src\scrapers\__init__.py
type nul > src\scrapers\metrics\__init__.py
type nul > src\scrapers\analyzers\__init__.py
type nul > src\scrapers\models\__init__.py
type nul > src\scrapers\exporters\__init__.py
type nul > src\scrapers\reports\__init__.py

:: Create metrics files
type nul > src\scrapers\metrics\load_time.py
type nul > src\scrapers\metrics\performance.py
type nul > src\scrapers\metrics\seo.py
type nul > src\scrapers\metrics\security.py
type nul > src\scrapers\metrics\accessibility.py
type nul > src\scrapers\metrics\business.py

:: Create analyzers files
type nul > src\scrapers\analyzers\html_analyzer.py
type nul > src\scrapers\analyzers\cms_detector.py
type nul > src\scrapers\analyzers\tech_detector.py
type nul > src\scrapers\analyzers\page_checker.py

:: Create models files
type nul > src\scrapers\models\website_intelligence.py

:: Create exporters files
type nul > src\scrapers\exporters\csv_exporter.py
type nul > src\scrapers\exporters\pdf_exporter.py

:: Create reports files
type nul > src\scrapers\reports\base_report.py
type nul > src\scrapers\reports\seo_report.py
type nul > src\scrapers\reports\performance_report.py
type nul > src\scrapers\reports\security_report.py
type nul > src\scrapers\reports\full_report.py

:: Create main files
type nul > src\scrapers\main.py
type nul > src\scrapers\base_scraper.py

echo.
echo Folder structure created successfully!
echo.
pause