"""
Content extraction service for parsing website content and metadata.
"""
import json
import logging
import re
from typing import Dict, List, Optional, Any

from bs4 import BeautifulSoup, Comment

logger = logging.getLogger(__name__)

class ContentExtractor:
    """Extract structured content and metadata from HTML pages."""
    
    def __init__(self):
        """Initialize content extractor."""
        # Tags to remove (navigation, ads, etc.)
        self.noise_tags = [
            'nav', 'header', 'footer', 'aside', 'script', 'style', 'noscript',
            'iframe', 'form', 'input', 'button', 'select', 'textarea'
        ]
        
        # Tags that typically contain noise
        self.noise_classes = [
            'nav', 'navigation', 'menu', 'sidebar', 'footer', 'header',
            'advertisement', 'ads', 'social', 'share', 'comment', 'comments',
            'related', 'recommended', 'popup', 'modal', 'overlay'
        ]
        
        # Main content indicators
        self.main_content_indicators = [
            'main', 'content', 'article', 'post', 'entry', 'body-content',
            'page-content', 'primary', 'main-content', 'content-area'
        ]
    
    def extract_content(self, html: str, url: str) -> Dict[str, Any]:
        """
        Extract structured content from HTML.
        
        Args:
            html: Raw HTML content
            url: Page URL for context
            
        Returns:
            Dict containing extracted content and metadata
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove comments
            for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
                comment.extract()
            
            # Extract basic metadata
            title = self._extract_title(soup)
            meta_description = self._extract_meta_description(soup)
            meta_keywords = self._extract_meta_keywords(soup)
            
            # Extract structured data
            structured_data = self._extract_structured_data(soup)
            
            # Extract Open Graph and Twitter Card data
            og_data = self._extract_open_graph(soup)
            twitter_data = self._extract_twitter_card(soup)
            
            # Extract heading hierarchy
            headings = self._extract_headings(soup)
            
            # Extract main content
            main_content = self._extract_main_content(soup)
            
            # Extract images with alt text
            images = self._extract_images(soup, url)
            
            # Extract links
            links = self._extract_links(soup, url)
            
            # Calculate content metrics
            content_metrics = self._calculate_content_metrics(main_content, headings)
            
            return {
                'url': url,
                'title': title,
                'meta_description': meta_description,
                'meta_keywords': meta_keywords,
                'headings': headings,
                'content': main_content,
                'structured_data': structured_data,
                'open_graph': og_data,
                'twitter_card': twitter_data,
                'images': images,
                'links': links,
                'content_metrics': content_metrics,
                'extracted_at': None  # Will be set by caller
            }
            
        except Exception as e:
            logger.error(f"Error extracting content from {url}: {e}")
            return {
                'url': url,
                'title': '',
                'meta_description': '',
                'meta_keywords': '',
                'headings': [],
                'content': '',
                'structured_data': {},
                'open_graph': {},
                'twitter_card': {},
                'images': [],
                'links': [],
                'content_metrics': {},
                'error': str(e)
            }
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title."""
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text(strip=True)
        
        # Fallback to h1
        h1 = soup.find('h1')
        if h1:
            return h1.get_text(strip=True)
        
        return ''
    
    def _extract_meta_description(self, soup: BeautifulSoup) -> str:
        """Extract meta description."""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc['content'].strip()
        
        # Fallback to Open Graph description
        og_desc = soup.find('meta', attrs={'property': 'og:description'})
        if og_desc and og_desc.get('content'):
            return og_desc['content'].strip()
        
        return ''
    
    def _extract_meta_keywords(self, soup: BeautifulSoup) -> str:
        """Extract meta keywords."""
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords and meta_keywords.get('content'):
            return meta_keywords['content'].strip()
        return ''
    
    def _extract_structured_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract JSON-LD and microdata structured data."""
        structured_data = {}
        
        # Extract JSON-LD
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        json_ld_data = []
        
        for script in json_ld_scripts:
            try:
                data = json.loads(script.string)
                json_ld_data.append(data)
            except (json.JSONDecodeError, AttributeError) as e:
                logger.debug(f"Error parsing JSON-LD: {e}")
                continue
        
        if json_ld_data:
            structured_data['json_ld'] = json_ld_data
        
        # Extract microdata (basic extraction)
        microdata_items = soup.find_all(attrs={'itemscope': True})
        microdata = []
        
        for item in microdata_items:
            item_type = item.get('itemtype', '')
            item_data = {'type': item_type, 'properties': {}}
            
            # Find properties within this item
            props = item.find_all(attrs={'itemprop': True})
            for prop in props:
                prop_name = prop.get('itemprop')
                prop_value = self._extract_microdata_value(prop)
                if prop_name and prop_value:
                    item_data['properties'][prop_name] = prop_value
            
            if item_data['properties']:
                microdata.append(item_data)
        
        if microdata:
            structured_data['microdata'] = microdata
        
        return structured_data
    
    def _extract_microdata_value(self, element) -> str:
        """Extract value from microdata property element."""
        # Check for specific attributes first
        if element.get('content'):
            return element['content']
        if element.get('datetime'):
            return element['datetime']
        if element.get('href'):
            return element['href']
        if element.get('src'):
            return element['src']
        
        # Otherwise return text content
        return element.get_text(strip=True)
    
    def _extract_open_graph(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract Open Graph metadata."""
        og_data = {}
        og_tags = soup.find_all('meta', attrs={'property': re.compile(r'^og:')})
        
        for tag in og_tags:
            property_name = tag.get('property', '').replace('og:', '')
            content = tag.get('content', '')
            if property_name and content:
                og_data[property_name] = content
        
        return og_data
    
    def _extract_twitter_card(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract Twitter Card metadata."""
        twitter_data = {}
        twitter_tags = soup.find_all('meta', attrs={'name': re.compile(r'^twitter:')})
        
        for tag in twitter_tags:
            name = tag.get('name', '').replace('twitter:', '')
            content = tag.get('content', '')
            if name and content:
                twitter_data[name] = content
        
        return twitter_data
    
    def _extract_headings(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract heading hierarchy."""
        headings = []
        heading_tags = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        
        for i, heading in enumerate(heading_tags):
            text = heading.get_text(strip=True)
            if text:  # Only include non-empty headings
                headings.append({
                    'level': int(heading.name[1]),  # h1 -> 1, h2 -> 2, etc.
                    'text': text,
                    'position': i + 1
                })
        
        return headings
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main content text, removing navigation and other noise."""
        # Create a copy to avoid modifying original
        content_soup = BeautifulSoup(str(soup), 'html.parser')
        
        # Remove noise tags
        for tag_name in self.noise_tags:
            for tag in content_soup.find_all(tag_name):
                tag.decompose()
        
        # Remove elements with noise classes/ids
        for noise_term in self.noise_classes:
            # Remove by class
            for element in content_soup.find_all(class_=re.compile(noise_term, re.I)):
                element.decompose()
            # Remove by id
            for element in content_soup.find_all(id=re.compile(noise_term, re.I)):
                element.decompose()
        
        # Try to find main content area
        main_content = None
        
        # Look for semantic HTML5 main element
        main_element = content_soup.find('main')
        if main_element:
            main_content = main_element
        else:
            # Look for common content indicators
            for indicator in self.main_content_indicators:
                # Try by id first
                element = content_soup.find(id=re.compile(indicator, re.I))
                if element:
                    main_content = element
                    break
                
                # Then try by class
                element = content_soup.find(class_=re.compile(indicator, re.I))
                if element:
                    main_content = element
                    break
        
        # If no main content found, use body
        if not main_content:
            main_content = content_soup.find('body') or content_soup
        
        # Extract text content
        text_content = main_content.get_text(separator=' ', strip=True)
        
        # Clean up whitespace
        text_content = re.sub(r'\s+', ' ', text_content)
        
        return text_content
    
    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Extract images with alt text and sources."""
        images = []
        img_tags = soup.find_all('img')
        
        for img in img_tags:
            src = img.get('src', '')
            alt = img.get('alt', '')
            title = img.get('title', '')
            
            if src:  # Only include images with src
                # Convert relative URLs to absolute
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    from urllib.parse import urljoin
                    src = urljoin(base_url, src)
                
                images.append({
                    'src': src,
                    'alt': alt,
                    'title': title
                })
        
        return images
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Extract internal and external links."""
        links = []
        link_tags = soup.find_all('a', href=True)
        
        for link in link_tags:
            href = link['href']
            text = link.get_text(strip=True)
            title = link.get('title', '')
            
            if href and text:  # Only include links with href and text
                # Determine if internal or external
                from urllib.parse import urljoin, urlparse
                absolute_url = urljoin(base_url, href)
                base_domain = urlparse(base_url).netloc
                link_domain = urlparse(absolute_url).netloc
                
                link_type = 'internal' if link_domain == base_domain else 'external'
                
                links.append({
                    'href': absolute_url,
                    'text': text,
                    'title': title,
                    'type': link_type
                })
        
        return links
    
    def _calculate_content_metrics(self, content: str, headings: List[Dict]) -> Dict[str, Any]:
        """Calculate content metrics for analysis."""
        if not content:
            return {}
        
        words = content.split()
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return {
            'word_count': len(words),
            'character_count': len(content),
            'sentence_count': len(sentences),
            'paragraph_count': content.count('\n\n') + 1,
            'heading_count': len(headings),
            'avg_words_per_sentence': len(words) / len(sentences) if sentences else 0,
            'reading_time_minutes': len(words) / 200  # Assume 200 words per minute
        }