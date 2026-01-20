#!/bin/bash
# Build script for Cold Email Outreach Engine (Linux/Mac)

echo ""
echo "========================================"
echo "  Building Cold Email Engine Executable"
echo "========================================"
echo ""

# Check if PyInstaller is installed
pip show pyinstaller > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "Installing PyInstaller..."
    pip install pyinstaller
fi

# Build the executable
echo "Building executable... This may take a minute."
pyinstaller cold_email_app.spec --noconfirm

echo ""
echo "========================================"
echo "  Build Complete!"
echo "========================================"
echo ""
echo "Your executable is at:"
echo "  dist/ColdEmailEngine"
echo ""
echo "To use it:"
echo "  1. Copy ColdEmailEngine to a new folder"
echo "  2. Copy the 'data' folder to that same location"
echo "  3. Run ./ColdEmailEngine from terminal"
echo ""
echo "Usage examples:"
echo "  ./ColdEmailEngine leads.csv"
echo "  ./ColdEmailEngine leads.csv --skip-ai"
echo ""
