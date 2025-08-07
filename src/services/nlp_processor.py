"""
NLP processing utilities for content preprocessing and text cleaning.
"""
import re
from typing import List, Dict, Any
from bs4 import BeautifulSoup
import html

class NLPProcessor:
    """Utilities for NLP text preprocessing and cleaning."""
    
    def __init__(self):
        """Initialize the NLP processor."""
        # Common stop words and noise patterns
        self.noise_patterns = [
            r'Copyright\s+\©?\s*\d{4}.*',
            r'All rights reserved\.?',
            r'Terms of Service',
            r'Privacy Policy',
            r'Cookie Policy',
            r'Sign up|Sign in|Login|Register',
            r'Follow us on|Connect with us',
            r'Subscribe to|Join our newsletter',
        ]
        
        # Navigation and UI text patterns
        self.navigation_patterns = [
            r'^Home$|^About$|^Contact$|^Services$|^Products$',
            r'^Menu$|^Navigation$',
            r'^Search$|^Filter$|^Sort by$',
            r'^Next$|^Previous$|^Back$',
            r'^Share$|^Print$|^Download$',
        ]
        
        # Common business stop words to filter out
        self.business_stop_words = {
            'company', 'business', 'service', 'product', 'solution',
            'website', 'page', 'site', 'information', 'content',
            'click', 'here', 'more', 'read', 'view', 'see',
            'learn', 'discover', 'find', 'get', 'contact',
            'home', 'about', 'services', 'products', 'portfolio'
        }
    
    def clean_text(self, text: str) -> str:
        """
        Clean and preprocess text for entity extraction.
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned text suitable for NLP processing
        """
        if not text:
            return ""
            
        # Decode HTML entities
        text = html.unescape(text)
        
        # Remove HTML tags if any
        text = BeautifulSoup(text, 'html.parser').get_text()
        
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text)
        
        # Remove noise patterns
        for pattern in self.noise_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
            
        # Remove navigation patterns
        for pattern in self.navigation_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Clean up remaining whitespace
        text = text.strip()
        
        return text
    
    def segment_content(self, page_content: Dict[str, Any]) -> Dict[str, str]:
        """
        Segment page content into different sections for targeted extraction.
        
        Args:
            page_content: Page content dictionary from CrawledPage
            
        Returns:
            Dictionary with segmented content sections
        """
        segments = {}
        
        # Title segment (high priority)
        if page_content.get('title'):
            segments['title'] = self.clean_text(page_content['title'])
            
        # Meta description segment (medium priority)  
        if page_content.get('meta_description'):
            segments['meta_description'] = self.clean_text(page_content['meta_description'])
            
        # Headings segment (high priority)
        if page_content.get('headings'):
            heading_text = self._extract_heading_text(page_content['headings'])
            if heading_text:
                segments['headings'] = self.clean_text(heading_text)
        
        # Main content segment (medium priority)
        if page_content.get('content_text'):
            # Split main content into sections to avoid overwhelming NLP
            content_sections = self._split_content(page_content['content_text'])
            segments['content_main'] = self.clean_text(content_sections.get('main', ''))
            segments['content_secondary'] = self.clean_text(content_sections.get('secondary', ''))
            
        # Structured data segments (high priority)
        if page_content.get('structured_data'):
            structured_text = self._extract_structured_data_text(page_content['structured_data'])
            if structured_text:
                segments['structured_data'] = structured_text
                
        return segments
    
    def _extract_heading_text(self, headings: List[Dict]) -> str:
        """Extract text from headings structure."""
        if not headings:
            return ""
            
        heading_texts = []
        for heading in headings:
            if isinstance(heading, dict):
                if 'text' in heading:
                    heading_texts.append(heading['text'])
                elif 'content' in heading:
                    heading_texts.append(heading['content'])
            elif isinstance(heading, str):
                heading_texts.append(heading)
                
        return " | ".join(heading_texts)  # Use separator to maintain context
    
    def _split_content(self, content: str, max_main_length: int = 2000) -> Dict[str, str]:
        """
        Split content into main and secondary sections.
        
        Args:
            content: Full content text
            max_main_length: Maximum length for main content section
            
        Returns:
            Dictionary with 'main' and 'secondary' content sections
        """
        if not content:
            return {'main': '', 'secondary': ''}
            
        if len(content) <= max_main_length:
            return {'main': content, 'secondary': ''}
            
        # Find a good breaking point (paragraph, sentence)
        break_point = max_main_length
        
        # Try to break at paragraph boundary
        para_break = content.rfind('\n\n', 0, max_main_length)
        if para_break > max_main_length * 0.7:  # At least 70% of target length
            break_point = para_break
        else:
            # Try to break at sentence boundary
            sent_break = content.rfind('. ', 0, max_main_length)
            if sent_break > max_main_length * 0.8:  # At least 80% of target length
                break_point = sent_break + 1
                
        return {
            'main': content[:break_point],
            'secondary': content[break_point:]
        }
    
    def _extract_structured_data_text(self, structured_data: Dict) -> str:
        """Extract relevant text from structured data (JSON-LD, microdata, etc.)."""
        if not structured_data:
            return ""
            
        text_parts = []
        
        # Common structured data fields that contain business entities
        business_fields = [
            'name', 'alternateName', 'description', 'headline',
            'brand', 'manufacturer', 'category', 'serviceType',
            'jobTitle', 'organizationName', 'productName',
            'offers', 'priceRange', 'location', 'address'
        ]
        
        def extract_text_recursive(data, path=""):
            """Recursively extract text from structured data."""
            if isinstance(data, dict):
                for key, value in data.items():
                    if key.lower() in [f.lower() for f in business_fields]:
                        if isinstance(value, str):
                            text_parts.append(value)
                        elif isinstance(value, (list, dict)):
                            extract_text_recursive(value, f"{path}.{key}")
                    else:
                        extract_text_recursive(value, f"{path}.{key}")
            elif isinstance(data, list):
                for item in data:
                    extract_text_recursive(item, path)
            elif isinstance(data, str) and len(data.strip()) > 0:
                text_parts.append(data)
                
        extract_text_recursive(structured_data)
        
        return " | ".join(text_parts)
    
    def filter_noise_entities(self, entities: List[str]) -> List[str]:
        """
        Filter out noise words and common non-business entities.
        
        Args:
            entities: List of extracted entity strings
            
        Returns:
            Filtered list of entities
        """
        filtered = []
        
        for entity in entities:
            entity_lower = entity.lower().strip()
            
            # Skip if too short
            if len(entity_lower) < 2:
                continue
                
            # Skip if it's a common stop word
            if entity_lower in self.business_stop_words:
                continue
                
            # Skip if it matches navigation patterns
            if any(re.match(pattern, entity, re.IGNORECASE) for pattern in self.navigation_patterns):
                continue
                
            # Skip if it's mostly numbers or punctuation
            if len(re.sub(r'[^\w\s]', '', entity_lower)) < 2:
                continue
                
            filtered.append(entity)
            
        return filtered
    
    def calculate_content_importance_score(self, content: str, source_field: str) -> float:
        """
        Calculate importance score for content based on various factors.
        
        Args:
            content: Content text
            source_field: Source field name (title, headings, content_text, etc.)
            
        Returns:
            Importance score between 0.0 and 1.0
        """
        base_scores = {
            'title': 0.9,
            'headings': 0.8,
            'meta_description': 0.7,
            'structured_data': 0.8,
            'content_main': 0.6,
            'content_secondary': 0.4,
            'content_text': 0.5
        }
        
        base_score = base_scores.get(source_field, 0.3)
        
        # Adjust based on content characteristics
        if content:
            # Shorter content in high-priority fields is often more focused
            if source_field in ['title', 'headings'] and len(content) < 100:
                base_score += 0.1
                
            # Content with proper capitalization suggests more structured information
            if re.search(r'\b[A-Z][a-z]+\b', content):
                base_score += 0.05
                
            # Content with numbers/prices suggests product/service information
            if re.search(r'\$\d+|\d+%|\d+\.\d+', content):
                base_score += 0.1
                
        return min(base_score, 1.0)