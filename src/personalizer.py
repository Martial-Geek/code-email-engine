"""
Step 7: AI Personalization Engine
Uses Ollama to generate personalized first lines for each lead.
"""

import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any
import ollama
import sys
import time

sys.path.append(str(Path(__file__).parent.parent))

from config.settings import EMAILS_DIR, FINAL_DIR, OLLAMA_MODEL
from utils.helpers import load_csv_safe, save_csv, log_step, log_success, log_warning, log_error
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn


def build_context(row: pd.Series) -> str:
    """
    Build context string for AI from lead data.
    """
    
    parts = []
    
    company = row.get('company_name', 'Unknown Company')
    parts.append(f"Company: {company}")
    
    website = row.get('website', '')
    if website:
        parts.append(f"Website: {website}")
    
    title = row.get('title', '')
    if title:
        parts.append(f"Website title: {title}")
    
    # Issues detected
    reasons = row.get('score_reasons', '')
    if reasons and reasons != 'none':
        issue_map = {
            'no_ssl': 'website lacks HTTPS/SSL security',
            'slow': 'website loads slowly (over 3 seconds)',
            'very_slow': 'website loads very slowly (over 5 seconds)',
            'no_contact_page': 'no contact page found',
            'old_cms': 'using outdated CMS version',
            'no_mobile': 'website is not mobile-friendly',
            'no_meta': 'missing meta description for SEO'
        }
        
        issues = []
        for reason in reasons.split(','):
            if reason in issue_map:
                issues.append(issue_map[reason])
        
        if issues:
            parts.append(f"Technical issues: {', '.join(issues)}")
    
    load_time = row.get('load_time', 0)
    if load_time > 0:
        parts.append(f"Page load time: {load_time} seconds")
    
    cms = row.get('cms_detected', '')
    if cms:
        parts.append(f"CMS: {cms}")
    
    return '\n'.join(parts)


def generate_first_line(context: str, model: str = OLLAMA_MODEL) -> Optional[str]:
    """
    Generate personalized first line using Ollama.
    """
    
    prompt = f"""You are writing the opening line of a cold email to a business owner.

Based on this information about their website:
{context}

Write ONE short, specific opening line (under 20 words) that:
1. References something specific about their website or business
2. Hints at an issue or opportunity without being negative
3. Sounds human and natural, not salesy
4. Does NOT include greetings like "Hi" or "Hello"
5. Does NOT mention your services or solutions

Examples of good first lines:
- "Noticed your site takes a few seconds to load - that can cost you visitors."
- "Your plumbing business has great reviews, but your site might be missing out on mobile visitors."
- "Saw you're still on WordPress 4 - there are some easy wins for speed there."

Write only the first line, nothing else:"""

    try:
        response = ollama.generate(
            model=model,
            prompt=prompt,
            options={
                'temperature': 0.7,
                'num_predict': 50,
            }
        )
        
        first_line = response['response'].strip()
        
        # Clean up common issues
        first_line = first_line.strip('"\'')
        
        # Remove if it starts with greetings
        greetings = ['hi ', 'hello ', 'hey ', 'dear ']
        for g in greetings:
            if first_line.lower().startswith(g):
                first_line = first_line[len(g):]
        
        return first_line if len(first_line) > 10 else None
        
    except Exception as e:
        log_error(f"Ollama error: {e}")
        return None


def personalize_leads(
    input_file: str, 
    output_file: str = None,
    batch_size: int = 10,
    delay: float = 0.5
) -> pd.DataFrame:
    """
    Main function to generate personalized first lines for all leads.
    
    Args:
        input_file: Input CSV from email guesser (best emails)
        output_file: Output CSV filename
        batch_size: Process in batches (for progress reporting)
        delay: Delay between API calls (seconds)
    """
    
    log_step("Starting AI personalization")
    
    # Check Ollama is running
    try:
        ollama.list()
        log_success("Ollama connected")
    except Exception as e:
        log_error(f"Cannot connect to Ollama: {e}")
        log_warning("Make sure Ollama is running: ollama serve")
        return pd.DataFrame()
    
    # Load email data
    input_path = EMAILS_DIR / input_file
    df = load_csv_safe(str(input_path))
    
    if df.empty:
        return pd.DataFrame()
    
    log_success(f"Loaded {len(df)} leads to personalize")
    
    # Generate first lines
    first_lines = []
    failed = 0
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
    ) as progress:
        
        task = progress.add_task("Generating first lines...", total=len(df))
        
        for idx, row in df.iterrows():
            context = build_context(row)
            first_line = generate_first_line(context)
            
            if first_line:
                first_lines.append(first_line)
            else:
                # Fallback generic line
                company = row.get('company_name', 'your business')
                first_lines.append(f"Took a look at {company}'s website and had a few thoughts.")
                failed += 1
            
            progress.update(task, advance=1)
            time.sleep(delay)  # Rate limiting
    
    df['first_line'] = first_lines
    
    # Stats
    log_step("Personalization complete")
    log_success(f"Generated {len(df) - failed} custom first lines")
    if failed > 0:
        log_warning(f"Used fallback for {failed} leads")
    
    # Preview a few
    log_step("Sample first lines:")
    for _, row in df.head(3).iterrows():
        print(f"  [{row['company_name']}]: {row['first_line']}")
    
    # Save output
    if output_file is None:
        output_file = input_file.replace('_emails', '_personalized').replace('.csv', '_personalized.csv')
    
    output_path = FINAL_DIR / output_file
    save_csv(df, str(output_path))
    
    return df


def main():
    """Run personalizer from command line."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate AI-powered first lines')
    parser.add_argument('input_file', help='Input CSV filename (in data/emails/)')
    parser.add_argument('output_file', nargs='?', help='Output CSV filename (in data/final/)')
    parser.add_argument('--delay', type=float, default=0.5, help='Delay between API calls')
    
    args = parser.parse_args()
    personalize_leads(args.input_file, args.output_file, delay=args.delay)


if __name__ == "__main__":
    main()