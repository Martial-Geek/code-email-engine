"""
Master pipeline script.
Runs all steps in sequence.
"""

import argparse
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from src.cleaner import clean_leads
from src.scraper import scrape_websites
from src.scorer import score_leads
from src.email_guesser import guess_emails
from src.personalizer import personalize_leads
from src.sequence_builder import build_sequence
from utils.helpers import log_step, log_success, log_error
from config.settings import EMAILS_DIR
from rich.console import Console

console = Console()


def run_full_pipeline(input_file: str, skip_ai: bool = False):
    """
    Run the complete pipeline from raw data to Instantly-ready CSV.
    
    Args:
        input_file: Raw CSV file in data/raw/
        skip_ai: Skip AI personalization (useful for testing)
    """
    
    console.print("\n[bold magenta]" + "=" * 60 + "[/bold magenta]")
    console.print("[bold magenta]   COLD EMAIL ENGINE - FULL PIPELINE   [/bold magenta]")
    console.print("[bold magenta]" + "=" * 60 + "[/bold magenta]\n")
    
    try:
        # Step 1: Clean leads
        log_step("STEP 1/6: Cleaning leads")
        cleaned_file = input_file.replace('.csv', '_cleaned.csv')
        clean_leads(input_file, cleaned_file)
        
        # Step 2: Scrape websites
        log_step("STEP 2/6: Scraping website intelligence")
        enriched_file = cleaned_file.replace('_cleaned.csv', '_enriched.csv')
        scrape_websites(cleaned_file, enriched_file)
        
        # Step 3: Score leads
        log_step("STEP 3/6: Scoring leads")
        scored_file = enriched_file.replace('_enriched.csv', '_scored.csv')
        score_leads(enriched_file, scored_file)
        
        # Step 4: Generate email guesses
        log_step("STEP 4/6: Generating email addresses")
        # Email files are saved in EMAILS_DIR, not in the same directory as scored file
        emails_filename = Path(input_file).stem + '_emails_best.csv'
        emails_file = str(EMAILS_DIR / emails_filename)
        guess_emails(scored_file)
        
        # Step 5: AI Personalization
        if not skip_ai:
            log_step("STEP 5/6: AI personalization")
            personalized_file = emails_file.replace('_best.csv', '_personalized.csv')
            personalize_leads(emails_file, personalized_file)
            final_input = personalized_file
        else:
            log_step("STEP 5/6: Skipping AI personalization")
            # Create placeholder first lines
            final_input = emails_file
        
        # Step 6: Build sequence
        log_step("STEP 6/6: Building email sequence")
        build_sequence(final_input if not skip_ai else emails_file)
        
        console.print("\n[bold green]" + "=" * 60 + "[/bold green]")
        console.print("[bold green]   PIPELINE COMPLETE   [/bold green]")
        console.print("[bold green]" + "=" * 60 + "[/bold green]")
        console.print("\n[green]Your Instantly-ready CSV is at: data/final/instantly_upload.csv[/green]")
        console.print("[green]Email templates are at: data/final/email_templates.txt[/green]\n")
        
    except Exception as e:
        log_error(f"Pipeline failed: {e}")
        raise


def run_single_step(step: str, input_file: str, output_file: str = None):
    """Run a single step of the pipeline."""
    
    steps = {
        'clean': clean_leads,
        'scrape': scrape_websites,
        'score': score_leads,
        'emails': guess_emails,
        'personalize': personalize_leads,
        'sequence': build_sequence,
    }
    
    if step not in steps:
        log_error(f"Unknown step: {step}. Available: {list(steps.keys())}")
        return
    
    steps[step](input_file, output_file)


def main():
    parser = argparse.ArgumentParser(
        description='Cold Email Engine Pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full pipeline
  python run_pipeline.py leads.csv
  
  # Run full pipeline without AI (for testing)
  python run_pipeline.py leads.csv --skip-ai
  
  # Run single step
  python run_pipeline.py --step clean leads.csv
  python run_pipeline.py --step scrape leads_cleaned.csv
  python run_pipeline.py --step score leads_enriched.csv
  python run_pipeline.py --step emails leads_scored.csv
  python run_pipeline.py --step personalize leads_emails_best.csv
  python run_pipeline.py --step sequence leads_personalized.csv
        """
    )
    
    parser.add_argument('input_file', help='Input CSV filename')
    parser.add_argument('--step', choices=['clean', 'scrape', 'score', 'emails', 'personalize', 'sequence'],
                        help='Run single step instead of full pipeline')
    parser.add_argument('--output', help='Output filename (for single step)')
    parser.add_argument('--skip-ai', action='store_true', help='Skip AI personalization')
    
    args = parser.parse_args()
    
    if args.step:
        run_single_step(args.step, args.input_file, args.output)
    else:
        run_full_pipeline(args.input_file, args.skip_ai)


if __name__ == "__main__":
    main()