"""
Main entry point for the website intelligence scraper.

This module provides the main scrape_websites function that integrates
with the existing pipeline, as well as standalone functionality.
"""

import asyncio
import argparse
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

import pandas as pd

# Add parent paths for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from .base_scraper import RobustWebsiteScraper
from .models.website_intelligence import WebsiteIntelligence
from .exporters.csv_exporter import CSVExporter
from .exporters.pdf_exporter import PDFExporter

# Try to import project-specific modules
try:
    from config.settings import CLEANED_DIR, ENRICHED_DIR
    from utils.helpers import load_csv_safe, save_csv, log_step, log_success, log_warning, log_error
    HAS_PROJECT_UTILS = True
except ImportError:
    HAS_PROJECT_UTILS = False
    CLEANED_DIR = Path("data/cleaned")
    ENRICHED_DIR = Path("data/enriched")


# =============================================================================
# LOGGING UTILITIES
# =============================================================================

def _log_step(message: str) -> None:
    """Log a step message."""
    if HAS_PROJECT_UTILS:
        log_step(message)
    else:
        print(f"[STEP] {message}")


def _log_success(message: str) -> None:
    """Log a success message."""
    if HAS_PROJECT_UTILS:
        log_success(message)
    else:
        print(f"[SUCCESS] {message}")


def _log_warning(message: str) -> None:
    """Log a warning message."""
    if HAS_PROJECT_UTILS:
        log_warning(message)
    else:
        print(f"[WARNING] {message}")


def _log_error(message: str) -> None:
    """Log an error message."""
    if HAS_PROJECT_UTILS:
        log_error(message)
    else:
        print(f"[ERROR] {message}")


def _load_csv(filepath: str) -> pd.DataFrame:
    """Load CSV file."""
    if HAS_PROJECT_UTILS:
        return load_csv_safe(filepath)
    else:
        try:
            return pd.read_csv(filepath)
        except Exception as e:
            _log_error(f"Failed to load CSV: {e}")
            return pd.DataFrame()


def _save_csv(df: pd.DataFrame, filepath: str) -> None:
    """Save DataFrame to CSV."""
    if HAS_PROJECT_UTILS:
        save_csv(df, filepath)
    else:
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(filepath, index=False)
        _log_success(f"Saved to {filepath}")


# =============================================================================
# COMPATIBILITY FUNCTIONS
# =============================================================================

def flatten_intelligence(intel: WebsiteIntelligence) -> Dict[str, Any]:
    """
    Flatten nested dataclass to flat dictionary for CSV export.
    
    This function is kept for backward compatibility with existing code.
    
    Args:
        intel: WebsiteIntelligence object
        
    Returns:
        Flat dictionary suitable for CSV export
    """
    return intel.to_flat_dict()


# =============================================================================
# MAIN PIPELINE FUNCTION
# =============================================================================

def scrape_websites(
    input_file: str, 
    output_file: Optional[str] = None,
    measurement_rounds: int = 3,
    generate_reports: bool = False,
    report_type: str = 'full'
) -> pd.DataFrame:
    """
    Main function to scrape websites from cleaned lead file.
    
    This function maintains backward compatibility with the existing pipeline
    (run_pipeline.py) while providing enhanced functionality.
    
    Args:
        input_file: Input CSV filename in data/cleaned/
        output_file: Output CSV filename in data/enriched/
        measurement_rounds: Number of load time measurements per site
        generate_reports: Whether to generate PDF reports
        report_type: Type of report to generate ('full', 'seo', 'performance', 'security')
        
    Returns:
        DataFrame with enriched website data
    """
    _log_step("Starting comprehensive website intelligence scraping")
    
    # Determine input path
    input_path = CLEANED_DIR / input_file
    if not input_path.exists():
        # Try as absolute path
        input_path = Path(input_file)
    
    if not input_path.exists():
        _log_error(f"Input file not found: {input_path}")
        return pd.DataFrame()
    
    # Load cleaned leads
    df = _load_csv(str(input_path))
    
    if df.empty:
        _log_error("Input file is empty")
        return pd.DataFrame()
    
    if 'domain' not in df.columns:
        _log_error("No 'domain' column found in input file")
        return pd.DataFrame()
    
    # Get unique domains
    domains = df['domain'].dropna().unique().tolist()
    
    if not domains:
        _log_error("No valid domains found in input file")
        return pd.DataFrame()
    
    _log_success(f"Found {len(domains)} unique domains to analyze")
    _log_step(f"Using {measurement_rounds} measurement rounds for load time statistics")
    
    # Run async scraper
    scraper = RobustWebsiteScraper(measurement_rounds=measurement_rounds)
    results = asyncio.run(scraper.analyze_batch(domains))
    
    # Convert to flat DataFrame
    results_data = [flatten_intelligence(r) for r in results]
    results_df = pd.DataFrame(results_data)
    
    # Merge with original data
    merged_df = df.merge(results_df, on='domain', how='left')
    
    # Calculate and display statistics
    _display_statistics(results_df, domains)
    
    # Generate reports if requested
    if generate_reports:
        _generate_reports(results, report_type)
    
    # Determine output path
    if output_file is None:
        output_file = input_file.replace('_cleaned.csv', '_enriched.csv')
        if output_file == input_file:
            output_file = input_file.replace('.csv', '_enriched.csv')
    
    output_path = ENRICHED_DIR / output_file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    _save_csv(merged_df, str(output_path))
    
    return merged_df


# =============================================================================
# STATISTICS AND REPORTING
# =============================================================================

def _display_statistics(results_df: pd.DataFrame, domains: List[str]) -> None:
    """Display analysis statistics."""
    total = len(domains)
    successful = len(results_df[results_df['error'].isna()])
    failed = total - successful
    
    # SSL statistics
    with_ssl = len(results_df[results_df['has_ssl'] == True])
    
    # Priority leads
    high_priority = len(results_df[results_df['buyer_priority_score'] >= 50])
    
    # CMS statistics
    outdated_cms = len(results_df[results_df['is_outdated_cms'] == True])
    
    # Load time statistics
    valid_load_times = results_df[results_df['load_time_median'] > 0]['load_time_median']
    if len(valid_load_times) > 0:
        avg_load_time = valid_load_times.mean()
        median_load_time = valid_load_times.median()
    else:
        avg_load_time = median_load_time = 0
    
    # Score statistics
    if 'overall_score' in results_df.columns:
        valid_scores = results_df[results_df['overall_score'] > 0]['overall_score']
        avg_overall = valid_scores.mean() if len(valid_scores) > 0 else 0
        avg_seo = results_df['seo_score'].mean() if 'seo_score' in results_df.columns else 0
        avg_security = results_df['security_score'].mean() if 'security_score' in results_df.columns else 0
    else:
        avg_overall = avg_seo = avg_security = 0
    
    # Display results
    _log_step("=" * 50)
    _log_step("SCRAPING COMPLETE - SUMMARY")
    _log_step("=" * 50)
    
    _log_success(f"Total domains: {total}")
    _log_success(f"Successfully analyzed: {successful} ({successful/total*100:.1f}%)")
    
    if failed > 0:
        _log_warning(f"Failed: {failed} ({failed/total*100:.1f}%)")
    
    _log_step("-" * 50)
    _log_success(f"Sites with SSL: {with_ssl} ({with_ssl/successful*100:.1f}%)" if successful > 0 else "Sites with SSL: 0")
    _log_success(f"High priority leads (score >= 50): {high_priority}")
    
    if outdated_cms > 0:
        _log_warning(f"Outdated CMS detected: {outdated_cms}")
    
    _log_step("-" * 50)
    _log_step(f"Load times - Mean: {avg_load_time:.2f}s, Median: {median_load_time:.2f}s")
    _log_step(f"Average scores - Overall: {avg_overall:.1f}, SEO: {avg_seo:.1f}, Security: {avg_security:.1f}")
    _log_step("=" * 50)


def _generate_reports(
    results: List[WebsiteIntelligence], 
    report_type: str = 'full'
) -> None:
    """
    Generate PDF reports for analyzed websites.
    
    Args:
        results: List of WebsiteIntelligence objects
        report_type: Type of report to generate
    """
    _log_step(f"Generating {report_type} PDF reports...")
    
    # Import report generators
    from .reports.full_report import FullReport
    from .reports.seo_report import SEOReport
    from .reports.performance_report import PerformanceReport
    from .reports.security_report import SecurityReport
    
    # Select report generator
    report_generators = {
        'full': FullReport,
        'seo': SEOReport,
        'performance': PerformanceReport,
        'security': SecurityReport,
    }
    
    if report_type not in report_generators:
        _log_warning(f"Unknown report type '{report_type}', using 'full'")
        report_type = 'full'
    
    report_generator = report_generators[report_type]()
    generated_count = 0
    failed_count = 0
    
    for intel in results:
        if intel.error is None:
            try:
                report_path = report_generator.generate(intel)
                generated_count += 1
            except Exception as e:
                _log_warning(f"Failed to generate report for {intel.domain}: {e}")
                failed_count += 1
    
    _log_success(f"Generated {generated_count} PDF reports")
    if failed_count > 0:
        _log_warning(f"Failed to generate {failed_count} reports")


# =============================================================================
# SINGLE WEBSITE ANALYSIS
# =============================================================================

def analyze_single_website(
    domain: str,
    measurement_rounds: int = 3,
    generate_report: bool = False,
    report_type: str = 'full',
    output_dir: Optional[str] = None
) -> WebsiteIntelligence:
    """
    Analyze a single website.
    
    This is a convenience function for analyzing individual domains
    outside of the batch pipeline.
    
    Args:
        domain: Domain to analyze (e.g., 'example.com')
        measurement_rounds: Number of load time measurements
        generate_report: Whether to generate a PDF report
        report_type: Type of report ('full', 'seo', 'performance', 'security')
        output_dir: Directory for reports (optional)
        
    Returns:
        WebsiteIntelligence object with analysis results
    """
    _log_step(f"Analyzing {domain}...")
    
    # Clean domain
    domain = domain.strip().lower()
    domain = domain.replace('https://', '').replace('http://', '')
    domain = domain.rstrip('/')
    
    # Run analysis
    scraper = RobustWebsiteScraper(measurement_rounds=measurement_rounds)
    intel = scraper.analyze_single_sync(domain)
    
    _log_success(f"Analysis complete for {domain}")
    _log_step(f"Overall score: {intel.overall_score}/100")
    _log_step(f"Buyer priority score: {intel.buyer_priority_score}")
    
    # Generate report if requested
    if generate_report:
        _generate_single_report(intel, report_type, output_dir)
    
    return intel


def _generate_single_report(
    intel: WebsiteIntelligence,
    report_type: str = 'full',
    output_dir: Optional[str] = None
) -> Optional[Path]:
    """
    Generate a report for a single website.
    
    Args:
        intel: WebsiteIntelligence object
        report_type: Type of report to generate
        output_dir: Output directory for the report
        
    Returns:
        Path to generated report, or None if failed
    """
    from .reports.full_report import FullReport
    from .reports.seo_report import SEOReport
    from .reports.performance_report import PerformanceReport
    from .reports.security_report import SecurityReport
    
    report_generators = {
        'full': FullReport,
        'seo': SEOReport,
        'performance': PerformanceReport,
        'security': SecurityReport,
    }
    
    if report_type not in report_generators:
        _log_warning(f"Unknown report type '{report_type}', using 'full'")
        report_type = 'full'
    
    try:
        output_path = Path(output_dir) if output_dir else None
        generator = report_generators[report_type](output_path)
        report_path = generator.generate(intel)
        _log_success(f"Report generated: {report_path}")
        return report_path
    except Exception as e:
        _log_error(f"Failed to generate report: {e}")
        return None


# =============================================================================
# BATCH ANALYSIS (STANDALONE)
# =============================================================================

def analyze_domains(
    domains: List[str],
    measurement_rounds: int = 3,
    output_csv: Optional[str] = None,
    generate_reports: bool = False,
    report_type: str = 'full'
) -> List[WebsiteIntelligence]:
    """
    Analyze a list of domains directly (without reading from file).
    
    This is useful for programmatic usage where domains are already in memory.
    
    Args:
        domains: List of domain strings
        measurement_rounds: Number of load time measurements per site
        output_csv: Optional path to save results as CSV
        generate_reports: Whether to generate PDF reports
        report_type: Type of reports to generate
        
    Returns:
        List of WebsiteIntelligence objects
    """
    if not domains:
        _log_error("No domains provided")
        return []
    
    # Clean domains
    clean_domains = []
    for domain in domains:
        domain = domain.strip().lower()
        domain = domain.replace('https://', '').replace('http://', '')
        domain = domain.rstrip('/')
        if domain:
            clean_domains.append(domain)
    
    clean_domains = list(set(clean_domains))  # Remove duplicates
    
    _log_step(f"Analyzing {len(clean_domains)} domains...")
    
    # Run analysis
    scraper = RobustWebsiteScraper(measurement_rounds=measurement_rounds)
    results = asyncio.run(scraper.analyze_batch(clean_domains))
    
    # Display statistics
    results_df = pd.DataFrame([flatten_intelligence(r) for r in results])
    _display_statistics(results_df, clean_domains)
    
    # Save CSV if requested
    if output_csv:
        exporter = CSVExporter()
        output_path = exporter.export(results, output_csv)
        _log_success(f"Results saved to {output_path}")
    
    # Generate reports if requested
    if generate_reports:
        _generate_reports(results, report_type)
    
    return results


# =============================================================================
# TEXT REPORT OUTPUT
# =============================================================================

def print_website_report(intel: WebsiteIntelligence) -> None:
    """
    Print a text report for a website to console.
    
    Args:
        intel: WebsiteIntelligence object
    """
    print("\n" + "=" * 60)
    print(f"WEBSITE ANALYSIS: {intel.domain}")
    print("=" * 60)
    
    print(f"\nStatus: {'Online' if intel.status_code == 200 else f'Error ({intel.status_code})'}")
    print(f"Final URL: {intel.final_url or 'N/A'}")
    print(f"Analyzed: {intel.analysis_timestamp}")
    
    if intel.error:
        print(f"\nError: {intel.error}")
    
    print("\n" + "-" * 40)
    print("SCORES")
    print("-" * 40)
    print(f"Overall Score: {intel.overall_score}/100")
    print(f"Buyer Priority: {intel.buyer_priority_score}")
    print(f"Lead Quality: {intel.business.get_lead_quality()}")
    
    print("\n" + "-" * 40)
    print("COMPONENT SCORES")
    print("-" * 40)
    print(f"Performance: {intel.performance.performance_grade} ({intel.performance.get_numeric_score()}/100)")
    print(f"SEO: {intel.seo.seo_score}/100")
    print(f"Security: {intel.security.security_headers_score}/100")
    print(f"Accessibility: {intel.accessibility.accessibility_score}/100")
    print(f"Business: {intel.business.business_legitimacy_score}/100")
    
    print("\n" + "-" * 40)
    print("TECHNOLOGY")
    print("-" * 40)
    print(f"CMS: {intel.cms_detected or 'Not detected'}", end="")
    if intel.cms_version:
        print(f" v{intel.cms_version}", end="")
    if intel.is_outdated_cms:
        print(" (OUTDATED)", end="")
    print()
    print(f"SSL: {'Yes' if intel.security.has_ssl else 'No'}")
    print(f"Mobile Friendly: {'Yes' if intel.is_mobile_friendly else 'No'}")
    if intel.technologies:
        print(f"Technologies: {', '.join(intel.technologies[:5])}")
    
    print("\n" + "-" * 40)
    print("PERFORMANCE")
    print("-" * 40)
    load_time = intel.performance.load_time_metrics
    if load_time.samples:
        print(f"Load Time (median): {load_time.median:.3f}s")
        print(f"Load Time (90th %): {load_time.percentile_90:.3f}s")
        print(f"HTML Size: {intel.performance.html_size_bytes/1024:.1f} KB")
    else:
        print("No performance data available")
    
    # Issues summary
    all_issues = intel.get_all_issues()
    total_issues = sum(len(issues) for issues in all_issues.values())
    
    if total_issues > 0:
        print("\n" + "-" * 40)
        print(f"ISSUES ({total_issues} total)")
        print("-" * 40)
        for category, issues in all_issues.items():
            if issues:
                print(f"\n{category.upper()}:")
                for issue in issues[:3]:  # Show max 3 per category
                    print(f"  • {issue}")
                if len(issues) > 3:
                    print(f"  ... and {len(issues) - 3} more")
    
    print("\n" + "=" * 60 + "\n")


# =============================================================================
# COMMAND LINE INTERFACE
# =============================================================================

def main():
    """Main entry point for command line usage."""
    parser = argparse.ArgumentParser(
        description='Website Intelligence Scraper - Comprehensive website analysis tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze websites from a CSV file (pipeline mode)
  python -m src.scrapers.main leads_cleaned.csv
  
  # Analyze with custom output file
  python -m src.scrapers.main leads_cleaned.csv --output leads_enriched.csv
  
  # Analyze a single domain
  python -m src.scrapers.main --domain example.com
  
  # Analyze with PDF report generation
  python -m src.scrapers.main leads_cleaned.csv --reports
  
  # Analyze single domain with specific report type
  python -m src.scrapers.main --domain example.com --reports --report-type seo
  
  # Analyze multiple domains directly
  python -m src.scrapers.main --domains example.com,test.com,demo.org
  
  # Customize measurement rounds
  python -m src.scrapers.main leads_cleaned.csv --rounds 5
        """
    )
    
    # Input options (mutually exclusive)
    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument(
        'input_file',
        nargs='?',
        help='Input CSV filename (in data/cleaned/ or absolute path)'
    )
    input_group.add_argument(
        '--domain', '-d',
        help='Single domain to analyze'
    )
    input_group.add_argument(
        '--domains',
        help='Comma-separated list of domains to analyze'
    )
    
    # Output options
    parser.add_argument(
        '--output', '-o',
        help='Output CSV filename (in data/enriched/ or absolute path)'
    )
    
    # Analysis options
    parser.add_argument(
        '--rounds', '-r',
        type=int,
        default=3,
        help='Number of load time measurement rounds (default: 3)'
    )
    
    # Report options
    parser.add_argument(
        '--reports',
        action='store_true',
        help='Generate PDF reports'
    )
    parser.add_argument(
        '--report-type',
        choices=['full', 'seo', 'performance', 'security'],
        default='full',
        help='Type of PDF report to generate (default: full)'
    )
    parser.add_argument(
        '--report-dir',
        help='Directory for PDF reports'
    )
    
    # Output options
    parser.add_argument(
        '--print',
        action='store_true',
        help='Print text report to console (for single domain analysis)'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results as JSON'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.input_file and not args.domain and not args.domains:
        parser.print_help()
        print("\nError: Please provide an input file, --domain, or --domains")
        sys.exit(1)
    
    # Single domain analysis
    if args.domain:
        intel = analyze_single_website(
            domain=args.domain,
            measurement_rounds=args.rounds,
            generate_report=args.reports,
            report_type=args.report_type,
            output_dir=args.report_dir
        )
        
        if args.print:
            print_website_report(intel)
        
        if args.json:
            import json
            print(json.dumps(intel.to_flat_dict(), indent=2, default=str))
        
        return
    
    # Multiple domains from command line
    if args.domains:
        domains = [d.strip() for d in args.domains.split(',')]
        results = analyze_domains(
            domains=domains,
            measurement_rounds=args.rounds,
            output_csv=args.output,
            generate_reports=args.reports,
            report_type=args.report_type
        )
        
        if args.json:
            import json
            data = [r.to_flat_dict() for r in results]
            print(json.dumps(data, indent=2, default=str))
        
        return
    
    # File-based analysis (pipeline mode)
    if args.input_file:
        scrape_websites(
            input_file=args.input_file,
            output_file=args.output,
            measurement_rounds=args.rounds,
            generate_reports=args.reports,
            report_type=args.report_type
        )


# =============================================================================
# MODULE ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    main()