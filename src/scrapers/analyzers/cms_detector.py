"""CMS detection from HTML content."""

import re
from typing import Optional, Tuple

from bs4 import BeautifulSoup


class CMSDetector:
    """Detects Content Management Systems from HTML patterns."""
    
    # Current stable versions (update periodically)
    CURRENT_VERSIONS = {
        "wordpress": "6.4",
        "joomla": "5.0",
        "drupal": "10.0",
    }
    
    def detect(self, html: str, soup: BeautifulSoup) -> Tuple[Optional[str], Optional[str]]:
        """
        Detect CMS and version from HTML patterns.
        
        Args:
            html: Raw HTML content
            soup: BeautifulSoup parsed object
            
        Returns:
            Tuple of (cms_name, version) or (None, None)
        """
        html_lower = html.lower()
        
        # Check each CMS
        detectors = [
            self._detect_wordpress,
            self._detect_wix,
            self._detect_squarespace,
            self._detect_shopify,
            self._detect_webflow,
            self._detect_joomla,
            self._detect_drupal,
            self._detect_ghost,
            self._detect_magento,
            self._detect_prestashop,
        ]
        
        for detector in detectors:
            result = detector(html_lower, soup)
            if result[0]:
                return result
        
        return None, None
    
    def _detect_wordpress(
        self, 
        html_lower: str, 
        soup: BeautifulSoup
    ) -> Tuple[Optional[str], Optional[str]]:
        """Detect WordPress."""
        if 'wp-content' in html_lower or 'wordpress' in html_lower:
            version = None
            generator = soup.find('meta', attrs={'name': 'generator'})
            if generator:
                gen_content = generator.get('content', '')
                version_match = re.search(r'WordPress\s*([\d.]+)', gen_content, re.I)
                if version_match:
                    version = version_match.group(1)
            return "wordpress", version
        return None, None
    
    def _detect_wix(
        self, 
        html_lower: str, 
        soup: BeautifulSoup
    ) -> Tuple[Optional[str], Optional[str]]:
        """Detect Wix."""
        if 'wix.com' in html_lower or '_wix' in html_lower:
            return "wix", None
        return None, None
    
    def _detect_squarespace(
        self, 
        html_lower: str, 
        soup: BeautifulSoup
    ) -> Tuple[Optional[str], Optional[str]]:
        """Detect Squarespace."""
        if 'squarespace' in html_lower:
            return "squarespace", None
        return None, None
    
    def _detect_shopify(
        self, 
        html_lower: str, 
        soup: BeautifulSoup
    ) -> Tuple[Optional[str], Optional[str]]:
        """Detect Shopify."""
        if 'shopify' in html_lower or 'cdn.shopify' in html_lower:
            return "shopify", None
        return None, None
    
    def _detect_webflow(
        self, 
        html_lower: str, 
        soup: BeautifulSoup
    ) -> Tuple[Optional[str], Optional[str]]:
        """Detect Webflow."""
        if 'webflow' in html_lower:
            return "webflow", None
        return None, None
    
    def _detect_joomla(
        self, 
        html_lower: str, 
        soup: BeautifulSoup
    ) -> Tuple[Optional[str], Optional[str]]:
        """Detect Joomla."""
        if '/joomla' in html_lower or 'joomla' in html_lower:
            version = None
            generator = soup.find('meta', attrs={'name': 'generator'})
            if generator:
                gen_content = generator.get('content', '')
                version_match = re.search(r'Joomla[!]?\s*([\d.]+)', gen_content, re.I)
                if version_match:
                    version = version_match.group(1)
            return "joomla", version
        return None, None
    
    def _detect_drupal(
        self, 
        html_lower: str, 
        soup: BeautifulSoup
    ) -> Tuple[Optional[str], Optional[str]]:
        """Detect Drupal."""
        if 'drupal' in html_lower or 'sites/default/files' in html_lower:
            version = None
            generator = soup.find('meta', attrs={'name': 'generator'})
            if generator:
                gen_content = generator.get('content', '')
                version_match = re.search(r'Drupal\s*([\d.]+)', gen_content, re.I)
                if version_match:
                    version = version_match.group(1)
            return "drupal", version
        return None, None
    
    def _detect_ghost(
        self, 
        html_lower: str, 
        soup: BeautifulSoup
    ) -> Tuple[Optional[str], Optional[str]]:
        """Detect Ghost."""
        if 'ghost' in html_lower and 'content/images' in html_lower:
            return "ghost", None
        return None, None
    
    def _detect_magento(
        self, 
        html_lower: str, 
        soup: BeautifulSoup
    ) -> Tuple[Optional[str], Optional[str]]:
        """Detect Magento."""
        if 'magento' in html_lower or 'mage' in html_lower:
            return "magento", None
        return None, None
    
    def _detect_prestashop(
        self, 
        html_lower: str, 
        soup: BeautifulSoup
    ) -> Tuple[Optional[str], Optional[str]]:
        """Detect PrestaShop."""
        if 'prestashop' in html_lower:
            return "prestashop", None
        return None, None
    
    def is_outdated(self, cms: str, version: Optional[str]) -> bool:
        """
        Check if CMS version is outdated.
        
        Args:
            cms: CMS name
            version: Detected version string
            
        Returns:
            True if version is outdated
        """
        if not version or cms not in self.CURRENT_VERSIONS:
            return False
        
        try:
            current = tuple(map(int, self.CURRENT_VERSIONS[cms].split('.')))
            detected = tuple(map(int, version.split('.')[:2]))
            
            # Consider outdated if more than one major version behind
            if detected[0] < current[0] - 1:
                return True
            if detected[0] == current[0] - 1 and len(current) > 1 and current[1] > 5:
                return True
                
        except (ValueError, IndexError):
            pass
        
        return False