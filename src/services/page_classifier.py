"""
Page classification service for identifying page types and content categories.
"""
import logging
import re
from typing import Dict, List, Tuple, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class PageClassifier:
    """Classify web pages by type and content category."""
    
    def __init__(self):
        """Initialize page classifier with rules and keywords."""
        
        # URL pattern rules for page type detection
        self.url_patterns = {
            'product': [
                r'/product[s]?/',
                r'/item[s]?/',
                r'/shop/',
                r'/store/',
                r'/buy/',
                r'/catalog/',
                r'/p/',
                r'-p\d+',  # product IDs
                r'/sku/',
                r'/products/.+',
                r'/items/.+',
            ],
            'service': [
                r'/service[s]?/',
                r'/solutions?/',
                r'/offerings?/',
                r'/what-we-do/',
                r'/our-services/',
                r'/consultation/',
                r'/consulting/',
            ],
            'blog': [
                r'/blog/',
                r'/news/',
                r'/article[s]?/',
                r'/post[s]?/',
                r'/insights?/',
                r'/updates?/',
                r'/press/',
                r'/stories/',
                r'/resources/blog/',
                r'/\d{4}/\d{2}/',  # Date patterns like /2024/01/
            ],
            'about': [
                r'/about/',
                r'/company/',
                r'/who-we-are/',
                r'/our-story/',
                r'/history/',
                r'/team/',
                r'/leadership/',
                r'/mission/',
                r'/vision/',
            ],
            'contact': [
                r'/contact/',
                r'/get-in-touch/',
                r'/reach-us/',
                r'/support/',
                r'/help/',
                r'/customer-service/',
            ],
            'pricing': [
                r'/pricing/',
                r'/plans?/',
                r'/packages?/',
                r'/costs?/',
                r'/rates?/',
                r'/subscription/',
            ],
            'faq': [
                r'/faq/',
                r'/frequently-asked-questions/',
                r'/questions/',
                r'/q-and-a/',
                r'/help-center/',
            ],
            'homepage': [
                r'^/$',
                r'^/index',
                r'^/home',
                r'^/welcome',
            ],
            'category': [
                r'/categor(y|ies)/',
                r'/departments?/',
                r'/sections?/',
                r'/types?/',
                r'/browse/',
            ],
            'legal': [
                r'/privacy/',
                r'/terms/',
                r'/legal/',
                r'/policy/',
                r'/disclaimer/',
                r'/copyright/',
                r'/license/',
            ]
        }
        
        # Content-based keywords for classification
        self.content_keywords = {
            'product': {
                'strong': [
                    'add to cart', 'buy now', 'purchase', 'price', 'in stock',
                    'out of stock', 'sku', 'product details', 'specifications',
                    'reviews', 'rating', 'customer reviews', '$', 'USD', 'EUR',
                    'shipping', 'delivery', 'warranty', 'return policy'
                ],
                'medium': [
                    'features', 'benefits', 'description', 'overview',
                    'availability', 'quantity', 'size', 'color', 'model',
                    'brand', 'manufacturer', 'technical specs'
                ]
            },
            'service': {
                'strong': [
                    'our services', 'what we do', 'solutions', 'consulting',
                    'professional services', 'expertise', 'consultation',
                    'get started', 'free consultation', 'contact us today'
                ],
                'medium': [
                    'experience', 'years of experience', 'qualified',
                    'certified', 'portfolio', 'case studies', 'results',
                    'approach', 'methodology', 'process'
                ]
            },
            'blog': {
                'strong': [
                    'published on', 'posted on', 'by author', 'read more',
                    'comments', 'share this', 'tags:', 'categories:',
                    'related posts', 'recent posts', 'archive'
                ],
                'medium': [
                    'learn more', 'tips', 'guide', 'tutorial', 'how to',
                    'best practices', 'insights', 'analysis', 'opinion',
                    'industry news', 'trends'
                ]
            },
            'about': {
                'strong': [
                    'about us', 'our story', 'our mission', 'our vision',
                    'who we are', 'company history', 'founded in',
                    'our team', 'leadership team', 'meet the team'
                ],
                'medium': [
                    'values', 'culture', 'philosophy', 'background',
                    'experience', 'commitment', 'dedication', 'passion',
                    'journey', 'growth'
                ]
            },
            'contact': {
                'strong': [
                    'contact us', 'get in touch', 'reach us', 'phone:',
                    'email:', 'address:', 'office hours', 'contact form',
                    'send message', 'call us', 'visit us'
                ],
                'medium': [
                    'location', 'directions', 'map', 'office', 'headquarters',
                    'support', 'customer service', 'help desk'
                ]
            },
            'pricing': {
                'strong': [
                    'pricing', 'plans', 'packages', 'subscription', 'cost',
                    'per month', 'per year', 'annual', 'monthly',
                    'free trial', 'sign up', 'choose plan'
                ],
                'medium': [
                    'features included', 'compare plans', 'upgrade',
                    'downgrade', 'billing', 'payment', 'discount'
                ]
            },
            'faq': {
                'strong': [
                    'frequently asked questions', 'faq', 'questions and answers',
                    'q&a', 'common questions', 'help center'
                ],
                'medium': [
                    'question:', 'answer:', 'how do i', 'what is',
                    'why does', 'when will', 'can i', 'troubleshooting'
                ]
            },
            'homepage': {
                'strong': [
                    'welcome to', 'home page', 'main page', 'get started',
                    'learn more about', 'discover', 'explore our',
                    'featured products', 'latest news'
                ],
                'medium': [
                    'overview', 'introduction', 'what we offer',
                    'our company', 'solutions', 'services'
                ]
            }
        }
        
        # Structured data type indicators
        self.structured_data_types = {
            'product': ['Product', 'Offer', 'Review', 'AggregateRating'],
            'service': ['Service', 'Organization', 'LocalBusiness'],
            'blog': ['Article', 'BlogPosting', 'NewsArticle'],
            'about': ['Organization', 'Corporation', 'Person'],
            'contact': ['Organization', 'LocalBusiness', 'ContactPoint'],
            'faq': ['FAQPage', 'Question', 'Answer']
        }
    
    def classify_page(self, url: str, title: str, content: str, 
                     structured_data: Optional[Dict] = None) -> Tuple[str, float]:
        """
        Classify a page and return type with confidence score.
        
        Args:
            url: Page URL
            title: Page title
            content: Page content text
            structured_data: Optional structured data (JSON-LD, microdata)
            
        Returns:
            Tuple of (page_type, confidence_score)
        """
        try:
            # Combine title and content for analysis
            text_content = f"{title} {content}".lower()
            
            # Get scores for each page type
            scores = {}
            
            for page_type in self.url_patterns.keys():
                url_score = self._score_url_patterns(url, page_type)
                content_score = self._score_content_keywords(text_content, page_type)
                structured_score = self._score_structured_data(structured_data, page_type)
                
                # Weighted combination of scores
                total_score = (
                    url_score * 0.4 +           # URL patterns are quite reliable
                    content_score * 0.5 +       # Content is most important
                    structured_score * 0.1      # Structured data is bonus
                )
                
                scores[page_type] = total_score
            
            # Find the best match
            best_type = max(scores.keys(), key=lambda k: scores[k])
            best_score = scores[best_type]
            
            # Apply confidence thresholds
            if best_score < 0.1:
                return 'unknown', 0.0
            elif best_score < 0.3:
                confidence = 0.3
            elif best_score < 0.5:
                confidence = 0.6
            elif best_score < 0.7:
                confidence = 0.8
            else:
                confidence = 0.95
            
            logger.debug(f"Page classification for {url}: {best_type} ({confidence:.2f})")
            logger.debug(f"All scores: {scores}")
            
            return best_type, confidence
            
        except Exception as e:
            logger.error(f"Error classifying page {url}: {e}")
            return 'unknown', 0.0
    
    def _score_url_patterns(self, url: str, page_type: str) -> float:
        """Score URL patterns for a given page type."""
        if page_type not in self.url_patterns:
            return 0.0
        
        try:
            parsed = urlparse(url)
            path = parsed.path.lower()
            
            # Check each pattern for this page type
            for pattern in self.url_patterns[page_type]:
                if re.search(pattern, path):
                    return 1.0  # Strong match
            
            return 0.0
            
        except Exception as e:
            logger.debug(f"Error scoring URL patterns for {url}: {e}")
            return 0.0
    
    def _score_content_keywords(self, content: str, page_type: str) -> float:
        """Score content keywords for a given page type."""
        if page_type not in self.content_keywords:
            return 0.0
        
        try:
            keywords = self.content_keywords[page_type]
            content_lower = content.lower()
            
            strong_matches = 0
            medium_matches = 0
            
            # Count strong keyword matches
            for keyword in keywords.get('strong', []):
                if keyword.lower() in content_lower:
                    strong_matches += 1
            
            # Count medium keyword matches
            for keyword in keywords.get('medium', []):
                if keyword.lower() in content_lower:
                    medium_matches += 1
            
            # Calculate weighted score
            strong_weight = 0.7
            medium_weight = 0.3
            
            max_strong = len(keywords.get('strong', []))
            max_medium = len(keywords.get('medium', []))
            
            strong_score = (strong_matches / max_strong) if max_strong > 0 else 0
            medium_score = (medium_matches / max_medium) if max_medium > 0 else 0
            
            total_score = (strong_score * strong_weight + medium_score * medium_weight)
            
            return min(total_score, 1.0)  # Cap at 1.0
            
        except Exception as e:
            logger.debug(f"Error scoring content keywords for {page_type}: {e}")
            return 0.0
    
    def _score_structured_data(self, structured_data: Optional[Dict], page_type: str) -> float:
        """Score structured data indicators for a given page type."""
        if not structured_data or page_type not in self.structured_data_types:
            return 0.0
        
        try:
            target_types = self.structured_data_types[page_type]
            found_types = set()
            
            # Check JSON-LD data
            json_ld = structured_data.get('json_ld', [])
            for item in json_ld:
                if isinstance(item, dict):
                    item_type = item.get('@type', '')
                    if isinstance(item_type, list):
                        found_types.update(item_type)
                    else:
                        found_types.add(item_type)
            
            # Check microdata
            microdata = structured_data.get('microdata', [])
            for item in microdata:
                if isinstance(item, dict):
                    item_type = item.get('type', '')
                    if item_type:
                        # Extract type name from schema.org URL
                        type_name = item_type.split('/')[-1]
                        found_types.add(type_name)
            
            # Calculate match score
            matches = 0
            for target_type in target_types:
                if target_type in found_types:
                    matches += 1
            
            return matches / len(target_types) if target_types else 0.0
            
        except Exception as e:
            logger.debug(f"Error scoring structured data for {page_type}: {e}")
            return 0.0
    
    def get_page_categories(self) -> List[str]:
        """Get list of all available page categories."""
        return list(self.url_patterns.keys())
    
    def classify_multiple_indicators(self, url: str, title: str, content: str,
                                   structured_data: Optional[Dict] = None) -> Dict[str, float]:
        """
        Get confidence scores for all page types.
        
        Returns:
            Dict mapping page types to confidence scores
        """
        text_content = f"{title} {content}".lower()
        scores = {}
        
        for page_type in self.url_patterns.keys():
            url_score = self._score_url_patterns(url, page_type)
            content_score = self._score_content_keywords(text_content, page_type)
            structured_score = self._score_structured_data(structured_data, page_type)
            
            total_score = (
                url_score * 0.4 +
                content_score * 0.5 +
                structured_score * 0.1
            )
            
            scores[page_type] = round(total_score, 3)
        
        return scores