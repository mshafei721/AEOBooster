"""
Sample business content for testing entity extraction.
"""
from typing import Dict, List, Any

class BusinessContentFixtures:
    """Test fixtures for business content samples."""
    
    @staticmethod
    def get_ecommerce_content() -> Dict[str, Any]:
        """E-commerce website content sample."""
        return {
            "id": "page_ecommerce_1",
            "title": "Premium Enterprise CRM Software - TechCorp Solutions",
            "meta_description": "Advanced CRM platform for enterprise businesses. Features include real-time analytics, customer management, and mobile-friendly dashboard.",
            "content_text": """
            Welcome to TechCorp Solutions, the leading provider of Enterprise CRM Software.
            
            Our Premium CRM Suite includes:
            - Real-time customer analytics
            - Mobile-friendly dashboard
            - Advanced reporting tools
            - 24/7 customer support
            - SSL security and OAuth integration
            
            Pricing starts at $99 per month for the Standard plan, with Enterprise plans available from $299 monthly.
            
            Serving businesses in New York, California, and Texas with headquarters located in San Francisco, CA.
            
            Features:
            - Multi-user access
            - Cross-platform compatibility
            - Unlimited data storage
            - API integration capabilities
            """,
            "headings": [
                {"level": 1, "text": "Enterprise CRM Software"},
                {"level": 2, "text": "Premium Features"}, 
                {"level": 2, "text": "Pricing Plans"},
                {"level": 3, "text": "Standard Plan - $99/month"},
                {"level": 3, "text": "Enterprise Plan - $299/month"}
            ],
            "structured_data": {
                "@type": "SoftwareApplication",
                "name": "TechCorp CRM Suite",
                "applicationCategory": "BusinessApplication",
                "offers": {
                    "@type": "Offer",
                    "priceRange": "$99 - $299",
                    "priceCurrency": "USD"
                },
                "brand": {
                    "@type": "Organization", 
                    "name": "TechCorp Solutions"
                }
            }
        }
    
    @staticmethod
    def get_service_business_content() -> Dict[str, Any]:
        """Service business website content sample."""
        return {
            "id": "page_service_1", 
            "title": "Digital Marketing Services - WebBoost Agency",
            "meta_description": "Professional digital marketing consulting including SEO, social media marketing, and web development services.",
            "content_text": """
            WebBoost Agency offers comprehensive Digital Marketing Services for small and medium businesses.
            
            Our services include:
            - SEO Consulting Services
            - Social Media Marketing
            - Web Development and Design
            - Content Marketing Strategy
            - Email Marketing Campaigns
            
            We specialize in helping businesses increase their online visibility and drive more customers.
            Based in Austin, Texas, serving clients nationwide.
            
            Contact us for a free consultation and custom pricing based on your needs.
            """,
            "headings": [
                {"level": 1, "text": "Digital Marketing Services"},
                {"level": 2, "text": "Our Expertise"},
                {"level": 2, "text": "Why Choose WebBoost"}
            ],
            "structured_data": {
                "@type": "LocalBusiness",
                "name": "WebBoost Agency", 
                "serviceType": "Digital Marketing",
                "address": {
                    "@type": "PostalAddress",
                    "addressLocality": "Austin",
                    "addressRegion": "TX"
                }
            }
        }
    
    @staticmethod
    def get_noisy_content() -> Dict[str, Any]:
        """Content with lots of noise and navigation elements."""
        return {
            "id": "page_noisy_1",
            "title": "Home | About | Contact | Services | Products",
            "meta_description": "Click here to learn more about our company",
            "content_text": """
            Home About Contact Services Products
            
            Copyright © 2024 Example Company. All rights reserved.
            Terms of Service Privacy Policy Cookie Policy
            
            Sign up for our newsletter Subscribe here Click to download
            Follow us on Facebook Twitter LinkedIn
            
            Menu Navigation Search Filter Sort by Next Previous Back
            
            Our actual business content:
            DataFlow Analytics Platform helps businesses analyze customer data.
            Professional Data Analysis Services available.
            Located in Boston, MA with satellite offices.
            """,
            "headings": [
                {"level": 1, "text": "Navigation Menu"},
                {"level": 2, "text": "Footer Links"}
            ],
            "structured_data": {}
        }
    
    @staticmethod
    def get_minimal_content() -> Dict[str, Any]:
        """Minimal content with limited information."""
        return {
            "id": "page_minimal_1",
            "title": "Page",
            "meta_description": "",
            "content_text": "Welcome to our site.",
            "headings": [],
            "structured_data": {}
        }
    
    @staticmethod
    def get_product_focused_content() -> Dict[str, Any]:
        """Product-focused content with detailed specifications."""
        return {
            "id": "page_product_1",
            "title": "iPhone 15 Pro Max - Latest Smartphone Technology",
            "meta_description": "Advanced iPhone with premium features, available in multiple storage options.",
            "content_text": """
            iPhone 15 Pro Max - The latest innovation from Apple Inc.
            
            Product Features:
            - 6.7-inch display with ProMotion technology
            - Advanced camera system with 48MP main lens
            - A17 Pro chip for lightning-fast performance
            - USB-C connectivity
            - Titanium construction for durability
            
            Available in:
            - 128GB model - Starting at $1,199
            - 256GB model - $1,299
            - 512GB model - $1,499
            - 1TB model - $1,699
            
            Available at Apple Store locations nationwide and authorized retailers.
            Free shipping on orders over $35.
            """,
            "headings": [
                {"level": 1, "text": "iPhone 15 Pro Max"},
                {"level": 2, "text": "Technical Specifications"},
                {"level": 2, "text": "Pricing and Availability"}
            ],
            "structured_data": {
                "@type": "Product",
                "name": "iPhone 15 Pro Max",
                "brand": {
                    "@type": "Brand",
                    "name": "Apple"
                },
                "offers": [
                    {
                        "@type": "Offer",
                        "price": "1199.00",
                        "priceCurrency": "USD"
                    }
                ]
            }
        }
    
    @staticmethod
    def get_expected_entities() -> Dict[str, List[Dict[str, Any]]]:
        """Expected entities for each content sample."""
        return {
            "ecommerce": [
                {"type": "product", "value": "Enterprise CRM Software", "confidence_min": 0.8},
                {"type": "product", "value": "Premium CRM Suite", "confidence_min": 0.7},
                {"type": "brand", "value": "TechCorp Solutions", "confidence_min": 0.8},
                {"type": "feature", "value": "Real-time analytics", "confidence_min": 0.6},
                {"type": "feature", "value": "24/7 support", "confidence_min": 0.6},
                {"type": "price", "value": "$99 per month", "confidence_min": 0.7},
                {"type": "price", "value": "$299 monthly", "confidence_min": 0.7},
                {"type": "location", "value": "San Francisco, CA", "confidence_min": 0.7},
                {"type": "location", "value": "New York", "confidence_min": 0.6},
            ],
            "service": [
                {"type": "service", "value": "Digital Marketing Services", "confidence_min": 0.8},
                {"type": "service", "value": "SEO Consulting Services", "confidence_min": 0.7},
                {"type": "service", "value": "Social Media Marketing", "confidence_min": 0.7},
                {"type": "service", "value": "Web Development", "confidence_min": 0.7},
                {"type": "brand", "value": "WebBoost Agency", "confidence_min": 0.8},
                {"type": "location", "value": "Austin, Texas", "confidence_min": 0.7},
            ],
            "noisy": [
                {"type": "product", "value": "DataFlow Analytics Platform", "confidence_min": 0.7},
                {"type": "service", "value": "Data Analysis Services", "confidence_min": 0.6},
                {"type": "location", "value": "Boston, MA", "confidence_min": 0.6},
            ],
            "minimal": [],
            "product": [
                {"type": "product", "value": "iPhone 15 Pro Max", "confidence_min": 0.9},
                {"type": "brand", "value": "Apple", "confidence_min": 0.8},
                {"type": "feature", "value": "A17 Pro chip", "confidence_min": 0.7},
                {"type": "feature", "value": "USB-C connectivity", "confidence_min": 0.6},
                {"type": "price", "value": "$1,199", "confidence_min": 0.8},
                {"type": "price", "value": "$1,299", "confidence_min": 0.8},
            ]
        }
    
    @staticmethod
    def get_all_samples() -> Dict[str, Dict[str, Any]]:
        """Get all content samples."""
        return {
            "ecommerce": BusinessContentFixtures.get_ecommerce_content(),
            "service": BusinessContentFixtures.get_service_business_content(),
            "noisy": BusinessContentFixtures.get_noisy_content(),
            "minimal": BusinessContentFixtures.get_minimal_content(),
            "product": BusinessContentFixtures.get_product_focused_content()
        }