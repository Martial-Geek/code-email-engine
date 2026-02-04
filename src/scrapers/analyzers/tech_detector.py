"""Technology stack detection from HTML content."""

from typing import List

from bs4 import BeautifulSoup


class TechnologyDetector:
    """Detects technologies used on a website."""
    
    def detect(self, html: str, soup: BeautifulSoup) -> List[str]:
        """
        Detect technologies from HTML patterns.
        
        Args:
            html: Raw HTML content
            soup: BeautifulSoup parsed object
            
        Returns:
            List of detected technology names
        """
        techs = []
        html_lower = html.lower()
        
        # JavaScript frameworks
        techs.extend(self._detect_js_frameworks(html, html_lower))
        
        # Analytics & Marketing
        techs.extend(self._detect_analytics(html_lower))
        
        # CSS Frameworks
        techs.extend(self._detect_css_frameworks(html_lower))
        
        # CDNs
        techs.extend(self._detect_cdns(html_lower))
        
        # Other technologies
        techs.extend(self._detect_other(html_lower))
        
        return list(set(techs))  # Remove duplicates
    
    def _detect_js_frameworks(self, html: str, html_lower: str) -> List[str]:
        """Detect JavaScript frameworks."""
        techs = []
        
        patterns = {
            'react': ['react', 'reactdom', '__NEXT_DATA__', '_next/'],
            'vue': ['vue', 'vuejs', '__vue__'],
            'angular': ['angular', 'ng-', 'ng-app'],
            'svelte': ['svelte'],
            'jquery': ['jquery'],
            'next.js': ['__NEXT_DATA__', '_next/'],
            'nuxt': ['__NUXT__', '_nuxt/'],
            'gatsby': ['gatsby'],
            'ember': ['ember'],
            'backbone': ['backbone'],
        }
        
        for tech, markers in patterns.items():
            for marker in markers:
                if marker in html_lower or marker in html:
                    techs.append(tech)
                    break
        
        return techs
    
    def _detect_analytics(self, html_lower: str) -> List[str]:
        """Detect analytics and marketing tools."""
        techs = []
        
        patterns = {
            'google_analytics': ['google-analytics', 'gtag', 'ga.js', 'analytics.js'],
            'google_tag_manager': ['googletagmanager', 'gtm.js'],
            'facebook_pixel': ['facebook.com/tr', 'fbevents', 'fbq('],
            'hotjar': ['hotjar'],
            'intercom': ['intercom'],
            'hubspot': ['hubspot', 'hs-scripts'],
            'mailchimp': ['mailchimp'],
            'segment': ['segment.com', 'analytics.min.js'],
            'mixpanel': ['mixpanel'],
            'amplitude': ['amplitude'],
            'heap': ['heap-'],
            'clarity': ['clarity.ms'],
            'plausible': ['plausible.io'],
        }
        
        for tech, markers in patterns.items():
            for marker in markers:
                if marker in html_lower:
                    techs.append(tech)
                    break
        
        return techs
    
    def _detect_css_frameworks(self, html_lower: str) -> List[str]:
        """Detect CSS frameworks."""
        techs = []
        
        patterns = {
            'bootstrap': ['bootstrap'],
            'tailwind': ['tailwind'],
            'bulma': ['bulma'],
            'foundation': ['foundation'],
            'materialize': ['materialize'],
            'semantic_ui': ['semantic-ui', 'semantic.min'],
        }
        
        for tech, markers in patterns.items():
            for marker in markers:
                if marker in html_lower:
                    techs.append(tech)
                    break
        
        return techs
    
    def _detect_cdns(self, html_lower: str) -> List[str]:
        """Detect CDN providers."""
        techs = []
        
        patterns = {
            'cloudflare': ['cloudflare', 'cdnjs.cloudflare'],
            'fastly': ['fastly'],
            'akamai': ['akamai'],
            'cloudfront': ['cloudfront.net'],
            'jsdelivr': ['jsdelivr'],
            'unpkg': ['unpkg.com'],
        }
        
        for tech, markers in patterns.items():
            for marker in markers:
                if marker in html_lower:
                    techs.append(tech)
                    break
        
        return techs
    
    def _detect_other(self, html_lower: str) -> List[str]:
        """Detect other technologies."""
        techs = []
        
        patterns = {
            'recaptcha': ['recaptcha', 'grecaptcha'],
            'stripe': ['stripe.com/v', 'stripe.js'],
            'paypal': ['paypal.com/sdk'],
            'google_maps': ['maps.googleapis', 'maps.google'],
            'youtube_embed': ['youtube.com/embed', 'youtube-nocookie'],
            'vimeo_embed': ['player.vimeo.com'],
            'typekit': ['use.typekit.net'],
            'google_fonts': ['fonts.googleapis', 'fonts.gstatic'],
            'font_awesome': ['fontawesome', 'font-awesome'],
            'livechat': ['livechat', 'livechatinc'],
            'zendesk': ['zendesk'],
            'drift': ['drift.com'],
            'crisp': ['crisp.chat'],
        }
        
        for tech, markers in patterns.items():
            for marker in markers:
                if marker in html_lower:
                    techs.append(tech)
                    break
        
        return techs