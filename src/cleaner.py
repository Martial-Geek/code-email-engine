"""
Step 2: Lead Cleaning
Takes raw Outscraper export and produces clean lead list.
"""

import pandas as pd
from pathlib import Path
from typing import Optional
import sys

sys.path.append(str(Path(__file__).parent.parent))

from config.settings import RAW_DIR, CLEANED_DIR
from utils.helpers import (
    normalize_url, extract_domain, is_valid_business_domain,
    clean_company_name, load_csv_safe, save_csv,
    log_step, log_success, log_warning, log_error
)


def clean_leads(input_file: str, output_file: Optional[str] = None) -> pd.DataFrame:
    """
    Main cleaning function.
    
    Steps:
    1. Load raw data
    2. Normalize URLs
    3. Extract domains
    4. Remove duplicates
    5. Remove invalid entries
    6. Clean company names
    """
    
    log_step("Starting lead cleaning process")
    
    # Load raw data
    input_path = RAW_DIR / input_file
    df = load_csv_safe(str(input_path))
    
    if df.empty:
        log_error("No data to process")
        return pd.DataFrame()
    
    initial_count = len(df)
    log_success(f"Loaded {initial_count} raw leads")
    
    # Find the website column (Outscraper uses different names)
    website_col = None
    possible_names = ['website', 'site', 'url', 'domain', 'Website']
    for col in possible_names:
        if col in df.columns:
            website_col = col
            break
    
    if not website_col:
        log_error(f"No website column found. Available columns: {df.columns.tolist()}")
        return pd.DataFrame()
    
    # Find company name column
    name_col = None
    possible_names = ['name', 'company', 'business_name', 'title', 'Name']
    for col in possible_names:
        if col in df.columns:
            name_col = col
            break
    
    log_step("Normalizing URLs")
    df['normalized_url'] = df[website_col].apply(normalize_url)
    
    # Remove rows without valid URLs
    before = len(df)
    df = df[df['normalized_url'].notna()]
    log_warning(f"Removed {before - len(df)} rows with invalid URLs")
    
    log_step("Extracting domains")
    df['domain'] = df['normalized_url'].apply(extract_domain)
    
    # Remove rows without valid domains
    before = len(df)
    df = df[df['domain'].notna()]
    log_warning(f"Removed {before - len(df)} rows with invalid domains")
    
    log_step("Filtering business domains")
    before = len(df)
    df = df[df['domain'].apply(is_valid_business_domain)]
    log_warning(f"Removed {before - len(df)} non-business domains")
    
    log_step("Removing duplicates by domain")
    before = len(df)
    df = df.drop_duplicates(subset=['domain'], keep='first')
    log_warning(f"Removed {before - len(df)} duplicate domains")
    
    # Clean company names
    if name_col:
        df['company_name'] = df[name_col].apply(clean_company_name)
    else:
        df['company_name'] = df['domain'].apply(lambda x: x.split('.')[0].title())
    
    # Build clean output
    clean_df = pd.DataFrame({
        'company_name': df['company_name'],
        'domain': df['domain'],
        'website': df['normalized_url']
    })
    
    # Add any extra useful columns from original data
    extra_cols = ['phone', 'address', 'city', 'category', 'google_rating', 'reviews']
    for col in extra_cols:
        matching = [c for c in df.columns if col.lower() in c.lower()]
        if matching:
            clean_df[col] = df[matching[0]].values
    
    log_step("Cleaning complete")
    log_success(f"Started with {initial_count} leads")
    log_success(f"Ended with {len(clean_df)} clean leads")
    log_success(f"Removal rate: {((initial_count - len(clean_df)) / initial_count * 100):.1f}%")
    
    # Save output
    if output_file is None:
        output_file = input_file.replace('.csv', '_cleaned.csv')
    
    output_path = CLEANED_DIR / output_file
    save_csv(clean_df, str(output_path))
    
    return clean_df


def main():
    """
    Run cleaner from command line.
    Usage: python cleaner.py input_file.csv [output_file.csv]
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Clean raw lead data')
    parser.add_argument('input_file', help='Input CSV filename (in data/raw/)')
    parser.add_argument('output_file', nargs='?', help='Output CSV filename (in data/cleaned/)')
    
    args = parser.parse_args()
    
    clean_leads(args.input_file, args.output_file)


if __name__ == "__main__":
    main()