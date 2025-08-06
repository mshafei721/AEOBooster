"""
Unit tests for the content extractor service.
"""
import pytest
import json
from src.services.content_extractor import ContentExtractor

class TestContentExtractor:
    """Test suite for ContentExtractor."""
    
    @pytest.fixture
    def extractor(self):
        """Create a content extractor instance for testing."""
        return ContentExtractor()
    
    @pytest.fixture
    def sample_html(self):
        """Sample HTML for testing."""
        return """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <title>Test Product - Best Widget Ever</title>
            <meta name="description" content="Amazing widget that solves all your problems">
            <meta name="keywords" content="widget, product, amazing">
            <meta property="og:title" content="Best Widget Ever">
            <meta property="og:description" content="OG description">
            <meta name="twitter:card" content="summary">
            <meta name="twitter:title" content="Twitter Widget Title">
            <script type="application/ld+json">
            {
                "@context": "https://schema.org",
                "@type": "Product",
                "name": "Test Widget",
                "description": "A great widget"
            }
            </script>
        </head>
        <body>
            <nav class="navigation">
                <ul>
                    <li><a href="/">Home</a></li>
                    <li><a href="/about">About</a></li>
                </ul>
            </nav>
            
            <header class="site-header">
                <h1>Site Header</h1>
            </header>
            
            <main class="main-content">
                <article>
                    <h1>Main Product Heading</h1>
                    <h2>Features</h2>
                    <p>This is the main content about our amazing product.</p>
                    <h3>Detailed Features</h3>
                    <p>More detailed information about the product features.</p>
                    
                    <div itemscope itemtype="https://schema.org/Product">
                        <span itemprop="name">Microdata Widget</span>
                        <span itemprop="price">$99.99</span>
                    </div>
                    
                    <img src="/images/widget.jpg" alt="Amazing widget photo" title="Widget Image">
                    <img src="https://cdn.example.com/hero.jpg" alt="Hero image">
                    
                    <a href="/contact">Contact us about this widget</a>
                    <a href="https://external.com/info">External info</a>
                </article>
            </main>
            
            <footer class="site-footer">
                <p>Footer content that should be filtered out</p>
            </footer>
            
            <script>
                // This script should be removed
                console.log("tracking");
            </script>
        </body>
        </html>
        """
    
    @pytest.fixture
    def blog_html(self):
        """Sample blog HTML for testing."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>How to Use Widgets - Ultimate Guide</title>
            <meta name="description" content="Complete guide to widget usage">
        </head>
        <body>
            <article class="blog-post">
                <header>
                    <h1>How to Use Widgets: Ultimate Guide</h1>
                    <p class="meta">Published on January 15, 2024 by John Doe</p>
                </header>
                
                <div class="content">
                    <h2>Introduction</h2>
                    <p>Widgets are amazing tools that can help you accomplish many tasks.</p>
                    
                    <h2>Getting Started</h2>
                    <p>First, you need to understand the basics of widget operation.</p>
                    
                    <h3>Step 1: Setup</h3>
                    <p>Begin by setting up your widget environment.</p>
                    
                    <h3>Step 2: Configuration</h3>
                    <p>Configure your widget for optimal performance.</p>
                </div>
                
                <footer class="post-footer">
                    <p>Tags: widgets, tutorial, guide</p>
                    <div class="share-buttons">
                        <a href="#" class="share">Share this post</a>
                    </div>
                </footer>
            </article>
        </body>
        </html>
        """
    
    def test_extract_title(self, extractor, sample_html):
        """Test title extraction."""
        result = extractor.extract_content(sample_html, "https://example.com")
        assert result['title'] == "Test Product - Best Widget Ever"
    
    def test_extract_meta_description(self, extractor, sample_html):
        """Test meta description extraction."""
        result = extractor.extract_content(sample_html, "https://example.com")
        assert result['meta_description'] == "Amazing widget that solves all your problems"
    
    def test_extract_meta_keywords(self, extractor, sample_html):
        """Test meta keywords extraction."""
        result = extractor.extract_content(sample_html, "https://example.com")
        assert result['meta_keywords'] == "widget, product, amazing"
    
    def test_extract_open_graph(self, extractor, sample_html):
        """Test Open Graph metadata extraction."""
        result = extractor.extract_content(sample_html, "https://example.com")
        
        og_data = result['open_graph']
        assert og_data['title'] == "Best Widget Ever"
        assert og_data['description'] == "OG description"
    
    def test_extract_twitter_card(self, extractor, sample_html):
        """Test Twitter Card metadata extraction."""
        result = extractor.extract_content(sample_html, "https://example.com")
        
        twitter_data = result['twitter_card']
        assert twitter_data['card'] == "summary"
        assert twitter_data['title'] == "Twitter Widget Title"
    
    def test_extract_structured_data_jsonld(self, extractor, sample_html):
        """Test JSON-LD structured data extraction."""
        result = extractor.extract_content(sample_html, "https://example.com")
        
        structured_data = result['structured_data']
        assert 'json_ld' in structured_data
        assert len(structured_data['json_ld']) == 1
        
        json_ld = structured_data['json_ld'][0]
        assert json_ld['@type'] == "Product"
        assert json_ld['name'] == "Test Widget"
    
    def test_extract_structured_data_microdata(self, extractor, sample_html):
        """Test microdata extraction."""
        result = extractor.extract_content(sample_html, "https://example.com")
        
        structured_data = result['structured_data']
        assert 'microdata' in structured_data
        assert len(structured_data['microdata']) >= 1
        
        # Find the Product microdata
        product_data = None
        for item in structured_data['microdata']:
            if 'Product' in item['type']:
                product_data = item
                break
        
        assert product_data is not None
        assert product_data['properties']['name'] == 'Microdata Widget'
        assert product_data['properties']['price'] == '$99.99'
    
    def test_extract_headings(self, extractor, blog_html):
        """Test heading hierarchy extraction."""
        result = extractor.extract_content(blog_html, "https://example.com")
        
        headings = result['headings']
        assert len(headings) == 5
        
        # Check heading levels and order
        expected_headings = [
            (1, "How to Use Widgets: Ultimate Guide"),
            (2, "Introduction"),
            (2, "Getting Started"),
            (3, "Step 1: Setup"),
            (3, "Step 2: Configuration")
        ]
        
        for i, (expected_level, expected_text) in enumerate(expected_headings):
            assert headings[i]['level'] == expected_level
            assert headings[i]['text'] == expected_text
            assert headings[i]['position'] == i + 1
    
    def test_extract_main_content(self, extractor, sample_html):
        """Test main content extraction with noise removal."""
        result = extractor.extract_content(sample_html, "https://example.com")
        
        content = result['content']
        
        # Should contain main content
        assert "Main Product Heading" in content
        assert "main content about our amazing product" in content
        assert "Detailed Features" in content
        
        # Should NOT contain navigation, header, footer, or script content
        assert "Site Header" not in content
        assert "Footer content" not in content
        assert "console.log" not in content
        assert "Home" not in content  # Navigation should be removed
    
    def test_extract_images(self, extractor, sample_html):
        """Test image extraction."""
        result = extractor.extract_content(sample_html, "https://example.com")
        
        images = result['images']
        assert len(images) == 2
        
        # Check first image (relative URL converted to absolute)
        img1 = images[0]
        assert img1['src'] == "https://example.com/images/widget.jpg"
        assert img1['alt'] == "Amazing widget photo"
        assert img1['title'] == "Widget Image"
        
        # Check second image (already absolute)
        img2 = images[1]
        assert img2['src'] == "https://cdn.example.com/hero.jpg"
        assert img2['alt'] == "Hero image"
    
    def test_extract_links(self, extractor, sample_html):
        """Test link extraction."""
        result = extractor.extract_content(sample_html, "https://example.com")
        
        links = result['links']
        
        # Find internal and external links
        internal_links = [link for link in links if link['type'] == 'internal']
        external_links = [link for link in links if link['type'] == 'external']
        
        assert len(internal_links) >= 1  # May have navigation links too
        assert len(external_links) == 1
        
        # Check that we have the expected internal contact link
        contact_links = [link for link in internal_links if 'contact' in link['href']]
        assert len(contact_links) == 1
        
        contact = contact_links[0]
        assert contact['href'] == "https://example.com/contact"
        assert contact['text'] == "Contact us about this widget"
        assert contact['type'] == "internal"
        
        # Check external link
        external = external_links[0]
        assert external['href'] == "https://external.com/info"
        assert external['text'] == "External info"
        assert external['type'] == "external"
    
    def test_calculate_content_metrics(self, extractor, blog_html):
        """Test content metrics calculation."""
        result = extractor.extract_content(blog_html, "https://example.com")
        
        metrics = result['content_metrics']
        
        assert 'word_count' in metrics
        assert 'character_count' in metrics
        assert 'sentence_count' in metrics
        assert 'paragraph_count' in metrics
        assert 'heading_count' in metrics
        assert 'avg_words_per_sentence' in metrics
        assert 'reading_time_minutes' in metrics
        
        # Basic validation
        assert metrics['word_count'] > 0
        assert metrics['character_count'] > 0
        assert metrics['sentence_count'] > 0
        assert metrics['heading_count'] == 5  # From blog_html
        assert metrics['reading_time_minutes'] > 0
    
    def test_extract_content_error_handling(self, extractor):
        """Test error handling with malformed HTML."""
        malformed_html = "<html><head><title>Test</head><body><p>Unclosed paragraph</body>"
        
        result = extractor.extract_content(malformed_html, "https://example.com")
        
        # Should still extract basic information
        assert result['title'] == "Test"
        assert result['url'] == "https://example.com"
        assert 'error' not in result  # Should handle gracefully
    
    def test_extract_empty_content(self, extractor):
        """Test extraction from empty or minimal HTML."""
        minimal_html = "<html><head></head><body></body></html>"
        
        result = extractor.extract_content(minimal_html, "https://example.com")
        
        assert result['title'] == ""
        assert result['meta_description'] == ""
        assert result['content'] == ""
        assert result['headings'] == []
        assert result['images'] == []
        assert result['links'] == []
    
    def test_microdata_value_extraction(self, extractor):
        """Test microdata value extraction for different attribute types."""
        html_with_various_props = """
        <div itemscope itemtype="https://schema.org/Event">
            <meta itemprop="name" content="Event Name">
            <time itemprop="startDate" datetime="2024-01-15T10:00">January 15, 2024</time>
            <a itemprop="url" href="https://example.com/event">Event Link</a>
            <img itemprop="image" src="/event-image.jpg" alt="Event">
            <span itemprop="description">Event description text</span>
        </div>
        """
        
        result = extractor.extract_content(html_with_various_props, "https://example.com")
        
        microdata = result['structured_data']['microdata']
        event_data = microdata[0]
        props = event_data['properties']
        
        assert props['name'] == "Event Name"  # From content attribute
        assert props['startDate'] == "2024-01-15T10:00"  # From datetime attribute
        assert props['url'] == "https://example.com/event"  # From href attribute
        assert props['image'] == "/event-image.jpg"  # From src attribute
        assert props['description'] == "Event description text"  # From text content

if __name__ == "__main__":
    pytest.main([__file__])