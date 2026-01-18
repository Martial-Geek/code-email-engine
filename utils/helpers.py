"""
Shared utility functions used across all modules.
"""

import re
import tldextract
from urllib.parse import urlparse
from typing import Optional
import pandas as pd
from rich.console import Console

console = Console()


def normalize_url(url: str) -> Optional[str]:
    """
    Clean and normalize a URL to consistent format.
    Returns None if URL is invalid.
    """
    if not url or not isinstance(url, str):
        return None
    
    url = url.strip().lower()
    
    # Remove common garbage
    url = re.sub(r'\s+', '', url)
    
    # Add scheme if missing
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    # Remove trailing slashes and paths for domain comparison
    try:
        parsed = urlparse(url)
        if not parsed.netloc:
            return None
        return f"{parsed.scheme}://{parsed.netloc}"
    except Exception:
        return None


def extract_domain(url: str) -> Optional[str]:
    """
    Extract clean domain from URL.
    Example: 'https://www.example.com/page' -> 'example.com'
    """
    if not url:
        return None
    
    try:
        extracted = tldextract.extract(url)
        if extracted.domain and extracted.suffix:
            return f"{extracted.domain}.{extracted.suffix}"
        return None
    except Exception:
        return None


def extract_root_domain(url: str) -> Optional[str]:
    """
    Extract just the domain name without TLD.
    Example: 'https://acme-corp.com' -> 'acme-corp'
    """
    if not url:
        return None
    
    try:
        extracted = tldextract.extract(url)
        return extracted.domain if extracted.domain else None
    except Exception:
        return None


def is_valid_business_domain(domain: str) -> bool:
    """
    Check if domain looks like a real business website.
    Filters out social media, email providers, etc.
    """
    if not domain:
        return False
    
    excluded = [
        'facebook.com', 'twitter.com', 'instagram.com', 'linkedin.com',
        'youtube.com', 'tiktok.com', 'pinterest.com',
        'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
        'google.com', 'yelp.com', 'yellowpages.com',
        'wix.com', 'squarespace.com', 'wordpress.com', 'weebly.com',
        'godaddy.com', 'namecheap.com'
    ]
    
    domain_lower = domain.lower()
    return not any(exc in domain_lower for exc in excluded)


def clean_company_name(name: str) -> Optional[str]:
    """
    Clean company name for use in emails.
    """
    if not name or not isinstance(name, str):
        return None
    
    name = name.strip()
    
    # Remove common suffixes
    suffixes = [' LLC', ' Inc', ' Inc.', ' Ltd', ' Ltd.', ' Corp', ' Corp.']
    for suffix in suffixes:
        if name.endswith(suffix):
            name = name[:-len(suffix)]
    
    return name.strip() if name else None


def load_csv_safe(filepath: str) -> pd.DataFrame:
    """
    Load CSV with error handling.
    """
    try:
        df = pd.read_csv(filepath, encoding='utf-8')
        console.print(f"[green]Loaded {len(df)} rows from {filepath}[/green]")
        return df
    except UnicodeDecodeError:
        df = pd.read_csv(filepath, encoding='latin-1')
        console.print(f"[yellow]Loaded {len(df)} rows (latin-1 encoding)[/yellow]")
        return df
    except Exception as e:
        console.print(f"[red]Error loading {filepath}: {e}[/red]")
        return pd.DataFrame()


def save_csv(df: pd.DataFrame, filepath: str) -> None:
    """
    Save DataFrame to CSV.
    """
    df.to_csv(filepath, index=False, encoding='utf-8')
    console.print(f"[green]Saved {len(df)} rows to {filepath}[/green]")


def log_step(message: str) -> None:
    """
    Print a formatted step message.
    """
    console.print(f"\n[bold blue]>>> {message}[/bold blue]")


def log_success(message: str) -> None:
    """
    Print success message.
    """
    console.print(f"[green]✓ {message}[/green]")


def log_warning(message: str) -> None:
    """
    Print warning message.
    """
    console.print(f"[yellow]⚠ {message}[/yellow]")


def log_error(message: str) -> None:
    """
    Print error message.
    """
    console.print(f"[red]✗ {message}[/red]")