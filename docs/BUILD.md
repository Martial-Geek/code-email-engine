# Building the Executable

This guide explains how to package the Cold Email Engine into a standalone executable that non-technical users can run.

## Prerequisites

Make sure you have Python 3.9+ installed and pip is available.

## Quick Build (Windows)

### Option 1: Automatic Build

Simply double-click `build.bat` - it will handle everything:

- Install PyInstaller if needed
- Build the executable
- Show you where the executable is located

### Option 2: Manual Build

1. Open Command Prompt or PowerShell
2. Navigate to the project folder
3. Run these commands:

```bash
pip install pyinstaller
pyinstaller cold_email_app.spec --noconfirm
```

The executable will be created in the `dist/ColdEmailEngine.exe` folder.

## Build on Mac/Linux

1. Open Terminal
2. Navigate to the project folder
3. Make the build script executable:

```bash
chmod +x build.sh
./build.sh
```

Or manually:

```bash
pip install pyinstaller
pyinstaller cold_email_app.spec --noconfirm
```

The executable will be in `dist/ColdEmailEngine`

## Distribution

To distribute to non-technical users:

### Required Files

```
ColdEmailEngine.exe          [or ColdEmailEngine on Mac/Linux]
data/                        [entire data folder with subdirectories]
USAGE.txt                    [instructions for users]
```

### Setup Instructions for Users

1. Create a new folder: `ColdEmailEngine`
2. Copy the executable into it
3. Copy the entire `data` folder
4. Copy `USAGE.txt` for reference
5. Users can now double-click the executable or run from command line

Example folder structure:

```
ColdEmailEngine/
├── ColdEmailEngine.exe
├── USAGE.txt
└── data/
    ├── raw/
    ├── cleaned/
    ├── enriched/
    ├── scored/
    ├── emails/
    └── final/
```

## Command Line Usage

Users can run the executable from command line:

```bash
# Full pipeline with AI personalization
ColdEmailEngine.exe leads.csv

# Skip AI personalization (faster)
ColdEmailEngine.exe leads.csv --skip-ai

# Run individual steps
ColdEmailEngine.exe --step clean leads.csv
ColdEmailEngine.exe --step scrape leads_cleaned.csv
ColdEmailEngine.exe --step score leads_enriched.csv
ColdEmailEngine.exe --step emails leads_scored.csv
ColdEmailEngine.exe --step personalize leads_emails_best.csv
ColdEmailEngine.exe --step sequence leads_personalized.csv
```

## Troubleshooting Build Issues

### "No module named X"

If you get import errors during build, add to the `hiddenimports` list in `cold_email_app.spec`

### File size too large

The executable will be ~150-300MB including all dependencies. This is normal for Python packages.

### Need to rebuild

1. Delete the `build/` and `dist/` folders
2. Run the build command again

## How It Works

The PyInstaller spec file (`cold_email_app.spec`) tells PyInstaller:

- What Python file to start with (`run_pipeline.py`)
- What folders to include (`config/`, `src/`, `utils/`, `data/`)
- What hidden imports are needed (libraries not auto-detected)
- How to name the output executable

The spec is pre-configured for this project, so you just need to run the build.

## Testing the Build

After building, test the executable:

```bash
cd dist/ColdEmailEngine

# Or just dist folder if it created a folder
ColdEmailEngine.exe --help

# Test with sample data
ColdEmailEngine.exe test_leads.csv --skip-ai
```

You should see the normal pipeline output.

---

For more information on using the app, see `USAGE.txt`
