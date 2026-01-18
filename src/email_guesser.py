"""
Step 5: Email Pattern Guessing
Generates probable email addresses for each lead.
"""

import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import re
import sys

sys.path.append(str(Path(__file__).parent.parent))

from config.settings import SCORED_DIR, EMAILS_DIR, EMAIL_PATTERNS
from utils.helpers import load_csv_safe, save_csv, log_step, log_success, log_warning


def extract_name_parts(company_name: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Try to extract first and last name from company name.
    Works best for names like "John Smith Plumbing" or "Smith & Sons".
    """
    
    if not company_name:
        return None, None
    
    # Clean up
    name = company_name.strip()
    
    # Remove common business suffixes
    suffixes = [
        'plumbing', 'electric', 'electrical', 'roofing', 'construction',
        'services', 'solutions', 'consulting', 'agency', 'studio',
        'design', 'marketing', 'group', 'company', 'co', 'llc', 'inc',
        '& sons', '& associates', '& co', 'and sons', 'and associates'
    ]
    
    name_lower = name.lower()
    for suffix in suffixes:
        if name_lower.endswith(suffix):
            name = name[:-(len(suffix))].strip()
            name_lower = name.lower()
    
    # Remove special characters
    name = re.sub(r'[^a-zA-Z\s]', '', name).strip()
    
    # Split into parts
    parts = name.split()
    
    if len(parts) >= 2:
        return parts[0].lower(), parts[-1].lower()
    elif len(parts) == 1:
        return parts[0].lower(), None
    
    return None, None


def generate_email_patterns(domain: str, first: Optional[str], last: Optional[str]) -> List[Dict]:
    """
    Generate possible email addresses with confidence scores.
    """
    
    emails = []
    
    # Generic emails (always include, moderate confidence)
    generic_patterns = [
        ('info@{domain}', 70),
        ('contact@{domain}', 65),
        ('hello@{domain}', 60),
        ('admin@{domain}', 50),
        ('sales@{domain}', 45),
    ]
    
    for pattern, confidence in generic_patterns:
        email = pattern.format(domain=domain)
        emails.append({
            'email': email,
            'pattern': pattern,
            'confidence': confidence,
            'type': 'generic'
        })
    
    # Personal emails (if we have name info)
    if first:
        personal_patterns = [
            ('{first}@{domain}', 75),
        ]
        
        if last:
            personal_patterns.extend([
                ('{first}.{last}@{domain}', 85),
                ('{first}{last}@{domain}', 70),
                ('{f}{last}@{domain}', 65),
                ('{first}_{last}@{domain}', 55),
                ('{last}.{first}@{domain}', 50),
            ])
        
        for pattern, confidence in personal_patterns:
            try:
                email = pattern.format(
                    domain=domain,
                    first=first,
                    last=last if last else '',
                    f=first[0] if first else ''
                )
                # Skip if pattern didn't fully resolve
                if '{' not in email and email.count('@') == 1:
                    emails.append({
                        'email': email,
                        'pattern': pattern,
                        'confidence': confidence,
                        'type': 'personal'
                    })
            except Exception:
                continue
    
    return emails


def is_valid_email_format(email: str) -> bool:
    """Basic email format validation."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def guess_emails(input_file: str, output_file: str = None, max_per_domain: int = 3) -> pd.DataFrame:
    """
    Main function to generate email guesses for all leads.
    
    Args:
        input_file: Input CSV from scored leads
        output_file: Output CSV filename
        max_per_domain: Maximum email guesses per domain
    """
    
    log_step("Starting email pattern guessing")
    
    # Load scored data
    input_path = SCORED_DIR / input_file
    df = load_csv_safe(str(input_path))
    
    if df.empty:
        return pd.DataFrame()
    
    log_success(f"Loaded {len(df)} leads")
    
    # Generate emails for each lead
    all_emails = []
    
    for _, row in df.iterrows():
        domain = row.get('domain')
        company = row.get('company_name', '')
        
        if not domain:
            continue
        
        # Extract name parts
        first, last = extract_name_parts(company)
        
        # Generate patterns
        patterns = generate_email_patterns(domain, first, last)
        
        # Filter valid emails and sort by confidence
        valid_patterns = [p for p in patterns if is_valid_email_format(p['email'])]
        valid_patterns.sort(key=lambda x: x['confidence'], reverse=True)
        
        # Take top N
        for pattern in valid_patterns[:max_per_domain]:
            all_emails.append({
                'domain': domain,
                'company_name': company,
                'email': pattern['email'],
                'confidence': pattern['confidence'],
                'pattern_type': pattern['type'],
                'pattern': pattern['pattern'],
                # Carry over important fields
                'score': row.get('score', 0),
                'priority': row.get('priority', ''),
                'website': row.get('website', ''),
                'title': row.get('title', ''),
                'score_reasons': row.get('score_reasons', ''),
            })
    
    emails_df = pd.DataFrame(all_emails)
    
    # Stats
    total_emails = len(emails_df)
    unique_domains = emails_df['domain'].nunique()
    avg_confidence = emails_df['confidence'].mean()
    
    type_counts = emails_df['pattern_type'].value_counts()
    
    log_step("Email guessing complete")
    log_success(f"Generated {total_emails} email guesses")
    log_success(f"Covering {unique_domains} domains")
    log_success(f"Average confidence: {avg_confidence:.1f}%")
    log_success(f"Generic emails: {type_counts.get('generic', 0)}")
    log_success(f"Personal emails: {type_counts.get('personal', 0)}")
    
    # Save output
    if output_file is None:
        output_file = input_file.replace('_scored.csv', '_emails.csv').replace('.csv', '_emails.csv')
    
    output_path = EMAILS_DIR / output_file
    save_csv(emails_df, str(output_path))
    
    # Also save a deduplicated version (one email per domain, highest confidence)
    best_emails = emails_df.sort_values('confidence', ascending=False).drop_duplicates(subset=['domain'], keep='first')
    best_output = output_file.replace('.csv', '_best.csv')
    save_csv(best_emails, str(EMAILS_DIR / best_output))
    log_success(f"Also saved best-guess file with {len(best_emails)} unique emails")
    
    return emails_df


def main():
    """Run email guesser from command line."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate email address guesses')
    parser.add_argument('input_file', help='Input CSV filename (in data/scored/)')
    parser.add_argument('output_file', nargs='?', help='Output CSV filename (in data/emails/)')
    parser.add_argument('--max', type=int, default=3, help='Max emails per domain')
    
    args = parser.parse_args()
    guess_emails(args.input_file, args.output_file, args.max)


if __name__ == "__main__":
    main()