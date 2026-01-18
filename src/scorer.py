"""
Step 4: Lead Quality Scoring
Scores leads based on website issues and opportunity signals.
"""

import pandas as pd
from pathlib import Path
from typing import Dict, Any
import sys

sys.path.append(str(Path(__file__).parent.parent))

from config.settings import ENRICHED_DIR, SCORED_DIR, SCORE_WEIGHTS, OLD_CMS_MARKERS
from utils.helpers import load_csv_safe, save_csv, log_step, log_success, log_warning


def calculate_score(row: pd.Series, weights: Dict[str, int]) -> Dict[str, Any]:
    """
    Calculate opportunity score for a single lead.
    Higher score = more issues = better opportunity.
    
    Returns dict with score breakdown.
    """
    
    score = 0
    reasons = []
    
    # No SSL
    if row.get('has_ssl') == False:
        score += weights['no_ssl']
        reasons.append('no_ssl')
    
    # Slow site
    load_time = row.get('load_time', 0)
    if load_time > 5:
        score += weights['very_slow_site']
        reasons.append('very_slow')
    elif load_time > 3:
        score += weights['slow_site']
        reasons.append('slow')
    
    # No contact page
    if row.get('has_contact_page') == False:
        score += weights['no_contact_page']
        reasons.append('no_contact_page')
    
    # Old CMS
    cms = str(row.get('cms_detected', '')).lower()
    if cms and any(old in cms for old in OLD_CMS_MARKERS):
        score += weights['old_cms']
        reasons.append('old_cms')
    
    # Not mobile friendly
    if row.get('is_mobile_friendly') == False:
        score += weights['no_mobile']
        reasons.append('no_mobile')
    
    # Missing meta description
    if not row.get('meta_description'):
        score += weights['missing_meta']
        reasons.append('no_meta')
    
    return {
        'score': score,
        'reasons': ','.join(reasons) if reasons else 'none',
        'reason_count': len(reasons)
    }


def classify_priority(score: int) -> str:
    """Classify lead priority based on score."""
    if score >= 6:
        return 'hot'
    elif score >= 4:
        return 'warm'
    elif score >= 2:
        return 'cool'
    else:
        return 'cold'


def score_leads(input_file: str, output_file: str = None) -> pd.DataFrame:
    """
    Main scoring function.
    """
    
    log_step("Starting lead scoring")
    
    # Load enriched data
    input_path = ENRICHED_DIR / input_file
    df = load_csv_safe(str(input_path))
    
    if df.empty:
        return pd.DataFrame()
    
    log_success(f"Loaded {len(df)} enriched leads")
    
    # Calculate scores
    log_step("Calculating opportunity scores")
    
    score_data = df.apply(lambda row: calculate_score(row, SCORE_WEIGHTS), axis=1)
    score_df = pd.DataFrame(score_data.tolist())
    
    df['score'] = score_df['score']
    df['score_reasons'] = score_df['reasons']
    df['reason_count'] = score_df['reason_count']
    df['priority'] = df['score'].apply(classify_priority)
    
    # Sort by score descending
    df = df.sort_values('score', ascending=False)
    
    # Stats
    priority_counts = df['priority'].value_counts()
    
    log_step("Scoring complete")
    log_success(f"Hot leads (score >= 6): {priority_counts.get('hot', 0)}")
    log_success(f"Warm leads (score 4-5): {priority_counts.get('warm', 0)}")
    log_warning(f"Cool leads (score 2-3): {priority_counts.get('cool', 0)}")
    log_warning(f"Cold leads (score 0-1): {priority_counts.get('cold', 0)}")
    
    # Average score
    avg_score = df['score'].mean()
    log_success(f"Average score: {avg_score:.2f}")
    
    # Most common issues
    all_reasons = ','.join(df['score_reasons'].fillna('')).split(',')
    reason_counts = pd.Series(all_reasons).value_counts()
    log_step("Most common issues:")
    for reason, count in reason_counts.head(5).items():
        if reason and reason != 'none':
            print(f"  - {reason}: {count}")
    
    # Save output
    if output_file is None:
        output_file = input_file.replace('_enriched.csv', '_scored.csv').replace('.csv', '_scored.csv')
    
    output_path = SCORED_DIR / output_file
    save_csv(df, str(output_path))
    
    return df


def main():
    """Run scorer from command line."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Score leads by opportunity')
    parser.add_argument('input_file', help='Input CSV filename (in data/enriched/)')
    parser.add_argument('output_file', nargs='?', help='Output CSV filename (in data/scored/)')
    
    args = parser.parse_args()
    score_leads(args.input_file, args.output_file)


if __name__ == "__main__":
    main()