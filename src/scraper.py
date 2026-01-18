"""
Step 3: Website Intelligence Scraper
Analyzes each website for technical details and issues.
"""

import asyncio
import httpx
from bs4 import BeautifulSoup
from dataclasses import dataclass, asdict
from typing import Optional, List
import json
import time
from pathlib import Path
import pandas as pd
import sys
import re

sys.path.append(str(Path(__file__).parent.parent))

from config.settings import (
    CLEANED_DIR, ENRICHED_DIR, REQUEST_TIMEOUT, 
    MAX_CONCURRENT_REQUESTS, USER_AGENT, OLD_CMS_MARKERS
)
from utils.helpers import (
    load_csv_safe, save_csv, log_step, log_success, 
    log_warning, log_error
)
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn


@dataclass
class WebsiteIntelligence:
    """Data structure for website analysis results."""
    domain: str
    has_ssl: bool = False
    load_time: float = 0.0
    status_code: int = 0
    title: Optional[str] = None
    meta_description: Optional[str] = None
    has_contact_page: bool = False
    cms_detected: Optional[str] = None
    is_mobile_friendly: bool = True  # Default assumption
    technologies: List[str] = None
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.technologies is None:
            self.technologies = []


class WebsiteScraper:
    """Async website analyzer."""
    
    def __init__(self, max_concurrent: int = MAX_CONCURRENT_REQUESTS):
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.headers = {
            'User-Agent': USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
    
    async def analyze_website(self, domain: str, client: httpx.AsyncClient) -> WebsiteIntelligence:
        """Analyze a single website."""
        
        intel = WebsiteIntelligence(domain=domain)
        
        async with self.semaphore:
            # Try HTTPS first
            urls_to_try = [f"https://{domain}", f"http://{domain}"]
            
            for url in urls_to_try:
                try:
                    start_time = time.time()
                    response = await client.get(
                        url, 
                        follow_redirects=True,
                        timeout=REQUEST_TIMEOUT
                    )
                    intel.load_time = round(time.time() - start_time, 2)
                    intel.status_code = response.status_code
                    intel.has_ssl = str(response.url).startswith('https')
                    
                    if response.status_code == 200:
                        await self._parse_html(response.text, intel)
                        await self._check_contact_page(domain, client, intel)
                        break
                        
                except httpx.TimeoutException:
                    intel.error = "timeout"
                except httpx.ConnectError:
                    intel.error = "connection_failed"
                except Exception as e:
                    intel.error = str(e)[:100]
        
        return intel
    
    async def _parse_html(self, html: str, intel: WebsiteIntelligence) -> None:
        """Extract information from HTML."""
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Title
            title_tag = soup.find('title')
            if title_tag:
                intel.title = title_tag.get_text(strip=True)[:200]
            
            # Meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                intel.meta_description = meta_desc.get('content', '')[:300]
            
            # Viewport (mobile friendly indicator)
            viewport = soup.find('meta', attrs={'name': 'viewport'})
            intel.is_mobile_friendly = viewport is not None
            
            # CMS Detection
            intel.cms_detected = self._detect_cms(html, soup)
            
            # Technology detection
            intel.technologies = self._detect_technologies(html, soup)
            
        except Exception:
            pass
    
    def _detect_cms(self, html: str, soup: BeautifulSoup) -> Optional[str]:
        """Detect CMS from HTML patterns."""
        
        html_lower = html.lower()
        
        # WordPress
        if 'wp-content' in html_lower or 'wordpress' in html_lower:
            # Try to find version
            version_match = re.search(r'wordpress\s*([\d.]+)', html_lower)
            if version_match:
                return f"wordpress {version_match.group(1)}"
            return "wordpress"
        
        # Wix
        if 'wix.com' in html_lower or '_wix' in html_lower:
            return "wix"
        
        # Squarespace
        if 'squarespace' in html_lower:
            return "squarespace"
        
        # Shopify
        if 'shopify' in html_lower or 'cdn.shopify' in html_lower:
            return "shopify"
        
        # Webflow
        if 'webflow' in html_lower:
            return "webflow"
        
        # Joomla
        if '/joomla' in html_lower or 'joomla' in html_lower:
            return "joomla"
        
        # Drupal
        if 'drupal' in html_lower:
            return "drupal"
        
        return None
    
    def _detect_technologies(self, html: str, soup: BeautifulSoup) -> List[str]:
        """Detect technologies used."""
        
        techs = []
        html_lower = html.lower()
        
        # JavaScript frameworks
        if 'react' in html_lower or 'reactdom' in html_lower:
            techs.append('react')
        if 'vue' in html_lower or 'vuejs' in html_lower:
            techs.append('vue')
        if 'angular' in html_lower:
            techs.append('angular')
        if 'jquery' in html_lower:
            techs.append('jquery')
        
        # Analytics
        if 'google-analytics' in html_lower or 'gtag' in html_lower or 'ga.js' in html_lower:
            techs.append('google_analytics')
        if 'facebook.com/tr' in html_lower or 'fbevents' in html_lower:
            techs.append('facebook_pixel')
        
        # Other
        if 'bootstrap' in html_lower:
            techs.append('bootstrap')
        if 'tailwind' in html_lower:
            techs.append('tailwind')
        
        return techs
    
    async def _check_contact_page(self, domain: str, client: httpx.AsyncClient, intel: WebsiteIntelligence) -> None:
        """Check if contact page exists."""
        
        contact_paths = ['/contact', '/contact-us', '/kontakt', '/contacto', '/about/contact']
        
        for path in contact_paths:
            try:
                url = f"https://{domain}{path}"
                response = await client.head(url, follow_redirects=True, timeout=5)
                if response.status_code == 200:
                    intel.has_contact_page = True
                    return
            except Exception:
                continue
    
    async def analyze_batch(self, domains: List[str]) -> List[WebsiteIntelligence]:
        """Analyze multiple websites concurrently."""
        
        results = []
        
        async with httpx.AsyncClient(headers=self.headers) as client:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            ) as progress:
                
                task = progress.add_task("Scraping websites...", total=len(domains))
                
                # Process in batches to avoid overwhelming
                batch_size = self.max_concurrent * 2
                
                for i in range(0, len(domains), batch_size):
                    batch = domains[i:i + batch_size]
                    tasks = [self.analyze_website(domain, client) for domain in batch]
                    batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    for result in batch_results:
                        if isinstance(result, WebsiteIntelligence):
                            results.append(result)
                        else:
                            # Handle exception
                            pass
                    
                    progress.update(task, advance=len(batch))
        
        return results


def scrape_websites(input_file: str, output_file: Optional[str] = None) -> pd.DataFrame:
    """
    Main function to scrape websites from cleaned lead file.
    """
    
    log_step("Starting website intelligence scraping")
    
    # Load cleaned leads
    input_path = CLEANED_DIR / input_file
    df = load_csv_safe(str(input_path))
    
    if df.empty or 'domain' not in df.columns:
        log_error("No valid data to process")
        return pd.DataFrame()
    
    domains = df['domain'].tolist()
    log_success(f"Found {len(domains)} domains to analyze")
    
    # Run async scraper
    scraper = WebsiteScraper()
    results = asyncio.run(scraper.analyze_batch(domains))
    
    # Convert to DataFrame
    results_df = pd.DataFrame([asdict(r) for r in results])
    
    # Merge with original data
    merged_df = df.merge(results_df, on='domain', how='left')
    
    # Stats
    successful = len(results_df[results_df['error'].isna()])
    with_ssl = len(results_df[results_df['has_ssl'] == True])
    slow_sites = len(results_df[results_df['load_time'] > 3])
    
    log_step("Scraping complete")
    log_success(f"Successfully analyzed: {successful}/{len(domains)}")
    log_success(f"Sites with SSL: {with_ssl}")
    log_warning(f"Slow sites (>3s): {slow_sites}")
    
    # Save output
    if output_file is None:
        output_file = input_file.replace('_cleaned.csv', '_enriched.csv').replace('.csv', '_enriched.csv')
    
    output_path = ENRICHED_DIR / output_file
    save_csv(merged_df, str(output_path))
    
    return merged_df


def main():
    """Run scraper from command line."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Scrape website intelligence')
    parser.add_argument('input_file', help='Input CSV filename (in data/cleaned/)')
    parser.add_argument('output_file', nargs='?', help='Output CSV filename (in data/enriched/)')
    
    args = parser.parse_args()
    scrape_websites(args.input_file, args.output_file)


if __name__ == "__main__":
    main()