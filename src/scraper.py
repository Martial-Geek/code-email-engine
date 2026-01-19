"""
Enhanced Website Intelligence Scraper with Statistical Robustness
"""

import asyncio
import httpx
from bs4 import BeautifulSoup
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
import json
import time
from pathlib import Path
import pandas as pd
import sys
import re
import statistics
from collections import defaultdict
import numpy as np

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
class LoadTimeMetrics:
    """Statistical metrics for load time measurements."""
    samples: List[float] = field(default_factory=list)
    median: float = 0.0
    trimmed_mean: float = 0.0  # Mean after removing outliers
    percentile_90: float = 0.0
    percentile_95: float = 0.0
    std_dev: float = 0.0
    iqr: float = 0.0  # Interquartile range
    coefficient_of_variation: float = 0.0  # CV = std_dev / mean
    confidence_score: float = 0.0  # How reliable is this measurement?
    
    def calculate(self) -> None:
        """Calculate all statistical metrics from samples."""
        if len(self.samples) < 2:
            if self.samples:
                self.median = self.samples[0]
                self.trimmed_mean = self.samples[0]
            return
        
        sorted_samples = sorted(self.samples)
        n = len(sorted_samples)
        
        # Median (robust to outliers)
        self.median = statistics.median(sorted_samples)
        
        # Percentiles
        self.percentile_90 = np.percentile(sorted_samples, 90)
        self.percentile_95 = np.percentile(sorted_samples, 95)
        
        # IQR (Interquartile Range)
        q1 = np.percentile(sorted_samples, 25)
        q3 = np.percentile(sorted_samples, 75)
        self.iqr = q3 - q1
        
        # Trimmed mean (remove top and bottom 10%)
        trim_count = max(1, n // 10)
        trimmed = sorted_samples[trim_count:-trim_count] if n > 4 else sorted_samples
        self.trimmed_mean = statistics.mean(trimmed)
        
        # Standard deviation
        self.std_dev = statistics.stdev(sorted_samples) if n > 1 else 0
        
        # Coefficient of variation (lower = more consistent)
        mean_val = statistics.mean(sorted_samples)
        self.coefficient_of_variation = (self.std_dev / mean_val) if mean_val > 0 else 0
        
        # Confidence score (based on sample size and consistency)
        # Higher samples + lower CV = higher confidence
        sample_factor = min(1.0, n / 5)  # Max out at 5 samples
        consistency_factor = max(0, 1 - self.coefficient_of_variation)
        self.confidence_score = round(sample_factor * consistency_factor, 2)


@dataclass
class PerformanceMetrics:
    """Comprehensive performance metrics."""
    # Load time stats
    load_time_metrics: LoadTimeMetrics = field(default_factory=LoadTimeMetrics)
    
    # Size metrics
    html_size_bytes: int = 0
    total_requests: int = 0  # Would need browser automation
    
    # Timing breakdown (when using browser automation)
    dns_lookup_time: float = 0.0
    tcp_connect_time: float = 0.0
    ttfb: float = 0.0  # Time to First Byte
    dom_content_loaded: float = 0.0
    fully_loaded: float = 0.0
    
    # Derived metrics
    performance_grade: str = "unknown"  # A, B, C, D, F
    
    def calculate_grade(self) -> None:
        """Calculate performance grade based on metrics."""
        score = 100
        
        # Penalize slow load times (using trimmed mean)
        load_time = self.load_time_metrics.trimmed_mean or self.load_time_metrics.median
        if load_time > 5:
            score -= 40
        elif load_time > 3:
            score -= 25
        elif load_time > 2:
            score -= 10
        elif load_time > 1:
            score -= 5
        
        # Penalize large HTML
        if self.html_size_bytes > 500000:  # 500KB
            score -= 20
        elif self.html_size_bytes > 200000:  # 200KB
            score -= 10
        
        # Penalize slow TTFB
        if self.ttfb > 1:
            score -= 15
        elif self.ttfb > 0.5:
            score -= 5
        
        # Grade assignment
        if score >= 90:
            self.performance_grade = "A"
        elif score >= 80:
            self.performance_grade = "B"
        elif score >= 70:
            self.performance_grade = "C"
        elif score >= 60:
            self.performance_grade = "D"
        else:
            self.performance_grade = "F"


@dataclass
class SEOMetrics:
    """SEO-related metrics for buyer perspective."""
    has_meta_description: bool = False
    has_meta_keywords: bool = False
    has_og_tags: bool = False  # Open Graph
    has_twitter_cards: bool = False
    has_structured_data: bool = False  # JSON-LD, microdata
    has_sitemap: bool = False
    has_robots_txt: bool = False
    canonical_url: Optional[str] = None
    h1_count: int = 0
    h2_count: int = 0
    image_count: int = 0
    images_without_alt: int = 0
    internal_links: int = 0
    external_links: int = 0
    seo_score: int = 0
    
    def calculate_score(self) -> None:
        """Calculate overall SEO score."""
        score = 0
        
        if self.has_meta_description:
            score += 15
        if self.has_og_tags:
            score += 10
        if self.has_twitter_cards:
            score += 5
        if self.has_structured_data:
            score += 15
        if self.has_sitemap:
            score += 10
        if self.has_robots_txt:
            score += 5
        if self.h1_count == 1:  # Exactly one H1 is best practice
            score += 10
        if self.h2_count > 0:
            score += 5
        if self.images_without_alt == 0 and self.image_count > 0:
            score += 10
        elif self.image_count > 0:
            alt_ratio = 1 - (self.images_without_alt / self.image_count)
            score += int(10 * alt_ratio)
        if self.canonical_url:
            score += 5
        
        # Penalize issues
        if self.h1_count > 1:
            score -= 5
        if self.h1_count == 0:
            score -= 10
        
        self.seo_score = max(0, min(100, score))


@dataclass
class SecurityMetrics:
    """Security-related metrics."""
    has_ssl: bool = False
    ssl_grade: Optional[str] = None  # Would need SSL Labs API
    has_hsts: bool = False
    has_csp: bool = False  # Content Security Policy
    has_x_frame_options: bool = False
    has_x_content_type_options: bool = False
    has_x_xss_protection: bool = False
    security_headers_score: int = 0
    
    def calculate_score(self) -> None:
        """Calculate security headers score."""
        score = 0
        if self.has_ssl:
            score += 30
        if self.has_hsts:
            score += 20
        if self.has_csp:
            score += 20
        if self.has_x_frame_options:
            score += 10
        if self.has_x_content_type_options:
            score += 10
        if self.has_x_xss_protection:
            score += 10
        
        self.security_headers_score = score


@dataclass
class AccessibilityMetrics:
    """Basic accessibility metrics."""
    has_lang_attribute: bool = False
    has_skip_link: bool = False
    forms_have_labels: bool = True
    images_have_alt: bool = True
    has_aria_landmarks: bool = False
    color_contrast_issues: int = 0  # Would need browser automation
    accessibility_score: int = 0
    
    def calculate_score(self) -> None:
        """Calculate basic accessibility score."""
        score = 0
        if self.has_lang_attribute:
            score += 20
        if self.has_skip_link:
            score += 15
        if self.forms_have_labels:
            score += 20
        if self.images_have_alt:
            score += 25
        if self.has_aria_landmarks:
            score += 20
        
        self.accessibility_score = score


@dataclass
class BusinessSignals:
    """Business-related signals for buyer qualification."""
    has_contact_page: bool = False
    has_contact_form: bool = False
    has_phone_number: bool = False
    has_email: bool = False
    has_physical_address: bool = False
    has_social_links: bool = False
    social_platforms: List[str] = field(default_factory=list)
    has_blog: bool = False
    has_testimonials: bool = False
    has_pricing_page: bool = False
    has_about_page: bool = False
    has_privacy_policy: bool = False
    has_terms_of_service: bool = False
    copyright_year: Optional[int] = None
    estimated_company_size: Optional[str] = None  # Based on signals
    business_legitimacy_score: int = 0
    
    def calculate_score(self) -> None:
        """Calculate business legitimacy score."""
        score = 0
        
        if self.has_contact_page:
            score += 10
        if self.has_contact_form:
            score += 5
        if self.has_phone_number:
            score += 15
        if self.has_email:
            score += 10
        if self.has_physical_address:
            score += 15
        if self.has_social_links:
            score += 5
        if len(self.social_platforms) >= 3:
            score += 5
        if self.has_about_page:
            score += 10
        if self.has_privacy_policy:
            score += 10
        if self.has_terms_of_service:
            score += 5
        if self.copyright_year and self.copyright_year >= 2023:
            score += 10
        
        self.business_legitimacy_score = min(100, score)


@dataclass 
class WebsiteIntelligence:
    """Comprehensive data structure for website analysis results."""
    domain: str
    
    # Basic info
    status_code: int = 0
    final_url: Optional[str] = None
    title: Optional[str] = None
    meta_description: Optional[str] = None
    
    # CMS & Technology
    cms_detected: Optional[str] = None
    cms_version: Optional[str] = None
    is_outdated_cms: bool = False
    technologies: List[str] = field(default_factory=list)
    
    # Comprehensive metrics
    performance: PerformanceMetrics = field(default_factory=PerformanceMetrics)
    seo: SEOMetrics = field(default_factory=SEOMetrics)
    security: SecurityMetrics = field(default_factory=SecurityMetrics)
    accessibility: AccessibilityMetrics = field(default_factory=AccessibilityMetrics)
    business: BusinessSignals = field(default_factory=BusinessSignals)
    
    # Mobile
    is_mobile_friendly: bool = True
    has_viewport_meta: bool = False
    
    # Overall scores
    overall_score: int = 0
    buyer_priority_score: int = 0  # How good a lead is this?
    
    # Meta
    analysis_timestamp: str = ""
    error: Optional[str] = None
    
    def calculate_overall_scores(self) -> None:
        """Calculate aggregate scores."""
        # Calculate component scores
        self.performance.calculate_grade()
        self.seo.calculate_score()
        self.security.calculate_score()
        self.accessibility.calculate_score()
        self.business.calculate_score()
        
        # Overall score (weighted)
        self.overall_score = int(
            self.performance_score * 0.25 +
            self.seo.seo_score * 0.20 +
            self.security.security_headers_score * 0.20 +
            self.accessibility.accessibility_score * 0.15 +
            self.business.business_legitimacy_score * 0.20
        )
        
        # Buyer priority score (focuses on what matters for sales)
        # Higher score = better lead (more issues to fix, but legitimate business)
        
        issues_score = 0
        
        # Performance issues (opportunity to sell optimization)
        load_time = self.performance.load_time_metrics.trimmed_mean
        if load_time > 3:
            issues_score += 20
        elif load_time > 2:
            issues_score += 10
        
        # Security issues (opportunity to sell security)
        if not self.security.has_ssl:
            issues_score += 25
        if self.security.security_headers_score < 50:
            issues_score += 15
        
        # SEO issues (opportunity to sell SEO services)
        if self.seo.seo_score < 50:
            issues_score += 20
        
        # Outdated CMS (opportunity to sell redesign)
        if self.is_outdated_cms:
            issues_score += 25
        
        # But only if it's a legitimate business
        legitimacy_multiplier = self.business.business_legitimacy_score / 100
        
        self.buyer_priority_score = int(issues_score * legitimacy_multiplier)
    
    @property
    def performance_score(self) -> int:
        """Convert performance grade to numeric score."""
        grade_map = {"A": 100, "B": 85, "C": 70, "D": 55, "F": 40, "unknown": 50}
        return grade_map.get(self.performance.performance_grade, 50)


class RobustWebsiteScraper:
    """
    Async website analyzer with statistical robustness.
    Performs multiple measurements and uses robust statistics.
    """
    
    def __init__(
        self, 
        max_concurrent: int = MAX_CONCURRENT_REQUESTS,
        measurement_rounds: int = 3,  # Number of times to measure each site
        measurement_delay: float = 0.5  # Delay between measurements
    ):
        self.max_concurrent = max_concurrent
        self.measurement_rounds = measurement_rounds
        self.measurement_delay = measurement_delay
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.headers = {
            'User-Agent': USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
    
    async def analyze_website(
        self, 
        domain: str, 
        client: httpx.AsyncClient
    ) -> WebsiteIntelligence:
        """Analyze a single website with multiple measurements."""
        
        intel = WebsiteIntelligence(
            domain=domain,
            analysis_timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
        )
        
        async with self.semaphore:
            # Perform multiple load time measurements
            load_times = []
            html_content = None
            response_headers = None
            
            urls_to_try = [f"https://{domain}", f"http://{domain}"]
            working_url = None
            
            for url in urls_to_try:
                try:
                    # First request to establish connection and get content
                    start_time = time.time()
                    response = await client.get(
                        url, 
                        follow_redirects=True,
                        timeout=REQUEST_TIMEOUT
                    )
                    first_load_time = time.time() - start_time
                    
                    if response.status_code == 200:
                        working_url = str(response.url)
                        intel.status_code = response.status_code
                        intel.final_url = working_url
                        intel.security.has_ssl = working_url.startswith('https')
                        
                        html_content = response.text
                        response_headers = response.headers
                        intel.performance.html_size_bytes = len(response.content)
                        
                        # Record first measurement
                        load_times.append(first_load_time)
                        
                        # Additional measurements for statistical robustness
                        for _ in range(self.measurement_rounds - 1):
                            await asyncio.sleep(self.measurement_delay)
                            try:
                                start_time = time.time()
                                await client.get(
                                    working_url,
                                    follow_redirects=True,
                                    timeout=REQUEST_TIMEOUT
                                )
                                load_times.append(time.time() - start_time)
                            except Exception:
                                pass  # Don't fail if subsequent measurements fail
                        
                        break
                        
                except httpx.TimeoutException:
                    intel.error = "timeout"
                except httpx.ConnectError:
                    intel.error = "connection_failed"
                except Exception as e:
                    intel.error = str(e)[:100]
            
            # Calculate load time statistics
            if load_times:
                intel.performance.load_time_metrics.samples = [round(t, 3) for t in load_times]
                intel.performance.load_time_metrics.calculate()
            
            # Parse HTML content
            if html_content:
                await self._parse_html(html_content, intel)
            
            # Parse security headers
            if response_headers:
                self._parse_security_headers(response_headers, intel)
            
            # Check additional pages
            if working_url:
                await self._check_additional_pages(domain, client, intel)
            
            # Calculate all scores
            intel.calculate_overall_scores()
        
        return intel
    
    async def _parse_html(self, html: str, intel: WebsiteIntelligence) -> None:
        """Extract comprehensive information from HTML."""
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            html_lower = html.lower()
            
            # Basic info
            title_tag = soup.find('title')
            if title_tag:
                intel.title = title_tag.get_text(strip=True)[:200]
            
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                intel.meta_description = meta_desc.get('content', '')[:300]
                intel.seo.has_meta_description = bool(intel.meta_description)
            
            # SEO metrics
            meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
            intel.seo.has_meta_keywords = meta_keywords is not None
            
            og_tags = soup.find('meta', attrs={'property': re.compile(r'^og:')})
            intel.seo.has_og_tags = og_tags is not None
            
            twitter_cards = soup.find('meta', attrs={'name': re.compile(r'^twitter:')})
            intel.seo.has_twitter_cards = twitter_cards is not None
            
            # Structured data
            json_ld = soup.find('script', attrs={'type': 'application/ld+json'})
            microdata = soup.find(attrs={'itemscope': True})
            intel.seo.has_structured_data = json_ld is not None or microdata is not None
            
            # Canonical URL
            canonical = soup.find('link', attrs={'rel': 'canonical'})
            if canonical:
                intel.seo.canonical_url = canonical.get('href')
            
            # Headings
            intel.seo.h1_count = len(soup.find_all('h1'))
            intel.seo.h2_count = len(soup.find_all('h2'))
            
            # Images
            images = soup.find_all('img')
            intel.seo.image_count = len(images)
            intel.seo.images_without_alt = len([img for img in images if not img.get('alt')])
            intel.accessibility.images_have_alt = intel.seo.images_without_alt == 0
            
            # Links
            links = soup.find_all('a', href=True)
            for link in links:
                href = link.get('href', '')
                if href.startswith(('http://', 'https://')) and intel.domain not in href:
                    intel.seo.external_links += 1
                else:
                    intel.seo.internal_links += 1
            
            # Mobile friendly
            viewport = soup.find('meta', attrs={'name': 'viewport'})
            intel.has_viewport_meta = viewport is not None
            intel.is_mobile_friendly = viewport is not None
            
            # Accessibility
            html_tag = soup.find('html')
            intel.accessibility.has_lang_attribute = html_tag and html_tag.get('lang') is not None
            
            skip_link = soup.find('a', attrs={'href': '#main'}) or soup.find('a', attrs={'class': re.compile(r'skip')})
            intel.accessibility.has_skip_link = skip_link is not None
            
            aria_landmarks = soup.find(attrs={'role': re.compile(r'main|navigation|banner|contentinfo')})
            intel.accessibility.has_aria_landmarks = aria_landmarks is not None
            
            # CMS Detection
            intel.cms_detected, intel.cms_version = self._detect_cms(html, soup)
            if intel.cms_detected:
                intel.is_outdated_cms = self._check_outdated_cms(intel.cms_detected, intel.cms_version)
            
            # Technology detection
            intel.technologies = self._detect_technologies(html, soup)
            
            # Business signals from content
            self._extract_business_signals(html, soup, intel)
            
        except Exception as e:
            pass
    
    def _detect_cms(self, html: str, soup: BeautifulSoup) -> tuple[Optional[str], Optional[str]]:
        """Detect CMS and version from HTML patterns."""
        
        html_lower = html.lower()
        
        # WordPress
        if 'wp-content' in html_lower or 'wordpress' in html_lower:
            version = None
            # Try meta generator
            generator = soup.find('meta', attrs={'name': 'generator'})
            if generator:
                gen_content = generator.get('content', '')
                version_match = re.search(r'WordPress\s*([\d.]+)', gen_content, re.I)
                if version_match:
                    version = version_match.group(1)
            return "wordpress", version
        
        # Wix
        if 'wix.com' in html_lower or '_wix' in html_lower:
            return "wix", None
        
        # Squarespace
        if 'squarespace' in html_lower:
            return "squarespace", None
        
        # Shopify
        if 'shopify' in html_lower or 'cdn.shopify' in html_lower:
            return "shopify", None
        
        # Webflow
        if 'webflow' in html_lower:
            return "webflow", None
        
        # Joomla
        if '/joomla' in html_lower or 'joomla' in html_lower:
            version = None
            generator = soup.find('meta', attrs={'name': 'generator'})
            if generator:
                gen_content = generator.get('content', '')
                version_match = re.search(r'Joomla[!]?\s*([\d.]+)', gen_content, re.I)
                if version_match:
                    version = version_match.group(1)
            return "joomla", version
        
        # Drupal
        if 'drupal' in html_lower:
            return "drupal", None
        
        return None, None
    
    def _check_outdated_cms(self, cms: str, version: Optional[str]) -> bool:
        """Check if CMS version is outdated."""
        
        # Current stable versions (update periodically)
        current_versions = {
            "wordpress": "6.4",
            "joomla": "5.0",
            "drupal": "10.0",
        }
        
        if not version or cms not in current_versions:
            return False
        
        try:
            current = tuple(map(int, current_versions[cms].split('.')))
            detected = tuple(map(int, version.split('.')[:2]))
            
            # Consider outdated if more than one major version behind
            if detected[0] < current[0] - 1:
                return True
            if detected[0] == current[0] - 1 and len(current) > 1 and current[1] > 5:
                return True
                
        except (ValueError, IndexError):
            pass
        
        return False
    
    def _detect_technologies(self, html: str, soup: BeautifulSoup) -> List[str]:
        """Detect technologies used."""
        
        techs = []
        html_lower = html.lower()
        
        # JavaScript frameworks
        if 'react' in html_lower or 'reactdom' in html_lower or '__NEXT_DATA__' in html:
            techs.append('react')
        if 'vue' in html_lower or 'vuejs' in html_lower:
            techs.append('vue')
        if 'angular' in html_lower or 'ng-' in html:
            techs.append('angular')
        if 'jquery' in html_lower:
            techs.append('jquery')
        if 'svelte' in html_lower:
            techs.append('svelte')
        
        # Analytics & Marketing
        if 'google-analytics' in html_lower or 'gtag' in html_lower or 'ga.js' in html_lower:
            techs.append('google_analytics')
        if 'googletagmanager' in html_lower:
            techs.append('google_tag_manager')
        if 'facebook.com/tr' in html_lower or 'fbevents' in html_lower:
            techs.append('facebook_pixel')
        if 'hotjar' in html_lower:
            techs.append('hotjar')
        if 'intercom' in html_lower:
            techs.append('intercom')
        if 'hubspot' in html_lower:
            techs.append('hubspot')
        if 'mailchimp' in html_lower:
            techs.append('mailchimp')
        
        # CSS Frameworks
        if 'bootstrap' in html_lower:
            techs.append('bootstrap')
        if 'tailwind' in html_lower:
            techs.append('tailwind')
        if 'bulma' in html_lower:
            techs.append('bulma')
        
        # CDNs
        if 'cloudflare' in html_lower:
            techs.append('cloudflare')
        if 'fastly' in html_lower:
            techs.append('fastly')
        if 'akamai' in html_lower:
            techs.append('akamai')
        
        return techs
    
    def _parse_security_headers(self, headers: httpx.Headers, intel: WebsiteIntelligence) -> None:
        """Parse security-related headers."""
        
        intel.security.has_hsts = 'strict-transport-security' in headers
        intel.security.has_csp = 'content-security-policy' in headers
        intel.security.has_x_frame_options = 'x-frame-options' in headers
        intel.security.has_x_content_type_options = 'x-content-type-options' in headers
        intel.security.has_x_xss_protection = 'x-xss-protection' in headers
    
    def _extract_business_signals(self, html: str, soup: BeautifulSoup, intel: WebsiteIntelligence) -> None:
        """Extract business-related signals from page content."""
        
        html_lower = html.lower()
        text_content = soup.get_text().lower()
        
        # Phone number detection
        phone_patterns = [
            r'\+?1?[-.\s]?$?\d{3}$?[-.\s]?\d{3}[-.\s]?\d{4}',  # US
            r'\+44\s?\d{4}\s?\d{6}',  # UK
            r'\+\d{1,3}[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}',  # International
        ]
        for pattern in phone_patterns:
            if re.search(pattern, html):
                intel.business.has_phone_number = True
                break
        
        # Email detection
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_pattern, html)
        # Filter out common false positives
        valid_emails = [e for e in emails if not any(x in e.lower() for x in ['example', 'test', 'your', 'email'])]
        intel.business.has_email = len(valid_emails) > 0
        
        # Physical address indicators
        address_indicators = ['street', 'avenue', 'road', 'blvd', 'suite', 'floor', 'zip', 'postal']
        intel.business.has_physical_address = any(ind in text_content for ind in address_indicators)
        
        # Social links
        social_platforms = {
            'facebook': ['facebook.com', 'fb.com'],
            'twitter': ['twitter.com', 'x.com'],
            'linkedin': ['linkedin.com'],
            'instagram': ['instagram.com'],
            'youtube': ['youtube.com'],
            'tiktok': ['tiktok.com'],
            'pinterest': ['pinterest.com'],
        }
        
        for platform, domains in social_platforms.items():
            for domain in domains:
                if domain in html_lower:
                    intel.business.social_platforms.append(platform)
                    break
        
        intel.business.has_social_links = len(intel.business.social_platforms) > 0
        
        # Blog detection
        blog_indicators = ['/blog', '/news', '/articles', '/posts']
        intel.business.has_blog = any(ind in html_lower for ind in blog_indicators)
        
        # Testimonials
        testimonial_indicators = ['testimonial', 'review', 'customer says', 'what our clients']
        intel.business.has_testimonials = any(ind in text_content for ind in testimonial_indicators)
        
        # Copyright year
        copyright_match = re.search(r'©\s*(\d{4})|copyright\s*(\d{4})', html_lower)
        if copyright_match:
            year = copyright_match.group(1) or copyright_match.group(2)
            intel.business.copyright_year = int(year)
        
        # Contact form detection
        forms = soup.find_all('form')
        for form in forms:
            form_html = str(form).lower()
            if any(x in form_html for x in ['contact', 'message', 'inquiry', 'email', 'name']):
                intel.business.has_contact_form = True
                break
    
    async def _check_additional_pages(
        self, 
        domain: str, 
        client: httpx.AsyncClient, 
        intel: WebsiteIntelligence
    ) -> None:
        """Check for existence of important pages."""
        
        pages_to_check = {
            '/contact': 'has_contact_page',
            '/contact-us': 'has_contact_page',
            '/about': 'has_about_page',
            '/about-us': 'has_about_page',
            '/pricing': 'has_pricing_page',
            '/privacy': 'has_privacy_policy',
            '/privacy-policy': 'has_privacy_policy',
            '/terms': 'has_terms_of_service',
            '/terms-of-service': 'has_terms_of_service',
            '/sitemap.xml': None,  # Special handling
            '/robots.txt': None,  # Special handling
        }
        
        base_url = f"https://{domain}"
        
        tasks = []
        for path in pages_to_check.keys():
            tasks.append(self._check_page_exists(f"{base_url}{path}", client))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for (path, attr), exists in zip(pages_to_check.items(), results):
            if isinstance(exists, bool) and exists:
                if path == '/sitemap.xml':
                    intel.seo.has_sitemap = True
                elif path == '/robots.txt':
                    intel.seo.has_robots_txt = True
                elif attr:
                    # Set the business attribute if not already set
                    current = getattr(intel.business, attr, False)
                    if not current:
                        setattr(intel.business, attr, True)
    
    async def _check_page_exists(self, url: str, client: httpx.AsyncClient) -> bool:
        """Check if a page exists (returns 200)."""
        try:
            response = await client.head(url, follow_redirects=True, timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    async def analyze_batch(self, domains: List[str]) -> List[WebsiteIntelligence]:
        """Analyze multiple websites concurrently."""
        
        results = []
        
        async with httpx.AsyncClient(headers=self.headers, http2=True) as client:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            ) as progress:
                
                task = progress.add_task("Scraping websites...", total=len(domains))
                
                # Process in batches
                batch_size = self.max_concurrent * 2
                
                for i in range(0, len(domains), batch_size):
                    batch = domains[i:i + batch_size]
                    tasks = [self.analyze_website(domain, client) for domain in batch]
                    batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    for result in batch_results:
                        if isinstance(result, WebsiteIntelligence):
                            results.append(result)
                    
                    progress.update(task, advance=len(batch))
        
        return results


def flatten_intelligence(intel: WebsiteIntelligence) -> Dict[str, Any]:
    """Flatten nested dataclass to flat dictionary for CSV export."""
    
    flat = {
        'domain': intel.domain,
        'status_code': intel.status_code,
        'final_url': intel.final_url,
        'title': intel.title,
        'meta_description': intel.meta_description,
        'cms_detected': intel.cms_detected,
        'cms_version': intel.cms_version,
        'is_outdated_cms': intel.is_outdated_cms,
        'technologies': ','.join(intel.technologies),
        'is_mobile_friendly': intel.is_mobile_friendly,
        'overall_score': intel.overall_score,
        'buyer_priority_score': intel.buyer_priority_score,
        'error': intel.error,
        'analysis_timestamp': intel.analysis_timestamp,
        
        # Performance metrics
        'load_time_median': intel.performance.load_time_metrics.median,
        'load_time_trimmed_mean': intel.performance.load_time_metrics.trimmed_mean,
        'load_time_p90': intel.performance.load_time_metrics.percentile_90,
        'load_time_p95': intel.performance.load_time_metrics.percentile_95,
        'load_time_std_dev': intel.performance.load_time_metrics.std_dev,
        'load_time_cv': intel.performance.load_time_metrics.coefficient_of_variation,
        'load_time_confidence': intel.performance.load_time_metrics.confidence_score,
        'load_time_samples': len(intel.performance.load_time_metrics.samples),
        'html_size_bytes': intel.performance.html_size_bytes,
        'performance_grade': intel.performance.performance_grade,
        
        # SEO metrics
        'seo_score': intel.seo.seo_score,
        'has_meta_description': intel.seo.has_meta_description,
        'has_og_tags': intel.seo.has_og_tags,
        'has_structured_data': intel.seo.has_structured_data,
        'has_sitemap': intel.seo.has_sitemap,
        'has_robots_txt': intel.seo.has_robots_txt,
        'h1_count': intel.seo.h1_count,
        'images_without_alt': intel.seo.images_without_alt,
        
        # Security metrics
        'has_ssl': intel.security.has_ssl,
        'has_hsts': intel.security.has_hsts,
        'has_csp': intel.security.has_csp,
        'security_score': intel.security.security_headers_score,
        
        # Accessibility
        'accessibility_score': intel.accessibility.accessibility_score,
        'has_lang_attribute': intel.accessibility.has_lang_attribute,
        
        # Business signals
        'business_score': intel.business.business_legitimacy_score,
        'has_contact_page': intel.business.has_contact_page,
        'has_contact_form': intel.business.has_contact_form,
        'has_phone_number': intel.business.has_phone_number,
        'has_email': intel.business.has_email,
        'has_physical_address': intel.business.has_physical_address,
        'social_platforms': ','.join(intel.business.social_platforms),
        'has_privacy_policy': intel.business.has_privacy_policy,
        'copyright_year': intel.business.copyright_year,
    }
    
    return flat


def scrape_websites(
    input_file: str, 
    output_file: Optional[str] = None,
    measurement_rounds: int = 3
) -> pd.DataFrame:
    """
    Main function to scrape websites from cleaned lead file.
    
    Args:
        input_file: Input CSV filename in data/cleaned/
        output_file: Output CSV filename in data/enriched/
        measurement_rounds: Number of load time measurements per site
    """
    
    log_step("Starting comprehensive website intelligence scraping")
    
    # Load cleaned leads
    input_path = CLEANED_DIR / input_file
    df = load_csv_safe(str(input_path))
    
    if df.empty or 'domain' not in df.columns:
        log_error("No valid data to process")
        return pd.DataFrame()
    
    domains = df['domain'].tolist()
    log_success(f"Found {len(domains)} domains to analyze")
    log_step(f"Using {measurement_rounds} measurement rounds for load time statistics")
    
    # Run async scraper
    scraper = RobustWebsiteScraper(measurement_rounds=measurement_rounds)
    results = asyncio.run(scraper.analyze_batch(domains))
    
    # Convert to flat DataFrame
    results_data = [flatten_intelligence(r) for r in results]
    results_df = pd.DataFrame(results_data)
    
    # Merge with original data
    merged_df = df.merge(results_df, on='domain', how='left')
    
    # Statistics
    successful = len(results_df[results_df['error'].isna()])
    with_ssl = len(results_df[results_df['has_ssl'] == True])
    high_priority = len(results_df[results_df['buyer_priority_score'] >= 50])
    outdated_cms = len(results_df[results_df['is_outdated_cms'] == True])
    
    # Load time statistics
    valid_load_times = results_df[results_df['load_time_median'] > 0]['load_time_median']
    if len(valid_load_times) > 0:
        avg_load_time = valid_load_times.mean()
        median_load_time = valid_load_times.median()
    else:
        avg_load_time = median_load_time = 0
    
    log_step("Scraping complete - Summary")
    log_success(f"Successfully analyzed: {successful}/{len(domains)}")
    log_success(f"Sites with SSL: {with_ssl}")
    log_success(f"High priority leads (score >= 50): {high_priority}")
    log_warning(f"Outdated CMS detected: {outdated_cms}")
    log_step(f"Load times - Mean: {avg_load_time:.2f}s, Median: {median_load_time:.2f}s")
    
    # Save output
    if output_file is None:
        output_file = input_file.replace('_cleaned.csv', '_enriched.csv').replace('.csv', '_enriched.csv')
    
    output_path = ENRICHED_DIR / output_file
    save_csv(merged_df, str(output_path))
    
    return merged_df


def main():
    """Run scraper from command line."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Scrape comprehensive website intelligence')
    parser.add_argument('input_file', help='Input CSV filename (in data/cleaned/)')
    parser.add_argument('output_file', nargs='?', help='Output CSV filename (in data/enriched/)')
    parser.add_argument('--rounds', type=int, default=3, help='Number of load time measurements (default: 3)')
    
    args = parser.parse_args()
    scrape_websites(args.input_file, args.output_file, args.rounds)


if __name__ == "__main__":
    main()