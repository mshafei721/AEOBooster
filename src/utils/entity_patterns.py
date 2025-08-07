"""
Custom entity patterns for business entity recognition.
"""
import re
from typing import Dict, List, Tuple, Any

class EntityPatterns:
    """Custom patterns and rules for business entity extraction."""
    
    def __init__(self):
        """Initialize entity patterns."""
        # Product patterns
        self.product_patterns = [
            (r'\b(?:Enterprise|Professional|Premium|Standard|Basic|Pro)\s+\w+(?:\s+\w+){0,3}\b', 0.2),
            (r'\b\w+\s+(?:Software|Platform|System|Tool|Suite|Solution|Service)\b', 0.3),
            (r'\b(?:Version|v\.?\s*)\d+(?:\.\d+)*\b', 0.1),
            (r'\b\w+\s+(?:API|SDK|Framework|Library|Plugin|Extension)\b', 0.2),
            (r'\b(?:iPhone|Android|Windows|Mac|Linux|iOS)\s+\w+(?:\s+\w+){0,2}\b', 0.2),
        ]
        
        # Service patterns
        self.service_patterns = [
            (r'\b(?:Consulting|Development|Design|Marketing|Support|Maintenance|Training)\s+Services?\b', 0.3),
            (r'\b(?:Web|Mobile|Software|Application)\s+Development\b', 0.3),
            (r'\b(?:Digital|Content|Social Media|Email|SEO)\s+Marketing\b', 0.3),
            (r'\b(?:Cloud|IT|Technical|Customer)\s+Support\b', 0.2),
            (r'\b(?:Project|Program|Product)\s+Management\b', 0.2),
            (r'\b(?:Data|Business|System)\s+Analysis\b', 0.2),
        ]
        
        # Brand patterns
        self.brand_patterns = [
            (r'\b[A-Z][a-z]+(?:[A-Z][a-z]*)*\s+(?:Inc|LLC|Corp|Ltd|Co)\.?\b', 0.3),
            (r'\b[A-Z][a-zA-Z]*[a-z]\s*®\b', 0.4),  # Registered trademarks
            (r'\b[A-Z][a-zA-Z]*[a-z]\s*™\b', 0.3),  # Trademarks
            (r'@[A-Za-z0-9_]+\b', 0.2),  # Social media handles
        ]
        
        # Feature patterns
        self.feature_patterns = [
            (r'\b(?:24/7|Real-time|Multi-user|Cross-platform|Mobile-friendly|Responsive)\b', 0.2),
            (r'\b(?:Free|Unlimited|Secure|Fast|Easy|Simple|Advanced|Custom)\b', 0.1),
            (r'\b(?:Dashboard|Analytics|Reporting|Integration|Automation|Workflow)\b', 0.2),
            (r'\b(?:SSL|API|REST|GraphQL|OAuth|SAML|Single Sign-On)\b', 0.2),
        ]
        
        # Location patterns
        self.location_patterns = [
            (r'\b(?:Headquarters|Located|Serving|Based)\s+in\s+[A-Z][a-z]+(?:,\s*[A-Z]{2})?\b', 0.3),
            (r'\b[A-Z][a-z]+,\s*[A-Z]{2}\s*\d{5}\b', 0.3),  # City, State ZIP
            (r'\b\d+\s+[A-Z][a-z]+\s+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Boulevard|Blvd)\b', 0.2),
            (r'\b(?:Downtown|Uptown|North|South|East|West)\s+[A-Z][a-z]+\b', 0.1),
        ]
        
        # Price patterns
        self.price_patterns = [
            (r'\$\d+(?:,\d{3})*(?:\.\d{2})?\s*(?:per|/)?(?:\s*month|monthly|mo|year|yearly|annually)?\b', 0.4),
            (r'\b(?:Starting\s+(?:at|from)\s*)?\$\d+(?:,\d{3})*(?:\.\d{2})?\b', 0.3),
            (r'\b(?:Free|Premium|Pro|Enterprise):\s*\$\d+(?:,\d{3})*(?:\.\d{2})?\b', 0.3),
            (r'\b\d+%\s*(?:off|discount|savings?)\b', 0.2),
            (r'\b(?:Save|Discount|Sale):\s*\$\d+(?:,\d{3})*(?:\.\d{2})?\b', 0.2),
        ]
        
        # Compile all patterns
        self.all_patterns = {
            'product': self.product_patterns,
            'service': self.service_patterns, 
            'brand': self.brand_patterns,
            'feature': self.feature_patterns,
            'location': self.location_patterns,
            'price': self.price_patterns
        }
        
        # spaCy custom patterns for business entities
        self.spacy_patterns = self._create_spacy_patterns()
    
    def get_regex_patterns(self) -> Dict[str, List[Tuple[str, float]]]:
        """Get all regex patterns with confidence modifiers."""
        return self.all_patterns
    
    def get_patterns(self) -> List[Dict[str, Any]]:
        """Get spaCy-compatible patterns for custom pipeline component."""
        return self.spacy_patterns
    
    def _create_spacy_patterns(self) -> List[Dict[str, Any]]:
        """Create spaCy EntityRuler patterns for business entities."""
        patterns = []
        
        # Product name patterns
        product_patterns = [
            {"label": "PRODUCT", "pattern": [
                {"LOWER": {"IN": ["enterprise", "professional", "premium", "standard", "basic", "pro"]}},
                {"IS_ALPHA": True, "OP": "+"}
            ]},
            {"label": "PRODUCT", "pattern": [
                {"IS_ALPHA": True},
                {"LOWER": {"IN": ["software", "platform", "system", "tool", "suite", "solution", "api", "sdk"]}}
            ]},
        ]
        patterns.extend(product_patterns)
        
        # Service patterns
        service_patterns = [
            {"label": "SERVICE", "pattern": [
                {"LOWER": {"IN": ["consulting", "development", "design", "marketing", "support", "training"]}},
                {"LOWER": {"IN": ["services", "service"]}, "OP": "?"}
            ]},
            {"label": "SERVICE", "pattern": [
                {"LOWER": {"IN": ["web", "mobile", "software", "application"]}},
                {"LOWER": "development"}
            ]},
        ]
        patterns.extend(service_patterns)
        
        # Brand/Organization patterns
        brand_patterns = [
            {"label": "BRAND", "pattern": [
                {"IS_TITLE": True},
                {"LOWER": {"IN": ["inc", "llc", "corp", "ltd", "co", "company"]}}
            ]},
        ]
        patterns.extend(brand_patterns)
        
        # Feature patterns
        feature_patterns = [
            {"label": "FEATURE", "pattern": [
                {"LOWER": {"IN": ["real-time", "24/7", "multi-user", "cross-platform", "mobile-friendly"]}}
            ]},
            {"label": "FEATURE", "pattern": [
                {"LOWER": {"IN": ["dashboard", "analytics", "reporting", "integration", "automation"]}}
            ]},
        ]
        patterns.extend(feature_patterns)
        
        return patterns
    
    def extract_price_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract price-related entities with additional context.
        
        Args:
            text: Text to extract prices from
            
        Returns:
            List of price entities with context
        """
        price_entities = []
        
        # Enhanced price patterns with context
        price_context_patterns = [
            (r'(?:Starting\s+(?:at|from)\s*)?(\$\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:per\s+)?(\w+)?', 'base_price'),
            (r'(\w+):\s*(\$\d+(?:,\d{3})*(?:\.\d{2})?)', 'plan_price'),
            (r'(?:Save|Discount|Sale):\s*(\$\d+(?:,\d{3})*(?:\.\d{2})?)', 'discount'),
            (r'(\d+)%\s*(?:off|discount|savings?)', 'percentage_discount'),
        ]
        
        for pattern, price_type in price_context_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                price_entity = {
                    'value': match.group().strip(),
                    'type': 'price',
                    'subtype': price_type,
                    'context': self._get_price_context(match, text),
                    'confidence': 0.8 if price_type in ['base_price', 'plan_price'] else 0.6
                }
                price_entities.append(price_entity)
                
        return price_entities
    
    def _get_price_context(self, match, text: str, window: int = 30) -> str:
        """Get context around a price match."""
        start = max(0, match.start() - window)
        end = min(len(text), match.end() + window)
        return text[start:end].strip()
    
    def extract_product_names(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract product names using advanced patterns.
        
        Args:
            text: Text to extract product names from
            
        Returns:
            List of product entities
        """
        product_entities = []
        
        # Advanced product patterns
        advanced_patterns = [
            # Version patterns
            (r'([A-Z][a-zA-Z\s]+?)\s+(?:Version|v\.?)\s*(\d+(?:\.\d+)*)', 'versioned_product'),
            
            # Suite/Platform patterns
            (r'([A-Z][a-zA-Z\s]+?)\s+(Suite|Platform|System|Framework)', 'platform_product'),
            
            # Edition patterns
            (r'([A-Z][a-zA-Z\s]+?)\s+(Enterprise|Professional|Standard|Premium|Basic)\s+Edition', 'edition_product'),
            
            # Service-based product patterns
            (r'([A-Z][a-zA-Z\s]+?)\s+(?:as\s+a\s+Service|SaaS|Service)', 'service_product'),
        ]
        
        for pattern, product_type in advanced_patterns:
            matches = re.finditer(pattern, text)
            
            for match in matches:
                product_name = match.group(1).strip()
                if len(product_name) > 2:  # Filter out very short matches
                    product_entity = {
                        'value': match.group().strip(),
                        'core_name': product_name,
                        'type': 'product',
                        'subtype': product_type,
                        'confidence': 0.7
                    }
                    product_entities.append(product_entity)
                    
        return product_entities
    
    def validate_entity_quality(self, entity_value: str, entity_type: str) -> bool:
        """
        Validate the quality of an extracted entity.
        
        Args:
            entity_value: The extracted entity text
            entity_type: The entity type (product, service, brand, etc.)
            
        Returns:
            True if entity passes quality checks
        """
        # Basic quality checks
        if not entity_value or len(entity_value.strip()) < 2:
            return False
            
        # Check for too many special characters
        special_char_ratio = len(re.findall(r'[^\w\s]', entity_value)) / len(entity_value)
        if special_char_ratio > 0.5:
            return False
            
        # Check for too many numbers (except for prices)
        if entity_type != 'price':
            number_ratio = len(re.findall(r'\d', entity_value)) / len(entity_value)
            if number_ratio > 0.7:
                return False
                
        # Check for common noise words
        noise_words = ['click', 'here', 'more', 'read', 'view', 'see', 'learn', 'get']
        entity_lower = entity_value.lower()
        if any(word in entity_lower for word in noise_words):
            return False
            
        return True