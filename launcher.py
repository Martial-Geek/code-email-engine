#!/usr/bin/env python3
"""
Interactive launcher for non-technical users.
Run this instead of command line for a guided experience.
"""

import subprocess
import sys
import os
from pathlib import Path


def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def show_banner():
    """Display welcome banner."""
    print("\n" + "=" * 70)
    print("         COLD EMAIL OUTREACH ENGINE - INTERACTIVE LAUNCHER".center(70))
    print("=" * 70 + "\n")


def list_csv_files():
    """List available CSV files in data/raw/"""
    raw_dir = Path("data/raw")
    if not raw_dir.exists():
        print("ERROR: data/raw folder not found!")
        return []
    
    csv_files = list(raw_dir.glob("*.csv"))
    if not csv_files:
        print("No CSV files found in data/raw/")
        print("Please add your leads CSV file there first.\n")
        return []
    
    return [f.name for f in sorted(csv_files)]


def main():
    clear_screen()
    show_banner()
    
    # Check if executable exists
    exe_path = Path("ColdEmailEngine.exe") if os.name == 'nt' else Path("ColdEmailEngine")
    if not exe_path.exists():
        print("⚠️  ColdEmailEngine executable not found!")
        print("Run: python build.py")
        print("Or: pyinstaller cold_email_app.spec --noconfirm")
        input("\nPress Enter to exit...")
        return
    
    # Get available CSV files
    csv_files = list_csv_files()
    
    if not csv_files:
        print("\nPlease add your CSV file to the data/raw/ folder")
        print("Examples: leads.csv, prospects.csv, contacts.csv\n")
        input("Press Enter to exit...")
        return
    
    # Show options
    print("📁 AVAILABLE CSV FILES:")
    for i, f in enumerate(csv_files, 1):
        print(f"   {i}. {f}")
    
    print("\n" + "-" * 70)
    print("\n🚀 SELECT AN OPTION:\n")
    print("1. Run FULL PIPELINE (with AI personalization)")
    print("2. Run FAST VERSION (skip AI - 10x faster)")
    print("3. Exit\n")
    
    choice = input("Enter your choice (1-3): ").strip()
    
    if choice == "3":
        print("\nGoodbye!")
        return
    
    if choice not in ["1", "2"]:
        print("\n❌ Invalid choice!")
        input("Press Enter to exit...")
        return
    
    # Select CSV file
    if len(csv_files) == 1:
        csv_file = csv_files[0]
        print(f"\nUsing: {csv_file}")
    else:
        print("\n📋 SELECT YOUR CSV FILE:\n")
        for i, f in enumerate(csv_files, 1):
            print(f"   {i}. {f}")
        
        file_choice = input("\nEnter number: ").strip()
        try:
            csv_file = csv_files[int(file_choice) - 1]
        except (ValueError, IndexError):
            print("\n❌ Invalid selection!")
            input("Press Enter to exit...")
            return
    
    # Confirm and run
    print("\n" + "=" * 70)
    skip_ai = " --skip-ai" if choice == "2" else ""
    mode = "FAST MODE (no AI)" if choice == "2" else "FULL PIPELINE (with AI)"
    print(f"\nRunning: {mode}")
    print(f"File: {csv_file}")
    print("\nThis may take 5-20 minutes. Please wait...\n")
    print("=" * 70 + "\n")
    
    # Run the pipeline
    try:
        cmd = f"ColdEmailEngine.exe {csv_file}{skip_ai}" if os.name == 'nt' else f"./ColdEmailEngine {csv_file}{skip_ai}"
        subprocess.run(cmd, shell=True, check=False)
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    print("\n✅ Process complete!")
    print("\nYour results are in:")
    print("  📄 data/final/instantly_upload.csv")
    print("  📧 data/final/email_templates.txt")
    print("\nOpen these files to review and customize before uploading to Instantly.\n")
    
    input("Press Enter to exit...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCancelled by user.")
        sys.exit(0)
