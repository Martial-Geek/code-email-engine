"""
Step 7: AI Personalization Engine
Uses LangChain with Google Gemini to generate personalized first lines for each lead.
"""

import pandas as pd
from pathlib import Path
from typing import Optional
import sys
import time

sys.path.append(str(Path(__file__).parent.parent))

from config.settings import EMAILS_DIR, FINAL_DIR, GEMINI_API_KEY, GEMINI_MODEL
from utils.helpers import load_csv_safe, save_csv, log_step, log_success, log_warning, log_error
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


def get_llm() -> ChatGoogleGenerativeAI:
    """Initialize the Gemini LLM."""
    return ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        google_api_key=GEMINI_API_KEY,
        temperature=0.7,
        max_output_tokens=100,
    )


def get_chain():
    """Build the simple prompt -> LLM -> output chain."""
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You write opening lines for cold emails to business owners.
Rules:
- ONE short line, under 20 words
- Reference something specific about their website
- Hint at an issue or opportunity without being negative
- Sound human, not salesy
- NO greetings (Hi, Hello, Hey)
- NO mentions of your services

Good examples:
- "Noticed your site takes a few seconds to load - that can cost you visitors."
- "Your plumbing business has great reviews, but your site might be missing out on mobile visitors."
- "Saw you're still on WordPress 4 - there are some easy wins for speed there."
"""),
        ("human", """Website info:
{context}

Write only the first line:""")
    ])
    
    llm = get_llm()
    output_parser = StrOutputParser()
    
    return prompt | llm | output_parser


def build_context(row: pd.Series) -> str:
    """Build context string for AI from lead data."""
    
    parts = []
    
    company = row.get('company_name', 'Unknown Company')
    parts.append(f"Company: {company}")
    
    if website := row.get('website', ''):
        parts.append(f"Website: {website}")
    
    if title := row.get('title', ''):
        parts.append(f"Website title: {title}")
    
    # Map issues to readable text
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
        
        issues = [issue_map[r] for r in reasons.split(',') if r in issue_map]
        if issues:
            parts.append(f"Technical issues: {', '.join(issues)}")
    
    if (load_time := row.get('load_time', 0)) > 0:
        parts.append(f"Page load time: {load_time} seconds")
    
    if cms := row.get('cms_detected', ''):
        parts.append(f"CMS: {cms}")
    
    return '\n'.join(parts)


def clean_first_line(text: str) -> Optional[str]:
    """Clean up the generated first line."""
    
    first_line = text.strip().strip('"\'')
    
    # Remove greetings
    greetings = ['hi ', 'hello ', 'hey ', 'dear ']
    for g in greetings:
        if first_line.lower().startswith(g):
            first_line = first_line[len(g):]
    
    return first_line if len(first_line) > 10 else None


def generate_first_line(chain, context: str) -> Optional[str]:
    """Generate personalized first line using the chain."""
    
    try:
        response = chain.invoke({"context": context})
        return clean_first_line(response)
    except Exception as e:
        log_error(f"Generation error: {e}")
        return None


def personalize_leads(
    input_file: str, 
    output_file: str = None,
    delay: float = 0.5
) -> pd.DataFrame:
    """
    Generate personalized first lines for all leads.
    
    Args:
        input_file: Input CSV filename (in data/emails/)
        output_file: Output CSV filename (in data/final/)
        delay: Delay between API calls (seconds) - Gemini free tier has rate limits
    """
    
    log_step("Starting AI personalization")
    
    # Validate API key
    if not GEMINI_API_KEY:
        log_error("GEMINI_API_KEY not set in config/settings.py")
        return pd.DataFrame()
    
    # Initialize chain
    try:
        chain = get_chain()
        log_success("Gemini connected")
    except Exception as e:
        log_error(f"Failed to initialize Gemini: {e}")
        return pd.DataFrame()
    
    # Load data
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
            first_line = generate_first_line(chain, context)
            
            if first_line:
                first_lines.append(first_line)
            else:
                # Fallback
                company = row.get('company_name', 'your business')
                first_lines.append(f"Took a look at {company}'s website and had a few thoughts.")
                failed += 1
            
            progress.update(task, advance=1)
            time.sleep(delay)  # Rate limiting for free tier
    
    df['first_line'] = first_lines
    
    # Stats
    log_step("Personalization complete")
    log_success(f"Generated {len(df) - failed} custom first lines")
    if failed > 0:
        log_warning(f"Used fallback for {failed} leads")
    
    # Preview
    log_step("Sample first lines:")
    for _, row in df.head(3).iterrows():
        print(f"  [{row['company_name']}]: {row['first_line']}")
    
    # Save
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
    parser.add_argument('--delay', type=float, default=1.0, help='Delay between API calls (default: 1.0 for free tier)')
    
    args = parser.parse_args()
    personalize_leads(args.input_file, args.output_file, delay=args.delay)


if __name__ == "__main__":
    main()