"""
Step 8: Sequence Generator
Builds email sequences ready for upload to Instantly.
"""

import pandas as pd
from pathlib import Path
from typing import List, Dict
import sys

sys.path.append(str(Path(__file__).parent.parent))

from config.settings import FINAL_DIR
from utils.helpers import load_csv_safe, save_csv, log_step, log_success


# Email templates - customize these for your service
EMAIL_TEMPLATES = {
    'email_1': {
        'subject': "Quick question about {{company_name}}",
        'body': """{{first_line}}

I help businesses like yours improve their online presence - faster sites, better conversions, more leads.

Would you be open to a quick chat about what I found?

Best,
[Your Name]""",
        'delay_days': 0
    },
    
    'email_2': {
        'subject': "Re: Quick question about {{company_name}}",
        'body': """Just wanted to follow up on my last note.

I put together a few specific suggestions for {{website}} that could help with [speed/security/mobile experience].

Happy to share if you're interested - no strings attached.

[Your Name]""",
        'delay_days': 3
    },
    
    'email_3': {
        'subject': "Re: Quick question about {{company_name}}",
        'body': """I recently helped [similar business type] improve their site speed by 60% - they saw a noticeable bump in inquiries within weeks.

I think there's similar potential for {{company_name}}.

Worth a 10-minute call?

[Your Name]""",
        'delay_days': 5
    },
    
    'email_4': {
        'subject': "Re: Quick question about {{company_name}}",
        'body': """I'll keep this short - I've reached out a few times about {{company_name}}'s website.

If now isn't the right time, no worries at all. Just let me know and I'll stop following up.

But if you've been meaning to reply - I'm here whenever you're ready.

[Your Name]""",
        'delay_days': 7
    }
}


def build_sequence(
    input_file: str,
    output_file: str = None,
    include_all_steps: bool = True
) -> pd.DataFrame:
    """
    Build email sequences for upload to Instantly.
    
    For Instantly CSV upload, we need:
    - email
    - first_name (optional)
    - company_name
    - custom variables (first_line, website, etc.)
    """
    
    log_step("Building email sequences")
    
    # Load personalized data
    input_path = FINAL_DIR / input_file
    df = load_csv_safe(str(input_path))
    
    if df.empty:
        return pd.DataFrame()
    
    log_success(f"Loaded {len(df)} personalized leads")
    
    # Build Instantly-ready CSV
    # Instantly uses {{variable}} syntax for personalization
    
    # Handle missing first_line column (when AI personalization is skipped)
    first_line_data = df.get('first_line', pd.Series([''] * len(df)))
    if 'first_line' not in df.columns:
        log_step("No personalized first lines found - using placeholders")
    
    instantly_df = pd.DataFrame({
        'email': df['email'],
        'company_name': df['company_name'],
        'website': df['website'],
        'first_line': first_line_data,
        # Add any other fields you want to use in templates
        'priority': df.get('priority', ''),
        'score': df.get('score', 0),
    })
    
    # Add domain for tracking
    instantly_df['domain'] = df['domain']
    
    # Clean up any NaN values
    instantly_df = instantly_df.fillna('')
    
    # Stats
    log_step("Sequence build complete")
    log_success(f"Ready to upload {len(instantly_df)} leads to Instantly")
    
    # Priority breakdown
    if 'priority' in instantly_df.columns:
        priority_counts = instantly_df['priority'].value_counts()
        for priority, count in priority_counts.items():
            if priority:
                print(f"  - {priority}: {count}")
    
    # Save output
    if output_file is None:
        output_file = "instantly_upload.csv"
    
    output_path = FINAL_DIR / output_file
    save_csv(instantly_df, str(output_path))
    
    # Also save the templates as reference
    templates_path = FINAL_DIR / "email_templates.txt"
    with open(templates_path, 'w') as f:
        f.write("EMAIL SEQUENCE TEMPLATES\n")
        f.write("=" * 50 + "\n\n")
        for name, template in EMAIL_TEMPLATES.items():
            f.write(f"{name.upper()}\n")
            f.write(f"Subject: {template['subject']}\n")
            f.write(f"Send after: Day {template['delay_days']}\n")
            f.write("-" * 30 + "\n")
            f.write(template['body'])
            f.write("\n\n" + "=" * 50 + "\n\n")
    
    log_success(f"Templates saved to {templates_path}")
    
    return instantly_df


def preview_email(row: pd.Series, template_key: str = 'email_1') -> str:
    """
    Preview what an email will look like for a specific lead.
    """
    
    template = EMAIL_TEMPLATES[template_key]
    
    subject = template['subject']
    body = template['body']
    
    # Replace variables
    replacements = {
        '{{company_name}}': str(row.get('company_name', '')),
        '{{website}}': str(row.get('website', '')),
        '{{first_line}}': str(row.get('first_line', '')),
        '{{domain}}': str(row.get('domain', '')),
    }
    
    for var, value in replacements.items():
        subject = subject.replace(var, value)
        body = body.replace(var, value)
    
    return f"TO: {row.get('email')}\nSUBJECT: {subject}\n\n{body}"


def main():
    """Run sequence builder from command line."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Build email sequences for Instantly')
    parser.add_argument('input_file', help='Input CSV filename (in data/final/)')
    parser.add_argument('output_file', nargs='?', help='Output CSV filename (in data/final/)')
    parser.add_argument('--preview', type=int, default=0, help='Preview N emails')
    
    args = parser.parse_args()
    
    df = build_sequence(args.input_file, args.output_file)
    
    if args.preview > 0 and not df.empty:
        log_step(f"Preview of first {args.preview} emails:")
        for idx, row in df.head(args.preview).iterrows():
            print("\n" + "=" * 50)
            print(preview_email(row))


if __name__ == "__main__":
    main()