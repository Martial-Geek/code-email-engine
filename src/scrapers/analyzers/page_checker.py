"""Page existence checker for additional website pages."""

import asyncio
import re
from typing import Dict, List, Tuple, Optional, TYPE_CHECKING
from xml.etree import ElementTree

import httpx

if TYPE_CHECKING:
    from ..models.website_intelligence import WebsiteIntelligence


class PageChecker:
    """
    Checks for existence of important pages on a website.
    
    This includes checking for:
    - Contact pages
    - About pages
    - Privacy policy
    - Terms of service
    - Sitemap
    - Robots.txt
    - Blog/News sections
    - And other important business pages
    """
    
    # Pages to check and their corresponding attributes
    # Format: path -> (object_name, attribute_name)
    PAGES_TO_CHECK: Dict[str, Tuple[str, str]] = {
        # Contact pages
        '/contact': ('business', 'has_contact_page'),
        '/contact-us': ('business', 'has_contact_page'),
        '/contactus': ('business', 'has_contact_page'),
        '/get-in-touch': ('business', 'has_contact_page'),
        '/reach-us': ('business', 'has_contact_page'),
        
        # About pages
        '/about': ('business', 'has_about_page'),
        '/about-us': ('business', 'has_about_page'),
        '/aboutus': ('business', 'has_about_page'),
        '/company': ('business', 'has_about_page'),
        '/who-we-are': ('business', 'has_about_page'),
        '/our-story': ('business', 'has_about_page'),
        
        # Pricing pages
        '/pricing': ('business', 'has_pricing_page'),
        '/prices': ('business', 'has_pricing_page'),
        '/plans': ('business', 'has_pricing_page'),
        '/packages': ('business', 'has_pricing_page'),
        '/buy': ('business', 'has_pricing_page'),
        
        # Legal pages - Privacy
        '/privacy': ('business', 'has_privacy_policy'),
        '/privacy-policy': ('business', 'has_privacy_policy'),
        '/privacypolicy': ('business', 'has_privacy_policy'),
        '/privacy_policy': ('business', 'has_privacy_policy'),
        '/data-privacy': ('business', 'has_privacy_policy'),
        
        # Legal pages - Terms
        '/terms': ('business', 'has_terms_of_service'),
        '/terms-of-service': ('business', 'has_terms_of_service'),
        '/terms-and-conditions': ('business', 'has_terms_of_service'),
        '/termsofservice': ('business', 'has_terms_of_service'),
        '/tos': ('business', 'has_terms_of_service'),
        '/legal': ('business', 'has_terms_of_service'),
        '/terms-of-use': ('business', 'has_terms_of_service'),
        
        # SEO pages
        '/sitemap.xml': ('seo', 'has_sitemap'),
        '/sitemap': ('seo', 'has_sitemap'),
        '/sitemap_index.xml': ('seo', 'has_sitemap'),
        '/sitemap-index.xml': ('seo', 'has_sitemap'),
        '/robots.txt': ('seo', 'has_robots_txt'),
    }
    
    # Additional paths to check for specific signals
    BLOG_PATHS = [
        '/blog', 
        '/news', 
        '/articles', 
        '/insights', 
        '/resources', 
        '/posts',
        '/updates',
        '/stories',
        '/journal',
    ]
    
    CAREERS_PATHS = [
        '/careers', 
        '/jobs', 
        '/join-us', 
        '/work-with-us',
        '/opportunities',
        '/hiring',
    ]
    
    SUPPORT_PATHS = [
        '/support', 
        '/help', 
        '/faq', 
        '/faqs', 
        '/knowledge-base',
        '/help-center',
        '/documentation',
        '/docs',
    ]
    
    ECOMMERCE_PATHS = [
        '/shop',
        '/store',
        '/products',
        '/cart',
        '/checkout',
        '/catalog',
    ]
    
    def __init__(self, timeout: float = 5.0, max_concurrent: int = 10):
        """
        Initialize page checker.
        
        Args:
            timeout: Request timeout in seconds
            max_concurrent: Maximum concurrent requests
        """
        self.timeout = timeout
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def check_pages(
        self,
        domain: str,
        client: httpx.AsyncClient,
        intel: 'WebsiteIntelligence'
    ) -> None:
        """
        Check for existence of important pages and update intelligence object.
        
        Args:
            domain: Website domain
            client: HTTP client
            intel: WebsiteIntelligence object to update
        """
        # Determine base URL (prefer HTTPS)
        if intel.final_url:
            # Extract base from final URL
            base_url = self._extract_base_url(intel.final_url)
        else:
            base_url = f"https://{domain}"
        
        # Run all checks concurrently
        await asyncio.gather(
            self._check_main_pages(base_url, client, intel),
            self._check_blog(base_url, client, intel),
            return_exceptions=True
        )
    
    def _extract_base_url(self, url: str) -> str:
        """Extract base URL from a full URL."""
        # Remove path, query, fragment
        match = re.match(r'(https?://[^/]+)', url)
        if match:
            return match.group(1)
        return url
    
    async def _check_main_pages(
        self,
        base_url: str,
        client: httpx.AsyncClient,
        intel: 'WebsiteIntelligence'
    ) -> None:
        """Check main pages from PAGES_TO_CHECK."""
        tasks = []
        paths = list(self.PAGES_TO_CHECK.keys())
        
        for path in paths:
            url = f"{base_url}{path}"
            tasks.append(self._check_page_exists(url, client))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for path, exists in zip(paths, results):
            if isinstance(exists, bool) and exists:
                obj_name, attr_name = self.PAGES_TO_CHECK[path]
                
                # Get the target object (seo or business)
                target_obj = getattr(intel, obj_name, None)
                
                if target_obj is not None:
                    # Only set if not already set (first match wins)
                    current = getattr(target_obj, attr_name, False)
                    if not current:
                        setattr(target_obj, attr_name, True)
    
    async def _check_blog(
        self,
        base_url: str,
        client: httpx.AsyncClient,
        intel: 'WebsiteIntelligence'
    ) -> None:
        """Check for blog/news section."""
        if intel.business.has_blog:
            return  # Already detected from HTML
        
        tasks = [
            self._check_page_exists(f"{base_url}{path}", client)
            for path in self.BLOG_PATHS
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for exists in results:
            if isinstance(exists, bool) and exists:
                intel.business.has_blog = True
                break
    
    async def _check_page_exists(
        self, 
        url: str, 
        client: httpx.AsyncClient
    ) -> bool:
        """
        Check if a page exists (returns 200).
        
        Uses HEAD request first for efficiency, falls back to GET if needed.
        
        Args:
            url: Full URL to check
            client: HTTP client
            
        Returns:
            True if page exists and returns 200
        """
        async with self.semaphore:
            try:
                # Try HEAD request first (faster)
                response = await client.head(
                    url, 
                    follow_redirects=True, 
                    timeout=self.timeout
                )
                
                # Some servers don't support HEAD, try GET
                if response.status_code == 405:  # Method Not Allowed
                    response = await client.get(
                        url,
                        follow_redirects=True,
                        timeout=self.timeout
                    )
                
                return response.status_code == 200
                
            except httpx.TimeoutException:
                return False
            except httpx.ConnectError:
                return False
            except httpx.TooManyRedirects:
                return False
            except httpx.HTTPStatusError:
                return False
            except Exception:
                return False
    
    async def check_specific_pages(
        self,
        base_url: str,
        paths: List[str],
        client: httpx.AsyncClient
    ) -> Dict[str, bool]:
        """
        Check specific pages and return results.
        
        This is useful for custom page checking outside the standard set.
        
        Args:
            base_url: Base URL (e.g., "https://example.com")
            paths: List of paths to check
            client: HTTP client
            
        Returns:
            Dictionary mapping path to existence boolean
        """
        tasks = [
            self._check_page_exists(f"{base_url}{path}", client)
            for path in paths
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            path: (isinstance(result, bool) and result)
            for path, result in zip(paths, results)
        }
    
    async def check_sitemap_content(
        self,
        base_url: str,
        client: httpx.AsyncClient
    ) -> Optional[Dict]:
        """
        Check sitemap and extract basic information.
        
        Args:
            base_url: Base URL
            client: HTTP client
            
        Returns:
            Dictionary with sitemap info or None if not found
        """
        sitemap_urls = [
            f"{base_url}/sitemap.xml",
            f"{base_url}/sitemap_index.xml",
            f"{base_url}/sitemap-index.xml",
        ]
        
        for sitemap_url in sitemap_urls:
            try:
                async with self.semaphore:
                    response = await client.get(
                        sitemap_url,
                        follow_redirects=True,
                        timeout=self.timeout
                    )
                
                if response.status_code == 200:
                    content = response.text
                    
                    # Try to parse XML
                    try:
                        root = ElementTree.fromstring(content)
                        
                        # Count URLs in sitemap
                        # Handle namespace
                        namespace = ''
                        if root.tag.startswith('{'):
                            namespace = root.tag.split('}')[0] + '}'
                        
                        url_count = len(root.findall(f'.//{namespace}url'))
                        sitemap_count = len(root.findall(f'.//{namespace}sitemap'))
                        
                        return {
                            'url': sitemap_url,
                            'is_index': sitemap_count > 0,
                            'url_count': url_count,
                            'sitemap_count': sitemap_count,
                            'size_bytes': len(content),
                        }
                        
                    except ElementTree.ParseError:
                        # Not valid XML, but file exists
                        return {
                            'url': sitemap_url,
                            'is_index': False,
                            'url_count': 0,
                            'sitemap_count': 0,
                            'size_bytes': len(content),
                            'parse_error': True,
                        }
                        
            except Exception:
                continue
        
        return None
    
    async def check_robots_content(
        self,
        base_url: str,
        client: httpx.AsyncClient
    ) -> Optional[Dict]:
        """
        Check robots.txt and extract basic information.
        
        Args:
            base_url: Base URL
            client: HTTP client
            
        Returns:
            Dictionary with robots.txt info or None if not found
        """
        robots_url = f"{base_url}/robots.txt"
        
        try:
            async with self.semaphore:
                response = await client.get(
                    robots_url,
                    follow_redirects=True,
                    timeout=self.timeout
                )
            
            if response.status_code == 200:
                content = response.text.lower()
                
                # Extract basic information
                has_sitemap = 'sitemap:' in content
                has_disallow = 'disallow:' in content
                has_allow = 'allow:' in content
                
                # Count user-agent blocks
                user_agents = content.count('user-agent:')
                
                # Check for common bot rules
                blocks_all = 'disallow: /' in content and 'user-agent: *' in content
                
                # Extract sitemap URLs
                sitemap_urls = []
                for line in content.split('\n'):
                    if line.strip().startswith('sitemap:'):
                        sitemap_url = line.split(':', 1)[1].strip()
                        sitemap_urls.append(sitemap_url)
                
                return {
                    'url': robots_url,
                    'has_sitemap_reference': has_sitemap,
                    'has_disallow_rules': has_disallow,
                    'has_allow_rules': has_allow,
                    'user_agent_count': user_agents,
                    'blocks_all_bots': blocks_all,
                    'sitemap_urls': sitemap_urls,
                    'size_bytes': len(content),
                }
                
        except Exception:
            pass
        
        return None
    
    async def check_careers_page(
        self,
        base_url: str,
        client: httpx.AsyncClient
    ) -> bool:
        """
        Check if website has a careers/jobs page.
        
        Args:
            base_url: Base URL
            client: HTTP client
            
        Returns:
            True if careers page exists
        """
        results = await self.check_specific_pages(base_url, self.CAREERS_PATHS, client)
        return any(results.values())
    
    async def check_support_page(
        self,
        base_url: str,
        client: httpx.AsyncClient
    ) -> bool:
        """
        Check if website has a support/help page.
        
        Args:
            base_url: Base URL
            client: HTTP client
            
        Returns:
            True if support page exists
        """
        results = await self.check_specific_pages(base_url, self.SUPPORT_PATHS, client)
        return any(results.values())
    
    async def check_ecommerce_pages(
        self,
        base_url: str,
        client: httpx.AsyncClient
    ) -> bool:
        """
        Check if website appears to be an e-commerce site.
        
        Args:
            base_url: Base URL
            client: HTTP client
            
        Returns:
            True if e-commerce pages exist
        """
        results = await self.check_specific_pages(base_url, self.ECOMMERCE_PATHS, client)
        return any(results.values())
    
    async def get_comprehensive_page_info(
        self,
        domain: str,
        client: httpx.AsyncClient
    ) -> Dict:
        """
        Get comprehensive information about all pages.
        
        This is useful for detailed analysis outside the main pipeline.
        
        Args:
            domain: Website domain
            client: HTTP client
            
        Returns:
            Dictionary with all page check results
        """
        base_url = f"https://{domain}"
        
        # Run all checks
        main_pages_task = self.check_specific_pages(
            base_url, 
            list(self.PAGES_TO_CHECK.keys()), 
            client
        )
        blog_task = self.check_specific_pages(base_url, self.BLOG_PATHS, client)
        careers_task = self.check_specific_pages(base_url, self.CAREERS_PATHS, client)
        support_task = self.check_specific_pages(base_url, self.SUPPORT_PATHS, client)
        ecommerce_task = self.check_specific_pages(base_url, self.ECOMMERCE_PATHS, client)
        sitemap_task = self.check_sitemap_content(base_url, client)
        robots_task = self.check_robots_content(base_url, client)
        
        results = await asyncio.gather(
            main_pages_task,
            blog_task,
            careers_task,
            support_task,
            ecommerce_task,
            sitemap_task,
            robots_task,
            return_exceptions=True
        )
        
        main_pages, blog_pages, careers_pages, support_pages, ecommerce_pages, sitemap_info, robots_info = results
        
        # Handle exceptions
        if isinstance(main_pages, Exception):
            main_pages = {}
        if isinstance(blog_pages, Exception):
            blog_pages = {}
        if isinstance(careers_pages, Exception):
            careers_pages = {}
        if isinstance(support_pages, Exception):
            support_pages = {}
        if isinstance(ecommerce_pages, Exception):
            ecommerce_pages = {}
        if isinstance(sitemap_info, Exception):
            sitemap_info = None
        if isinstance(robots_info, Exception):
            robots_info = None
        
        # Organize results by category
        return {
            'domain': domain,
            'base_url': base_url,
            'contact': {
                'found': any(
                    main_pages.get(p, False) 
                    for p in ['/contact', '/contact-us', '/contactus', '/get-in-touch', '/reach-us']
                ),
                'paths_checked': {
                    p: main_pages.get(p, False) 
                    for p in ['/contact', '/contact-us', '/contactus', '/get-in-touch', '/reach-us']
                },
            },
            'about': {
                'found': any(
                    main_pages.get(p, False) 
                    for p in ['/about', '/about-us', '/aboutus', '/company', '/who-we-are', '/our-story']
                ),
                'paths_checked': {
                    p: main_pages.get(p, False) 
                    for p in ['/about', '/about-us', '/aboutus', '/company', '/who-we-are', '/our-story']
                },
            },
            'pricing': {
                'found': any(
                    main_pages.get(p, False) 
                    for p in ['/pricing', '/prices', '/plans', '/packages', '/buy']
                ),
                'paths_checked': {
                    p: main_pages.get(p, False) 
                    for p in ['/pricing', '/prices', '/plans', '/packages', '/buy']
                },
            },
            'privacy_policy': {
                'found': any(
                    main_pages.get(p, False) 
                    for p in ['/privacy', '/privacy-policy', '/privacypolicy', '/privacy_policy', '/data-privacy']
                ),
                'paths_checked': {
                    p: main_pages.get(p, False) 
                    for p in ['/privacy', '/privacy-policy', '/privacypolicy', '/privacy_policy', '/data-privacy']
                },
            },
            'terms_of_service': {
                'found': any(
                    main_pages.get(p, False) 
                    for p in ['/terms', '/terms-of-service', '/terms-and-conditions', '/termsofservice', '/tos', '/legal', '/terms-of-use']
                ),
                'paths_checked': {
                    p: main_pages.get(p, False) 
                    for p in ['/terms', '/terms-of-service', '/terms-and-conditions', '/termsofservice', '/tos', '/legal', '/terms-of-use']
                },
            },
            'blog': {
                'found': any(blog_pages.values()),
                'paths_checked': blog_pages,
            },
            'careers': {
                'found': any(careers_pages.values()),
                'paths_checked': careers_pages,
            },
            'support': {
                'found': any(support_pages.values()),
                'paths_checked': support_pages,
            },
            'ecommerce': {
                'found': any(ecommerce_pages.values()),
                'paths_checked': ecommerce_pages,
            },
            'sitemap': sitemap_info,
            'robots_txt': robots_info,
            'summary': {
                'has_contact': any(
                    main_pages.get(p, False) 
                    for p in ['/contact', '/contact-us', '/contactus', '/get-in-touch', '/reach-us']
                ),
                'has_about': any(
                    main_pages.get(p, False) 
                    for p in ['/about', '/about-us', '/aboutus', '/company', '/who-we-are', '/our-story']
                ),
                'has_pricing': any(
                    main_pages.get(p, False) 
                    for p in ['/pricing', '/prices', '/plans', '/packages', '/buy']
                ),
                'has_privacy': any(
                    main_pages.get(p, False) 
                    for p in ['/privacy', '/privacy-policy', '/privacypolicy', '/privacy_policy', '/data-privacy']
                ),
                'has_terms': any(
                    main_pages.get(p, False) 
                    for p in ['/terms', '/terms-of-service', '/terms-and-conditions', '/termsofservice', '/tos', '/legal', '/terms-of-use']
                ),
                'has_blog': any(blog_pages.values()),
                'has_careers': any(careers_pages.values()),
                'has_support': any(support_pages.values()),
                'is_ecommerce': any(ecommerce_pages.values()),
                'has_sitemap': sitemap_info is not None,
                'has_robots': robots_info is not None,
            },
        }
    
    def get_page_categories(self) -> Dict[str, List[str]]:
        """
        Get all page categories and their paths.
        
        Returns:
            Dictionary mapping category to list of paths
        """
        return {
            'contact': ['/contact', '/contact-us', '/contactus', '/get-in-touch', '/reach-us'],
            'about': ['/about', '/about-us', '/aboutus', '/company', '/who-we-are', '/our-story'],
            'pricing': ['/pricing', '/prices', '/plans', '/packages', '/buy'],
            'privacy': ['/privacy', '/privacy-policy', '/privacypolicy', '/privacy_policy', '/data-privacy'],
            'terms': ['/terms', '/terms-of-service', '/terms-and-conditions', '/termsofservice', '/tos', '/legal', '/terms-of-use'],
            'seo': ['/sitemap.xml', '/sitemap', '/sitemap_index.xml', '/sitemap-index.xml', '/robots.txt'],
            'blog': self.BLOG_PATHS,
            'careers': self.CAREERS_PATHS,
            'support': self.SUPPORT_PATHS,
            'ecommerce': self.ECOMMERCE_PATHS,
        }