"""
Website crawler service with Playwright primary engine and BeautifulSoup fallback.
"""
import asyncio
import logging
import re
import time
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse, urlunparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Page, Browser, TimeoutError

from .content_extractor import ContentExtractor
from .page_classifier import PageClassifier

logger = logging.getLogger(__name__)

class CrawlerService:
    """Main crawler service with Playwright and BeautifulSoup engines."""
    
    def __init__(self, 
                 max_pages: int = 50,
                 delay_seconds: float = 1.0,
                 timeout_seconds: int = 30,
                 respect_robots: bool = True):
        """
        Initialize crawler service.
        
        Args:
            max_pages: Maximum number of pages to crawl
            delay_seconds: Delay between requests
            timeout_seconds: Request timeout
            respect_robots: Whether to respect robots.txt
        """
        self.max_pages = max_pages
        self.delay_seconds = delay_seconds
        self.timeout_seconds = timeout_seconds
        self.respect_robots = respect_robots
        
        self.content_extractor = ContentExtractor()
        self.page_classifier = PageClassifier()
        
        # Track crawled URLs to avoid duplicates
        self.crawled_urls: Set[str] = set()
        self.failed_urls: Set[str] = set()
        self.robots_cache: Dict[str, RobotFileParser] = {}
        
    async def crawl_website(self, 
                           project_id: str, 
                           base_url: str,
                           progress_callback=None) -> Dict:
        """
        Crawl a website starting from base_url.
        
        Args:
            project_id: Project ID to associate crawled content
            base_url: Starting URL to crawl
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dict with crawling results and statistics
        """
        logger.info(f"Starting crawl for project {project_id} at {base_url}")
        
        # Normalize and validate base URL
        normalized_url = self.normalize_url(base_url)
        if not normalized_url:
            raise ValueError(f"Invalid URL: {base_url}")
            
        # Check robots.txt if enabled
        if self.respect_robots and not self._can_fetch_url(normalized_url):
            raise ValueError(f"Robots.txt disallows crawling: {normalized_url}")
        
        crawl_results = {
            'project_id': project_id,
            'base_url': normalized_url,
            'pages_crawled': 0,
            'pages_failed': 0,
            'total_pages_found': 0,
            'crawled_pages': [],
            'failed_pages': [],
            'started_at': time.time(),
            'completed_at': None,
            'status': 'running'
        }
        
        try:
            # Start with Playwright for JavaScript-heavy sites
            async with async_playwright() as p:
                browser = await p.chromium.launch()
                try:
                    results = await self._crawl_with_playwright(
                        browser, normalized_url, project_id, crawl_results, progress_callback
                    )
                    crawl_results.update(results)
                finally:
                    await browser.close()
                    
        except Exception as e:
            logger.error(f"Playwright crawling failed, trying BeautifulSoup fallback: {e}")
            # Fallback to BeautifulSoup
            results = await self._crawl_with_beautifulsoup(
                normalized_url, project_id, crawl_results, progress_callback
            )
            crawl_results.update(results)
        
        crawl_results['completed_at'] = time.time()
        crawl_results['status'] = 'completed'
        
        logger.info(f"Crawl completed. Pages: {crawl_results['pages_crawled']}, "
                   f"Failed: {crawl_results['pages_failed']}")
        
        return crawl_results
    
    async def _crawl_with_playwright(self, 
                                   browser: Browser, 
                                   base_url: str, 
                                   project_id: str,
                                   crawl_results: Dict,
                                   progress_callback) -> Dict:
        """Crawl using Playwright for JavaScript-rendered content."""
        
        page = await browser.new_page()
        urls_to_crawl = [base_url]
        
        try:
            while urls_to_crawl and crawl_results['pages_crawled'] < self.max_pages:
                current_url = urls_to_crawl.pop(0)
                
                if current_url in self.crawled_urls or current_url in self.failed_urls:
                    continue
                
                # Check robots.txt
                if self.respect_robots and not self._can_fetch_url(current_url):
                    continue
                
                try:
                    # Navigate to page with timeout
                    await page.goto(current_url, timeout=self.timeout_seconds * 1000)
                    await page.wait_for_load_state('networkidle', timeout=10000)
                    
                    # Get page content
                    content = await page.content()
                    title = await page.title()
                    
                    # Extract and classify content
                    extracted_content = self.content_extractor.extract_content(content, current_url)
                    page_type, confidence = self.page_classifier.classify_page(
                        current_url, extracted_content['title'], extracted_content['content']
                    )
                    
                    # Store crawled page data
                    page_data = {
                        'url': current_url,
                        'title': title,
                        'page_type': page_type,
                        'confidence_score': confidence,
                        'content': extracted_content,
                        'status': 'crawled',
                        'crawled_at': time.time()
                    }
                    
                    crawl_results['crawled_pages'].append(page_data)
                    self.crawled_urls.add(current_url)
                    crawl_results['pages_crawled'] += 1
                    
                    # Find more URLs to crawl from this page
                    new_urls = await self._extract_urls_from_page(page, base_url)
                    for url in new_urls:
                        if (url not in self.crawled_urls and 
                            url not in self.failed_urls and 
                            url not in urls_to_crawl):
                            urls_to_crawl.append(url)
                    
                    crawl_results['total_pages_found'] = len(urls_to_crawl) + crawl_results['pages_crawled']
                    
                    # Progress callback
                    if progress_callback:
                        await progress_callback({
                            'current_url': current_url,
                            'pages_crawled': crawl_results['pages_crawled'],
                            'pages_found': crawl_results['total_pages_found']
                        })
                    
                    # Respectful delay
                    await asyncio.sleep(self.delay_seconds)
                    
                except TimeoutError:
                    logger.warning(f"Timeout crawling {current_url}")
                    self.failed_urls.add(current_url)
                    crawl_results['failed_pages'].append({
                        'url': current_url, 
                        'error': 'timeout',
                        'failed_at': time.time()
                    })
                    crawl_results['pages_failed'] += 1
                    
                except Exception as e:
                    logger.error(f"Error crawling {current_url}: {e}")
                    self.failed_urls.add(current_url)
                    crawl_results['failed_pages'].append({
                        'url': current_url, 
                        'error': str(e),
                        'failed_at': time.time()
                    })
                    crawl_results['pages_failed'] += 1
        
        finally:
            await page.close()
            
        return crawl_results
    
    async def _crawl_with_beautifulsoup(self, 
                                      base_url: str, 
                                      project_id: str,
                                      crawl_results: Dict,
                                      progress_callback) -> Dict:
        """Fallback crawling with BeautifulSoup for static content."""
        
        urls_to_crawl = [base_url]
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; AEOBooster/1.0; +https://aeobooster.com)'
        })
        
        while urls_to_crawl and crawl_results['pages_crawled'] < self.max_pages:
            current_url = urls_to_crawl.pop(0)
            
            if current_url in self.crawled_urls or current_url in self.failed_urls:
                continue
            
            # Check robots.txt
            if self.respect_robots and not self._can_fetch_url(current_url):
                continue
            
            try:
                response = session.get(current_url, timeout=self.timeout_seconds)
                response.raise_for_status()
                
                # Extract and classify content
                extracted_content = self.content_extractor.extract_content(response.text, current_url)
                page_type, confidence = self.page_classifier.classify_page(
                    current_url, extracted_content['title'], extracted_content['content']
                )
                
                # Store crawled page data
                page_data = {
                    'url': current_url,
                    'title': extracted_content['title'],
                    'page_type': page_type,
                    'confidence_score': confidence,
                    'content': extracted_content,
                    'status': 'crawled',
                    'crawled_at': time.time()
                }
                
                crawl_results['crawled_pages'].append(page_data)
                self.crawled_urls.add(current_url)
                crawl_results['pages_crawled'] += 1
                
                # Find more URLs to crawl
                soup = BeautifulSoup(response.text, 'html.parser')
                new_urls = self._extract_urls_from_soup(soup, base_url)
                for url in new_urls:
                    if (url not in self.crawled_urls and 
                        url not in self.failed_urls and 
                        url not in urls_to_crawl):
                        urls_to_crawl.append(url)
                
                crawl_results['total_pages_found'] = len(urls_to_crawl) + crawl_results['pages_crawled']
                
                # Progress callback
                if progress_callback:
                    await progress_callback({
                        'current_url': current_url,
                        'pages_crawled': crawl_results['pages_crawled'],
                        'pages_found': crawl_results['total_pages_found']
                    })
                
                # Respectful delay
                await asyncio.sleep(self.delay_seconds)
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Error crawling {current_url}: {e}")
                self.failed_urls.add(current_url)
                crawl_results['failed_pages'].append({
                    'url': current_url, 
                    'error': str(e),
                    'failed_at': time.time()
                })
                crawl_results['pages_failed'] += 1
        
        return crawl_results
    
    async def _extract_urls_from_page(self, page: Page, base_url: str) -> List[str]:
        """Extract URLs from a Playwright page."""
        try:
            links = await page.eval_on_selector_all('a[href]', 
                'elements => elements.map(el => el.href)')
            return self._filter_and_normalize_urls(links, base_url)
        except Exception as e:
            logger.error(f"Error extracting URLs from page: {e}")
            return []
    
    def _extract_urls_from_soup(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract URLs from BeautifulSoup parsed content."""
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            absolute_url = urljoin(base_url, href)
            links.append(absolute_url)
        return self._filter_and_normalize_urls(links, base_url)
    
    def _filter_and_normalize_urls(self, urls: List[str], base_url: str) -> List[str]:
        """Filter and normalize URLs to same domain."""
        base_domain = urlparse(base_url).netloc
        filtered_urls = []
        
        for url in urls:
            try:
                parsed = urlparse(url)
                
                # Only same domain
                if parsed.netloc != base_domain:
                    continue
                
                # Skip non-http schemes
                if parsed.scheme not in ['http', 'https']:
                    continue
                
                # Skip files that are unlikely to be web pages
                if parsed.path.lower().endswith(('.pdf', '.jpg', '.jpeg', '.png', '.gif', 
                                               '.css', '.js', '.xml', '.zip', '.doc', '.docx')):
                    continue
                
                # Normalize URL (remove fragment, sort query params)
                normalized = self.normalize_url(url)
                if normalized:
                    filtered_urls.append(normalized)
                    
            except Exception as e:
                logger.debug(f"Error processing URL {url}: {e}")
                continue
        
        return list(set(filtered_urls))  # Remove duplicates
    
    def normalize_url(self, url: str) -> Optional[str]:
        """Normalize URL by removing fragments and unnecessary parameters."""
        try:
            parsed = urlparse(url.strip())
            
            # Basic validation
            if not parsed.netloc or parsed.scheme not in ['http', 'https']:
                return None
            
            # Remove fragment
            normalized = urlunparse((
                parsed.scheme,
                parsed.netloc.lower(),
                parsed.path,
                parsed.params,
                parsed.query,
                ''  # Remove fragment
            ))
            
            return normalized
            
        except Exception:
            return None
    
    def _can_fetch_url(self, url: str) -> bool:
        """Check if URL can be fetched according to robots.txt."""
        try:
            parsed = urlparse(url)
            robot_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
            
            # Check cache first
            if robot_url not in self.robots_cache:
                rp = RobotFileParser()
                rp.set_url(robot_url)
                try:
                    rp.read()
                    self.robots_cache[robot_url] = rp
                except Exception:
                    # If robots.txt can't be read, allow crawling
                    self.robots_cache[robot_url] = None
                    return True
            
            rp = self.robots_cache[robot_url]
            if rp is None:
                return True
                
            # Check if our user agent can fetch this URL
            user_agent = 'Mozilla/5.0 (compatible; AEOBooster/1.0; +https://aeobooster.com)'
            return rp.can_fetch(user_agent, url)
            
        except Exception as e:
            logger.debug(f"Error checking robots.txt for {url}: {e}")
            return True  # Default to allowing if check fails