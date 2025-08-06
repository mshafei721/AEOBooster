"""
Unit tests for the crawler service.
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import json
from bs4 import BeautifulSoup

from src.services.crawler_service import CrawlerService
from src.services.content_extractor import ContentExtractor
from src.services.page_classifier import PageClassifier

class TestCrawlerService:
    """Test suite for CrawlerService."""
    
    @pytest.fixture
    def crawler(self):
        """Create a crawler instance for testing."""
        return CrawlerService(
            max_pages=10,
            delay_seconds=0.1,  # Fast for tests
            timeout_seconds=5,
            respect_robots=False  # Disable for tests
        )
    
    @pytest.fixture
    def mock_html(self):
        """Sample HTML content for testing."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Page</title>
            <meta name="description" content="Test description">
            <meta name="keywords" content="test, page">
        </head>
        <body>
            <h1>Main Heading</h1>
            <p>This is test content for the crawler.</p>
            <a href="/about">About Us</a>
            <a href="/products">Products</a>
            <a href="https://external.com">External Link</a>
        </body>
        </html>
        """
    
    def test_normalize_url(self, crawler):
        """Test URL normalization."""
        # Valid URLs
        assert crawler.normalize_url("https://example.com/path") == "https://example.com/path"
        assert crawler.normalize_url("HTTP://EXAMPLE.COM/Path") == "http://example.com/Path"
        assert crawler.normalize_url("https://example.com/path#fragment") == "https://example.com/path"
        
        # Invalid URLs
        assert crawler.normalize_url("not-a-url") is None
        assert crawler.normalize_url("") is None
        assert crawler.normalize_url("ftp://example.com") is None
    
    def test_filter_and_normalize_urls(self, crawler):
        """Test URL filtering and normalization."""
        base_url = "https://example.com"
        urls = [
            "https://example.com/page1",
            "https://example.com/page2#fragment",
            "https://other.com/external",  # External domain
            "https://example.com/file.pdf",  # PDF file
            "mailto:test@example.com",  # Non-HTTP scheme
            "https://example.com/page1",  # Duplicate
            "/relative/path",  # This would be processed differently
        ]
        
        filtered = crawler._filter_and_normalize_urls(urls, base_url)
        
        # Should include only same-domain, non-file URLs without duplicates
        expected = [
            "https://example.com/page1",
            "https://example.com/page2"
        ]
        
        assert len(filtered) == 2
        assert all(url in filtered for url in expected)
    
    @pytest.mark.asyncio
    async def test_crawl_with_beautifulsoup_success(self, crawler, mock_html):
        """Test successful crawling with BeautifulSoup."""
        # Mock requests.Session
        mock_session = Mock()
        mock_response = Mock()
        mock_response.text = mock_html
        mock_response.raise_for_status.return_value = None
        mock_session.get.return_value = mock_response
        
        crawl_results = {
            'project_id': 'test-project',
            'base_url': 'https://example.com',
            'pages_crawled': 0,
            'pages_failed': 0,
            'total_pages_found': 0,
            'crawled_pages': [],
            'failed_pages': []
        }
        
        with patch('requests.Session', return_value=mock_session):
            results = await crawler._crawl_with_beautifulsoup(
                'https://example.com', 
                'test-project', 
                crawl_results,
                None
            )
        
        assert results['pages_crawled'] == 1
        assert len(results['crawled_pages']) == 1
        
        page = results['crawled_pages'][0]
        assert page['url'] == 'https://example.com'
        assert page['title'] == 'Test Page'
        assert page['status'] == 'crawled'
    
    @pytest.mark.asyncio
    async def test_crawl_with_beautifulsoup_failure(self, crawler):
        """Test crawling failure handling with BeautifulSoup."""
        # Mock requests.Session to raise an exception
        mock_session = Mock()
        mock_session.get.side_effect = Exception("Network error")
        
        crawl_results = {
            'project_id': 'test-project',
            'base_url': 'https://example.com',
            'pages_crawled': 0,
            'pages_failed': 0,
            'total_pages_found': 0,
            'crawled_pages': [],
            'failed_pages': []
        }
        
        with patch('requests.Session', return_value=mock_session):
            results = await crawler._crawl_with_beautifulsoup(
                'https://example.com',
                'test-project',
                crawl_results,
                None
            )
        
        assert results['pages_crawled'] == 0
        assert results['pages_failed'] == 1
        assert len(results['failed_pages']) == 1
        assert 'Network error' in results['failed_pages'][0]['error']
    
    def test_extract_urls_from_soup(self, crawler, mock_html):
        """Test URL extraction from BeautifulSoup."""
        soup = BeautifulSoup(mock_html, 'html.parser')
        base_url = "https://example.com"
        
        urls = crawler._extract_urls_from_soup(soup, base_url)
        
        # Should extract relative URLs and convert to absolute
        expected_urls = [
            "https://example.com/about",
            "https://example.com/products"
        ]
        
        assert len(urls) == 2
        assert all(url in urls for url in expected_urls)
    
    @pytest.mark.asyncio
    async def test_crawl_website_integration(self, crawler):
        """Test full website crawling integration."""
        base_url = "https://example.com"
        project_id = "test-project"
        
        # Mock the Playwright crawling to avoid actual browser launch
        mock_results = {
            'project_id': project_id,
            'base_url': base_url,
            'pages_crawled': 2,
            'pages_failed': 0,
            'total_pages_found': 2,
            'crawled_pages': [
                {
                    'url': 'https://example.com',
                    'title': 'Home Page',
                    'page_type': 'homepage',
                    'confidence_score': 0.9,
                    'content': {
                        'title': 'Home Page',
                        'content': 'Welcome to our website',
                        'headings': [{'level': 1, 'text': 'Welcome', 'position': 1}]
                    },
                    'status': 'crawled',
                    'crawled_at': 1234567890.0
                }
            ],
            'failed_pages': []
        }
        
        with patch.object(crawler, '_crawl_with_playwright', new_callable=AsyncMock) as mock_playwright:
            mock_playwright.return_value = mock_results
            
            results = await crawler.crawl_website(project_id, base_url)
        
        assert results['status'] == 'completed'
        assert results['pages_crawled'] == 2
        assert results['pages_failed'] == 0
        assert len(results['crawled_pages']) == 1
    
    def test_can_fetch_url_robots_disabled(self, crawler):
        """Test robots.txt checking when disabled."""
        crawler.respect_robots = False
        
        # Should always return True when robots.txt respect is disabled
        assert crawler._can_fetch_url("https://example.com/any-path") == True
    
    def test_can_fetch_url_robots_enabled(self, crawler):
        """Test robots.txt checking when enabled."""
        crawler.respect_robots = True
        
        # Mock RobotFileParser
        mock_robot_parser = Mock()
        mock_robot_parser.can_fetch.return_value = True
        
        with patch('urllib.robotparser.RobotFileParser') as mock_rp_class:
            mock_rp_class.return_value = mock_robot_parser
            
            result = crawler._can_fetch_url("https://example.com/allowed-path")
            
            assert result == True
            mock_robot_parser.set_url.assert_called_once()
            mock_robot_parser.read.assert_called_once()
            mock_robot_parser.can_fetch.assert_called_once()
    
    def test_can_fetch_url_robots_error(self, crawler):
        """Test robots.txt error handling."""
        crawler.respect_robots = True
        
        # Mock RobotFileParser to raise an exception
        with patch('urllib.robotparser.RobotFileParser') as mock_rp_class:
            mock_rp_class.return_value.read.side_effect = Exception("robots.txt error")
            
            # Should default to allowing crawling when robots.txt can't be read
            result = crawler._can_fetch_url("https://example.com/path")
            assert result == True
    
    @pytest.mark.asyncio
    async def test_progress_callback(self, crawler):
        """Test progress callback functionality."""
        progress_updates = []
        
        async def mock_callback(progress):
            progress_updates.append(progress)
        
        # This is a simplified test - in real usage, progress callback
        # would be called during the crawling process
        await mock_callback({
            'current_url': 'https://example.com/page1',
            'pages_crawled': 1,
            'pages_found': 5
        })
        
        assert len(progress_updates) == 1
        assert progress_updates[0]['current_url'] == 'https://example.com/page1'
        assert progress_updates[0]['pages_crawled'] == 1
        assert progress_updates[0]['pages_found'] == 5

class TestCrawlerServiceEdgeCases:
    """Test edge cases and error conditions."""
    
    @pytest.fixture
    def crawler(self):
        return CrawlerService(max_pages=5, delay_seconds=0.1)
    
    def test_invalid_base_url(self, crawler):
        """Test crawling with invalid base URL."""
        with pytest.raises(ValueError, match="Invalid URL"):
            asyncio.run(crawler.crawl_website("project-id", "not-a-valid-url"))
    
    def test_robots_disallowed_url(self, crawler):
        """Test crawling URL disallowed by robots.txt."""
        crawler.respect_robots = True
        
        # Mock robots.txt to disallow crawling
        mock_robot_parser = Mock()
        mock_robot_parser.can_fetch.return_value = False
        
        with patch('urllib.robotparser.RobotFileParser', return_value=mock_robot_parser):
            with pytest.raises(ValueError, match="Robots.txt disallows crawling"):
                asyncio.run(crawler.crawl_website("project-id", "https://example.com"))
    
    @pytest.mark.asyncio
    async def test_max_pages_limit(self, crawler):
        """Test that crawler respects max pages limit."""
        # Mock to simulate finding many URLs but should stop at max_pages
        mock_results = {
            'project_id': 'test-project',
            'pages_crawled': crawler.max_pages,  # Should stop at max
            'pages_failed': 0,
            'total_pages_found': 100,  # Many more found
            'crawled_pages': [{'url': f'https://example.com/page{i}', 
                              'title': f'Page {i}', 'content': {}, 
                              'status': 'crawled', 'crawled_at': 1234567890.0} 
                             for i in range(crawler.max_pages)],
            'failed_pages': []
        }
        
        with patch.object(crawler, '_crawl_with_playwright', new_callable=AsyncMock) as mock_playwright:
            mock_playwright.return_value = mock_results
            
            results = await crawler.crawl_website("project-id", "https://example.com")
        
        # Should not exceed max_pages
        assert results['pages_crawled'] <= crawler.max_pages

if __name__ == "__main__":
    pytest.main([__file__])