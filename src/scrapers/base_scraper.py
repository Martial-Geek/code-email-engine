"""Base scraper class with robust measurement capabilities."""

import asyncio
import time
from typing import List, Optional, Tuple

import httpx

from .models.website_intelligence import WebsiteIntelligence
from .analyzers.html_analyzer import HTMLAnalyzer
from .analyzers.page_checker import PageChecker

# Import settings - adjust path as needed for your project
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    from config.settings import REQUEST_TIMEOUT, MAX_CONCURRENT_REQUESTS, USER_AGENT
except ImportError:
    # Default values if settings not available
    REQUEST_TIMEOUT = 30
    MAX_CONCURRENT_REQUESTS = 10
    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )


class RobustWebsiteScraper:
    """
    Async website analyzer with statistical robustness.
    Performs multiple measurements and uses robust statistics.
    """
    
    DEFAULT_HEADERS = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    def __init__(
        self, 
        max_concurrent: int = MAX_CONCURRENT_REQUESTS,
        measurement_rounds: int = 3,
        measurement_delay: float = 0.5,
        timeout: float = REQUEST_TIMEOUT,
        user_agent: str = USER_AGENT
    ):
        """
        Initialize the scraper.
        
        Args:
            max_concurrent: Maximum concurrent requests
            measurement_rounds: Number of times to measure each site
            measurement_delay: Delay between measurements in seconds
            timeout: Request timeout in seconds
            user_agent: User agent string
        """
        self.max_concurrent = max_concurrent
        self.measurement_rounds = measurement_rounds
        self.measurement_delay = measurement_delay
        self.timeout = timeout
        self.semaphore = asyncio.Semaphore(max_concurrent)
        
        self.headers = {**self.DEFAULT_HEADERS, 'User-Agent': user_agent}
        
        # Initialize analyzers
        self.html_analyzer = HTMLAnalyzer()
        self.page_checker = PageChecker()
    
    async def analyze_website(
        self, 
        domain: str, 
        client: httpx.AsyncClient
    ) -> WebsiteIntelligence:
        """
        Analyze a single website with multiple measurements.
        
        Args:
            domain: Website domain to analyze
            client: HTTP client
            
        Returns:
            WebsiteIntelligence object with analysis results
        """
        intel = WebsiteIntelligence(
            domain=domain,
            analysis_timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
        )
        
        async with self.semaphore:
            # Perform load time measurements and get content
            html_content, response_headers, working_url = await self._fetch_with_measurements(
                domain, client, intel
            )
            
            # Parse HTML content
            if html_content:
                self.html_analyzer.analyze(html_content, intel)
            
            # Parse security headers
            if response_headers:
                self._parse_security_headers(response_headers, intel)
            
            # Check additional pages
            if working_url:
                await self.page_checker.check_pages(domain, client, intel)
            
            # Calculate all scores
            intel.calculate_overall_scores()
        
        return intel
    
    async def _fetch_with_measurements(
        self,
        domain: str,
        client: httpx.AsyncClient,
        intel: WebsiteIntelligence
    ) -> Tuple[Optional[str], Optional[httpx.Headers], Optional[str]]:
        """
        Fetch website with multiple load time measurements.
        
        Returns:
            Tuple of (html_content, response_headers, working_url)
        """
        load_times: List[float] = []
        html_content: Optional[str] = None
        response_headers: Optional[httpx.Headers] = None
        working_url: Optional[str] = None
        
        urls_to_try = [f"https://{domain}", f"http://{domain}"]
        
        for url in urls_to_try:
            try:
                # First request to establish connection and get content
                start_time = time.time()
                response = await client.get(
                    url, 
                    follow_redirects=True,
                    timeout=self.timeout
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
                                timeout=self.timeout
                            )
                            load_times.append(time.time() - start_time)
                        except Exception:
                            pass  # Don't fail if subsequent measurements fail
                    
                    break
                else:
                    # Non-200 status code
                    intel.status_code = response.status_code
                    intel.final_url = str(response.url)
                    
            except httpx.TimeoutException:
                intel.error = "timeout"
            except httpx.ConnectError:
                intel.error = "connection_failed"
            except httpx.TooManyRedirects:
                intel.error = "too_many_redirects"
            except httpx.HTTPStatusError as e:
                intel.error = f"http_error_{e.response.status_code}"
                intel.status_code = e.response.status_code
            except Exception as e:
                intel.error = str(e)[:100]
        
        # Calculate load time statistics
        if load_times:
            intel.performance.load_time_metrics.samples = [
                round(t, 3) for t in load_times
            ]
            intel.performance.load_time_metrics.calculate()
        
        return html_content, response_headers, working_url
    
    def _parse_security_headers(
        self, 
        headers: httpx.Headers, 
        intel: WebsiteIntelligence
    ) -> None:
        """Parse security-related headers."""
        security = intel.security
        
        # Convert header names to lowercase for comparison
        header_names = [h.lower() for h in headers.keys()]
        
        security.has_hsts = 'strict-transport-security' in header_names
        security.has_csp = 'content-security-policy' in header_names
        security.has_x_frame_options = 'x-frame-options' in header_names
        security.has_x_content_type_options = 'x-content-type-options' in header_names
        security.has_x_xss_protection = 'x-xss-protection' in header_names
    
    async def analyze_batch(
        self, 
        domains: List[str],
        show_progress: bool = True
    ) -> List[WebsiteIntelligence]:
        """
        Analyze multiple websites concurrently.
        
        Args:
            domains: List of domains to analyze
            show_progress: Whether to show progress bar
            
        Returns:
            List of WebsiteIntelligence objects
        """
        results: List[WebsiteIntelligence] = []
        
        async with httpx.AsyncClient(
            headers=self.headers, 
            http2=True,
            follow_redirects=True,
            timeout=self.timeout
        ) as client:
            if show_progress:
                results = await self._process_with_progress(domains, client)
            else:
                results = await self._process_batch(domains, client)
        
        return results
    
    async def _process_with_progress(
        self,
        domains: List[str],
        client: httpx.AsyncClient
    ) -> List[WebsiteIntelligence]:
        """Process domains with progress bar."""
        results: List[WebsiteIntelligence] = []
        
        try:
            from rich.progress import (
                Progress, SpinnerColumn, TextColumn, BarColumn, 
                TaskProgressColumn, TimeRemainingColumn
            )
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TimeRemainingColumn(),
            ) as progress:
                task = progress.add_task(
                    "[cyan]Analyzing websites...", 
                    total=len(domains)
                )
                
                batch_size = self.max_concurrent * 2
                
                for i in range(0, len(domains), batch_size):
                    batch = domains[i:i + batch_size]
                    tasks = [
                        self.analyze_website(domain, client) 
                        for domain in batch
                    ]
                    batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    for result in batch_results:
                        if isinstance(result, WebsiteIntelligence):
                            results.append(result)
                        elif isinstance(result, Exception):
                            # Create error result for failed analyses
                            # We don't have domain info here, so skip
                            pass
                    
                    progress.update(task, advance=len(batch))
                    
        except ImportError:
            # Rich not available, process without progress
            results = await self._process_batch(domains, client)
        
        return results
    
    async def _process_batch(
        self,
        domains: List[str],
        client: httpx.AsyncClient
    ) -> List[WebsiteIntelligence]:
        """Process domains without progress bar."""
        results: List[WebsiteIntelligence] = []
        
        batch_size = self.max_concurrent * 2
        
        for i in range(0, len(domains), batch_size):
            batch = domains[i:i + batch_size]
            tasks = [
                self.analyze_website(domain, client) 
                for domain in batch
            ]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, WebsiteIntelligence):
                    results.append(result)
        
        return results
    
    async def analyze_single(self, domain: str) -> WebsiteIntelligence:
        """
        Analyze a single website (convenience method).
        
        Args:
            domain: Domain to analyze
            
        Returns:
            WebsiteIntelligence object
        """
        async with httpx.AsyncClient(
            headers=self.headers,
            http2=True,
            follow_redirects=True,
            timeout=self.timeout
        ) as client:
            return await self.analyze_website(domain, client)
    
    def analyze_single_sync(self, domain: str) -> WebsiteIntelligence:
        """
        Synchronous wrapper for analyzing a single website.
        
        Args:
            domain: Domain to analyze
            
        Returns:
            WebsiteIntelligence object
        """
        return asyncio.run(self.analyze_single(domain))
    
    def analyze_batch_sync(
        self, 
        domains: List[str],
        show_progress: bool = True
    ) -> List[WebsiteIntelligence]:
        """
        Synchronous wrapper for batch analysis.
        
        Args:
            domains: List of domains to analyze
            show_progress: Whether to show progress
            
        Returns:
            List of WebsiteIntelligence objects
        """
        return asyncio.run(self.analyze_batch(domains, show_progress))