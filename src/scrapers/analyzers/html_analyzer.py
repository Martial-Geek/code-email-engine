"""HTML content analyzer for extracting metrics and signals."""

import re
from typing import Optional

from bs4 import BeautifulSoup

from ..models.website_intelligence import WebsiteIntelligence
from .cms_detector import CMSDetector
from .tech_detector import TechnologyDetector


class HTMLAnalyzer:
    """Analyzes HTML content to extract comprehensive metrics."""
    
    # Social platforms for detection
    SOCIAL_PLATFORMS = {
        'facebook': ['facebook.com', 'fb.com'],
        'twitter': ['twitter.com', 'x.com'],
        'linkedin': ['linkedin.com'],
        'instagram': ['instagram.com'],
        'youtube': ['youtube.com'],
        'tiktok': ['tiktok.com'],
        'pinterest': ['pinterest.com'],
        'github': ['github.com'],
        'medium': ['medium.com'],
    }
    
    # Patterns for business signal detection
    PHONE_PATTERNS = [
        r'\+?1?[-.\s]?$?\d{3}$?[-.\s]?\d{3}[-.\s]?\d{4}',  # US/Canada
        r'\+44\s?\d{4}\s?\d{6}',  # UK
        r'\+49\s?\d{3,4}\s?\d{6,8}',  # Germany
        r'\+33\s?\d\s?\d{2}\s?\d{2}\s?\d{2}\s?\d{2}',  # France
        r'\+\d{1,3}[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}',  # International
    ]
    
    EMAIL_PATTERN = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    
    # False positive filters for email detection
    EMAIL_FALSE_POSITIVES = [
        'example', 'test', 'your', 'email', 'domain', 
        'sample', 'user', 'name', 'info@example'
    ]
    
    # Address indicators
    ADDRESS_INDICATORS = [
        'street', 'avenue', 'road', 'blvd', 'boulevard', 'suite', 
        'floor', 'zip', 'postal', 'address', 'ave', 'st.', 'rd.',
        'lane', 'drive', 'court', 'plaza', 'building'
    ]
    
    # Blog indicators
    BLOG_INDICATORS = ['/blog', '/news', '/articles', '/posts', '/insights', '/resources']
    
    # Testimonial indicators
    TESTIMONIAL_INDICATORS = [
        'testimonial', 'review', 'customer says', 'what our clients',
        'client stories', 'success stories', 'case study', 'case studies',
        'feedback', 'what people say'
    ]
    
    def __init__(self):
        self.cms_detector = CMSDetector()
        self.tech_detector = TechnologyDetector()
    
    def analyze(self, html: str, intel: WebsiteIntelligence) -> None:
        """
        Extract comprehensive information from HTML.
        
        Args:
            html: Raw HTML content
            intel: WebsiteIntelligence object to populate
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')
            html_lower = html.lower()
            
            # Basic info
            self._extract_basic_info(soup, intel)
            
            # SEO metrics
            self._extract_seo_metrics(soup, html_lower, intel)
            
            # Accessibility metrics
            self._extract_accessibility_metrics(soup, intel)
            
            # CMS Detection
            cms, version = self.cms_detector.detect(html, soup)
            intel.cms_detected = cms
            intel.cms_version = version
            if cms:
                intel.is_outdated_cms = self.cms_detector.is_outdated(cms, version)
            
            # Technology detection
            intel.technologies = self.tech_detector.detect(html, soup)
            
            # Mobile friendly checks
            self._extract_mobile_metrics(soup, intel)
            
            # Business signals from content
            self._extract_business_signals(html, soup, intel)
            
        except Exception:
            # Don't fail completely on parse errors
            pass
    
    def _extract_basic_info(
        self, 
        soup: BeautifulSoup, 
        intel: WebsiteIntelligence
    ) -> None:
        """Extract basic page information."""
        # Title
        title_tag = soup.find('title')
        if title_tag:
            intel.title = title_tag.get_text(strip=True)[:200]
        
        # Meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            intel.meta_description = meta_desc.get('content', '')[:300]
    
    def _extract_seo_metrics(
        self, 
        soup: BeautifulSoup, 
        html_lower: str, 
        intel: WebsiteIntelligence
    ) -> None:
        """Extract SEO-related metrics."""
        seo = intel.seo
        
        # Meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        seo.has_meta_description = (
            meta_desc is not None and 
            bool(meta_desc.get('content', '').strip())
        )
        
        # Meta keywords
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        seo.has_meta_keywords = meta_keywords is not None
        
        # Open Graph tags
        og_tags = soup.find('meta', attrs={'property': re.compile(r'^og:')})
        seo.has_og_tags = og_tags is not None
        
        # Twitter cards
        twitter_cards = soup.find('meta', attrs={'name': re.compile(r'^twitter:')})
        seo.has_twitter_cards = twitter_cards is not None
        
        # Structured data (JSON-LD or microdata)
        json_ld = soup.find('script', attrs={'type': 'application/ld+json'})
        microdata = soup.find(attrs={'itemscope': True})
        seo.has_structured_data = json_ld is not None or microdata is not None
        
        # Canonical URL
        canonical = soup.find('link', attrs={'rel': 'canonical'})
        if canonical:
            seo.canonical_url = canonical.get('href')
        
        # Headings count
        seo.h1_count = len(soup.find_all('h1'))
        seo.h2_count = len(soup.find_all('h2'))
        
        # Images analysis
        images = soup.find_all('img')
        seo.image_count = len(images)
        seo.images_without_alt = len([
            img for img in images 
            if not img.get('alt')
        ])
        
        # Links analysis
        links = soup.find_all('a', href=True)
        for link in links:
            href = link.get('href', '')
            if href.startswith(('http://', 'https://')) and intel.domain not in href:
                seo.external_links += 1
            elif href and not href.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
                seo.internal_links += 1
    
    def _extract_accessibility_metrics(
        self, 
        soup: BeautifulSoup, 
        intel: WebsiteIntelligence
    ) -> None:
        """Extract accessibility-related metrics."""
        accessibility = intel.accessibility
        
        # Language attribute on html tag
        html_tag = soup.find('html')
        accessibility.has_lang_attribute = (
            html_tag is not None and 
            html_tag.get('lang') is not None
        )
        
        # Skip navigation link
        skip_link = (
            soup.find('a', attrs={'href': '#main'}) or 
            soup.find('a', attrs={'href': '#content'}) or
            soup.find('a', attrs={'href': '#main-content'}) or
            soup.find('a', attrs={'class': re.compile(r'skip', re.I)}) or
            soup.find('a', string=re.compile(r'skip', re.I))
        )
        accessibility.has_skip_link = skip_link is not None
        
        # ARIA landmarks
        aria_landmarks = soup.find(
            attrs={'role': re.compile(r'^(main|navigation|banner|contentinfo|complementary|search)$')}
        )
        # Also check for HTML5 semantic elements
        semantic_elements = soup.find(['main', 'nav', 'header', 'footer', 'aside'])
        accessibility.has_aria_landmarks = (
            aria_landmarks is not None or 
            semantic_elements is not None
        )
        
        # Form labels check
        accessibility.forms_have_labels = self._check_form_labels(soup)
        
        # Images have alt (sync with SEO metrics)
        accessibility.images_have_alt = intel.seo.images_without_alt == 0
    
    def _check_form_labels(self, soup: BeautifulSoup) -> bool:
        """Check if form inputs have proper labels."""
        forms = soup.find_all('form')
        
        if not forms:
            return True  # No forms, so no issues
        
        inputs_without_labels = 0
        
        for form in forms:
            # Find all input elements that need labels
            inputs = form.find_all(['input', 'select', 'textarea'])
            
            for inp in inputs:
                input_type = inp.get('type', 'text').lower()
                
                # Skip inputs that don't need visible labels
                if input_type in ['hidden', 'submit', 'button', 'reset', 'image']:
                    continue
                
                # Check for various labeling methods
                has_label = (
                    # aria-label attribute
                    inp.get('aria-label') or
                    # aria-labelledby attribute
                    inp.get('aria-labelledby') or
                    # placeholder (not ideal but acceptable)
                    inp.get('placeholder') or
                    # title attribute
                    inp.get('title') or
                    # Associated label element
                    (inp.get('id') and soup.find('label', attrs={'for': inp.get('id')})) or
                    # Wrapped in label element
                    inp.find_parent('label')
                )
                
                if not has_label:
                    inputs_without_labels += 1
        
        return inputs_without_labels == 0
    
    def _extract_mobile_metrics(
        self, 
        soup: BeautifulSoup, 
        intel: WebsiteIntelligence
    ) -> None:
        """Extract mobile-friendliness metrics."""
        # Viewport meta tag
        viewport = soup.find('meta', attrs={'name': 'viewport'})
        intel.has_viewport_meta = viewport is not None
        
        # Basic mobile-friendly check
        # A proper viewport tag is a good indicator
        if viewport:
            viewport_content = viewport.get('content', '').lower()
            # Check for responsive viewport settings
            intel.is_mobile_friendly = (
                'width=device-width' in viewport_content or
                'initial-scale' in viewport_content
            )
        else:
            intel.is_mobile_friendly = False
    
    def _extract_business_signals(
        self, 
        html: str, 
        soup: BeautifulSoup, 
        intel: WebsiteIntelligence
    ) -> None:
        """Extract business-related signals from page content."""
        html_lower = html.lower()
        text_content = soup.get_text().lower()
        business = intel.business
        
        # Phone number detection
        self._detect_phone_numbers(html, business)
        
        # Email detection
        self._detect_emails(html, business)
        
        # Physical address detection
        business.has_physical_address = any(
            indicator in text_content 
            for indicator in self.ADDRESS_INDICATORS
        )
        
        # Social media links
        self._detect_social_links(html_lower, business)
        
        # Blog detection
        business.has_blog = any(
            indicator in html_lower 
            for indicator in self.BLOG_INDICATORS
        )
        
        # Testimonials detection
        business.has_testimonials = any(
            indicator in text_content 
            for indicator in self.TESTIMONIAL_INDICATORS
        )
        
        # Copyright year extraction
        self._extract_copyright_year(html_lower, business)
        
        # Contact form detection
        self._detect_contact_form(soup, business)
        
        # Pricing page indicators
        business.has_pricing_page = any(
            indicator in html_lower 
            for indicator in ['/pricing', '/plans', '/packages', 'pricing-table']
        )
    
    def _detect_phone_numbers(self, html: str, business) -> None:
        """Detect phone numbers in HTML."""
        for pattern in self.PHONE_PATTERNS:
            if re.search(pattern, html):
                business.has_phone_number = True
                return
    
    def _detect_emails(self, html: str, business) -> None:
        """Detect email addresses in HTML."""
        emails = re.findall(self.EMAIL_PATTERN, html)
        
        # Filter out false positives
        valid_emails = [
            email for email in emails 
            if not any(
                fp in email.lower() 
                for fp in self.EMAIL_FALSE_POSITIVES
            )
        ]
        
        business.has_email = len(valid_emails) > 0
    
    def _detect_social_links(self, html_lower: str, business) -> None:
        """Detect social media links."""
        for platform, domains in self.SOCIAL_PLATFORMS.items():
            for domain in domains:
                if domain in html_lower:
                    if platform not in business.social_platforms:
                        business.social_platforms.append(platform)
                    break
        
        business.has_social_links = len(business.social_platforms) > 0
    
    def _extract_copyright_year(self, html_lower: str, business) -> None:
        """Extract copyright year from HTML."""
        # Try different copyright patterns
        patterns = [
            r'©\s*(\d{4})',
            r'copyright\s*(\d{4})',
            r'copyright\s*©?\s*(\d{4})',
            r'$c$\s*(\d{4})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html_lower)
            if match:
                try:
                    year = int(match.group(1))
                    # Sanity check: year should be reasonable
                    if 1990 <= year <= 2030:
                        business.copyright_year = year
                        return
                except ValueError:
                    continue
    
    def _detect_contact_form(self, soup: BeautifulSoup, business) -> None:
        """Detect presence of contact form."""
        forms = soup.find_all('form')
        
        contact_indicators = [
            'contact', 'message', 'inquiry', 'enquiry', 
            'get in touch', 'reach out', 'send us', 'write to us'
        ]
        
        for form in forms:
            form_str = str(form).lower()
            form_text = form.get_text().lower()
            
            # Check form attributes and content
            if any(indicator in form_str or indicator in form_text 
                   for indicator in contact_indicators):
                business.has_contact_form = True
                return
            
            # Check for common contact form fields
            has_name = form.find(['input'], attrs={'name': re.compile(r'name', re.I)})
            has_email = form.find(['input'], attrs={'type': 'email'}) or \
                       form.find(['input'], attrs={'name': re.compile(r'email', re.I)})
            has_message = form.find(['textarea'])
            
            if has_name and has_email and has_message:
                business.has_contact_form = True
                return