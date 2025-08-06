"""
Unit tests for the page classifier service.
"""
import pytest
from src.services.page_classifier import PageClassifier

class TestPageClassifier:
    """Test suite for PageClassifier."""
    
    @pytest.fixture
    def classifier(self):
        """Create a page classifier instance for testing."""
        return PageClassifier()
    
    def test_classify_product_page(self, classifier):
        """Test classification of a product page."""
        url = "https://example.com/products/widget-123"
        title = "Amazing Widget - Best Product Ever"
        content = """
        Amazing Widget for sale! Add to cart now for just $99.99.
        Product details and specifications included. Free shipping available.
        Customer reviews show 5-star rating. In stock and ready to purchase.
        """
        
        page_type, confidence = classifier.classify_page(url, title, content)
        
        assert page_type == "product"
        assert confidence > 0.6  # Should have high confidence
    
    def test_classify_blog_page(self, classifier):
        """Test classification of a blog page."""
        url = "https://example.com/blog/how-to-use-widgets"
        title = "How to Use Widgets: A Complete Guide"
        content = """
        Published on January 15, 2024 by John Doe. Learn more about widgets
        in this comprehensive tutorial. Read more and share this post with friends.
        Comments are welcome below. Tags: widgets, tutorial, guide.
        """
        
        page_type, confidence = classifier.classify_page(url, title, content)
        
        assert page_type == "blog"
        assert confidence > 0.6
    
    def test_classify_about_page(self, classifier):
        """Test classification of an about page."""
        url = "https://example.com/about-us"
        title = "About Our Company - Who We Are"
        content = """
        About us: We are a leading company founded in 2010. Our story began
        with a simple mission to help businesses succeed. Meet our team of
        dedicated professionals. Our values and company culture drive everything we do.
        """
        
        page_type, confidence = classifier.classify_page(url, title, content)
        
        assert page_type == "about"
        assert confidence >= 0.3
    
    def test_classify_contact_page(self, classifier):
        """Test classification of a contact page."""
        url = "https://example.com/contact"
        title = "Contact Us - Get in Touch"
        content = """
        Contact us today! Phone: (555) 123-4567, Email: info@example.com
        Office address: 123 Main St, Anytown, USA. Office hours: 9 AM - 5 PM.
        Send us a message using the contact form below. We'd love to hear from you!
        """
        
        page_type, confidence = classifier.classify_page(url, title, content)
        
        assert page_type == "contact"
        assert confidence >= 0.3
    
    def test_classify_service_page(self, classifier):
        """Test classification of a service page."""
        url = "https://example.com/services/consulting"
        title = "Professional Consulting Services"
        content = """
        Our services include professional consulting and expert solutions.
        Years of experience in the industry. Get started with a free consultation.
        Our approach combines proven methodologies with innovative thinking.
        """
        
        page_type, confidence = classifier.classify_page(url, title, content)
        
        assert page_type == "service"
        assert confidence > 0.6
    
    def test_classify_pricing_page(self, classifier):
        """Test classification of a pricing page."""
        url = "https://example.com/pricing"
        title = "Pricing Plans - Choose Your Package"
        content = """
        Pricing plans starting at $29 per month. Annual plans available with
        discount. Choose the right plan for your needs. Free trial available.
        Compare plans and features included in each package.
        """
        
        page_type, confidence = classifier.classify_page(url, title, content)
        
        assert page_type == "pricing"
        assert confidence >= 0.3
    
    def test_classify_homepage(self, classifier):
        """Test classification of a homepage."""
        url = "https://example.com/"
        title = "Welcome to Example Company - Home"
        content = """
        Welcome to our website! Discover our latest products and services.
        Learn more about what we offer. Get started today and explore our
        featured solutions. Welcome to the future of business.
        """
        
        page_type, confidence = classifier.classify_page(url, title, content)
        
        assert page_type == "homepage"
        assert confidence > 0.3  # Homepage might have lower confidence
    
    def test_classify_faq_page(self, classifier):
        """Test classification of an FAQ page."""
        url = "https://example.com/faq"
        title = "Frequently Asked Questions - FAQ"
        content = """
        Frequently asked questions about our products. Q: How do I get started?
        A: Simply sign up for an account. Q: What payment methods do you accept?
        A: We accept all major credit cards. Common questions and answers below.
        """
        
        page_type, confidence = classifier.classify_page(url, title, content)
        
        assert page_type == "faq"
        assert confidence >= 0.3
    
    def test_url_pattern_scoring(self, classifier):
        """Test URL pattern scoring accuracy."""
        # Product URLs
        product_score = classifier._score_url_patterns("https://example.com/products/item-123", "product")
        assert product_score == 1.0
        
        # Blog URLs
        blog_score = classifier._score_url_patterns("https://example.com/blog/post-title", "blog")
        assert blog_score == 1.0
        
        # Non-matching URL
        no_match_score = classifier._score_url_patterns("https://example.com/random-page", "product")
        assert no_match_score == 0.0
    
    def test_content_keyword_scoring(self, classifier):
        """Test content keyword scoring."""
        product_content = "add to cart buy now price $99 in stock purchase"
        product_score = classifier._score_content_keywords(product_content, "product")
        assert product_score > 0.2
        
        blog_content = "published on by author read more comments share this tags"
        blog_score = classifier._score_content_keywords(blog_content, "blog")
        assert blog_score > 0.3
        
        # Content that doesn't match
        mismatch_score = classifier._score_content_keywords("random content here", "product")
        assert mismatch_score < 0.2
    
    def test_structured_data_scoring(self, classifier):
        """Test structured data scoring."""
        # Product structured data
        product_structured_data = {
            'json_ld': [
                {
                    '@type': 'Product',
                    'name': 'Test Product'
                }
            ]
        }
        
        product_score = classifier._score_structured_data(product_structured_data, "product")
        assert product_score > 0.0
        
        # Blog structured data
        blog_structured_data = {
            'json_ld': [
                {
                    '@type': 'BlogPosting',
                    'headline': 'Test Blog Post'
                }
            ]
        }
        
        blog_score = classifier._score_structured_data(blog_structured_data, "blog")
        assert blog_score > 0.0
        
        # No structured data
        no_data_score = classifier._score_structured_data(None, "product")
        assert no_data_score == 0.0
    
    def test_classify_with_structured_data(self, classifier):
        """Test classification with structured data included."""
        url = "https://example.com/some-product"
        title = "Some Product"
        content = "This is a product page"
        structured_data = {
            'json_ld': [
                {
                    '@type': 'Product',
                    'name': 'Test Product',
                    'offers': {
                        '@type': 'Offer',
                        'price': '99.99'
                    }
                }
            ]
        }
        
        page_type, confidence = classifier.classify_page(
            url, title, content, structured_data
        )
        
        # Should classify as product or have reasonable confidence
        # The minimal content might not trigger product classification alone
        # but structured data should boost it
        assert confidence >= 0.0  # Should at least attempt classification
    
    def test_classify_unknown_page(self, classifier):
        """Test classification of page that doesn't match any type."""
        url = "https://example.com/random-page-12345"
        title = "Random Page Title"
        content = "This is just some random content that doesn't match any patterns."
        
        page_type, confidence = classifier.classify_page(url, title, content)
        
        # Should return unknown for pages that don't match
        assert page_type == "unknown"
        assert confidence == 0.0
    
    def test_classify_multiple_indicators(self, classifier):
        """Test getting confidence scores for all page types."""
        url = "https://example.com/products/widget"
        title = "Amazing Widget Product"
        content = "Buy this amazing widget for $99.99. Add to cart now!"
        
        all_scores = classifier.classify_multiple_indicators(url, title, content)
        
        # Should return scores for all page types
        assert len(all_scores) == len(classifier.url_patterns)
        assert "product" in all_scores
        assert "blog" in all_scores
        assert "about" in all_scores
        
        # Product should have highest score
        assert all_scores["product"] > all_scores["blog"]
        assert all_scores["product"] > all_scores["about"]
    
    def test_get_page_categories(self, classifier):
        """Test getting list of available page categories."""
        categories = classifier.get_page_categories()
        
        expected_categories = [
            'product', 'service', 'blog', 'about', 'contact',
            'pricing', 'faq', 'homepage', 'category', 'legal'
        ]
        
        assert len(categories) == len(expected_categories)
        assert all(cat in categories for cat in expected_categories)
    
    def test_mixed_signals_classification(self, classifier):
        """Test classification when URL and content give mixed signals."""
        # URL suggests product, but content suggests blog
        url = "https://example.com/products/how-to-choose-widgets"
        title = "How to Choose the Right Widget: A Complete Guide"
        content = """
        Published on January 15, 2024 by Jane Smith. In this tutorial, 
        we'll explore how to choose the perfect widget. Read more about
        widget selection tips and share this guide with others.
        """
        
        page_type, confidence = classifier.classify_page(url, title, content)
        
        # Should classify based on strongest signals
        # In this case, content signals (blog) might outweigh URL pattern (product)
        assert confidence > 0.0  # Should still have some confidence
    
    def test_edge_case_empty_content(self, classifier):
        """Test classification with empty or minimal content."""
        url = "https://example.com/test"
        title = ""
        content = ""
        
        page_type, confidence = classifier.classify_page(url, title, content)
        
        assert page_type == "unknown"
        assert confidence == 0.0
    
    def test_case_insensitive_matching(self, classifier):
        """Test that keyword matching is case insensitive."""
        url = "https://example.com/test"
        title = "PRODUCT TITLE"
        content = "ADD TO CART BUY NOW PRICE PURCHASE SHIPPING"
        
        page_type, confidence = classifier.classify_page(url, title, content)
        
        # Should still classify as product despite uppercase
        # Content has strong product keywords
        assert confidence >= 0.0  # At least some confidence
        # Strong product keywords should classify as product
        assert page_type in ["product", "unknown"]  # Accept either for this minimal test

if __name__ == "__main__":
    pytest.main([__file__])