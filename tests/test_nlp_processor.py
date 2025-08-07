"""
Tests for NLP processor and text processing utilities.
"""
import pytest
from src.services.nlp_processor import NLPProcessor
from tests.fixtures.sample_business_content import BusinessContentFixtures

@pytest.fixture
def nlp_processor():
    """Create NLP processor instance for testing."""
    return NLPProcessor()

@pytest.fixture
def business_content():
    """Get business content fixtures."""
    return BusinessContentFixtures()

class TestNLPProcessor:
    """Test cases for NLPProcessor class."""
    
    def test_clean_text_basic(self, nlp_processor):
        """Test basic text cleaning functionality."""
        # Test HTML entity decoding
        text = "Company &amp; Solutions &lt;Enterprise&gt;"
        cleaned = nlp_processor.clean_text(text)
        assert "&" in cleaned and "<Enterprise>" in cleaned
        
        # Test whitespace normalization
        text = "Multiple    spaces   and\n\ntabs"
        cleaned = nlp_processor.clean_text(text)
        assert cleaned == "Multiple spaces and tabs"
        
        # Test empty/None handling
        assert nlp_processor.clean_text("") == ""
        assert nlp_processor.clean_text(None) == ""
    
    def test_clean_text_html_removal(self, nlp_processor):
        """Test HTML tag removal."""
        text = "<div>Enterprise <strong>CRM</strong> Software</div>"
        cleaned = nlp_processor.clean_text(text)
        assert "<div>" not in cleaned
        assert "<strong>" not in cleaned
        assert "Enterprise CRM Software" in cleaned
    
    def test_clean_text_noise_patterns(self, nlp_processor):
        """Test removal of noise patterns."""
        text = "Great Software! Copyright © 2024 Company Inc. All rights reserved. Terms of Service"
        cleaned = nlp_processor.clean_text(text)
        
        # Should remove copyright notice and legal terms
        assert "Copyright" not in cleaned
        assert "All rights reserved" not in cleaned
        assert "Terms of Service" not in cleaned
        assert "Great Software!" in cleaned
    
    def test_clean_text_navigation_patterns(self, nlp_processor):
        """Test removal of navigation patterns."""
        text = "Home About Contact Services Our great product line Next Previous"
        cleaned = nlp_processor.clean_text(text)
        
        # Should remove navigation terms but keep content
        assert "Home About Contact" not in cleaned or len(cleaned) < len(text)
        assert "great product line" in cleaned
    
    def test_segment_content_complete(self, nlp_processor, business_content):
        """Test content segmentation with complete page content."""
        content = business_content.get_ecommerce_content()
        segments = nlp_processor.segment_content(content)
        
        # Should create segments for all major content types
        assert "title" in segments
        assert "meta_description" in segments
        assert "headings" in segments
        assert "content_main" in segments
        assert "structured_data" in segments
        
        # Verify content is present
        assert "Enterprise CRM Software" in segments["title"]
        assert "Advanced CRM platform" in segments["meta_description"]
        assert len(segments["content_main"]) > 0
    
    def test_segment_content_minimal(self, nlp_processor, business_content):
        """Test content segmentation with minimal content."""
        content = business_content.get_minimal_content()
        segments = nlp_processor.segment_content(content)
        
        # Should handle minimal content gracefully
        assert "title" in segments
        assert segments["title"] == "Page"
        assert segments.get("meta_description", "") == ""
        assert segments.get("content_main", "") == "Welcome to our site."
    
    def test_extract_heading_text(self, nlp_processor):
        """Test heading text extraction."""
        headings = [
            {"level": 1, "text": "Main Heading"},
            {"level": 2, "text": "Sub Heading"},
            {"content": "Another Heading"},  # Different format
            "String Heading"  # Simple string
        ]
        
        heading_text = nlp_processor._extract_heading_text(headings)
        
        assert "Main Heading" in heading_text
        assert "Sub Heading" in heading_text  
        assert "Another Heading" in heading_text
        assert "String Heading" in heading_text
        
        # Should use separator
        assert "|" in heading_text
    
    def test_split_content(self, nlp_processor):
        """Test content splitting for large texts."""
        # Test short content (should not split)
        short_content = "This is short content."
        result = nlp_processor._split_content(short_content)
        assert result["main"] == short_content
        assert result["secondary"] == ""
        
        # Test long content (should split)
        long_content = "A" * 3000  # Longer than default max_main_length
        result = nlp_processor._split_content(long_content, max_main_length=1000)
        assert len(result["main"]) <= 1000
        assert len(result["secondary"]) > 0
        assert len(result["main"]) + len(result["secondary"]) == len(long_content)
    
    def test_extract_structured_data_text(self, nlp_processor):
        """Test structured data text extraction."""
        structured_data = {
            "@type": "Product",
            "name": "Enterprise Software",
            "brand": {
                "@type": "Brand", 
                "name": "TechCorp"
            },
            "offers": {
                "price": "99.00",
                "priceCurrency": "USD"
            },
            "description": "Advanced business solution",
            "irrelevant_field": "Should be ignored"
        }
        
        text = nlp_processor._extract_structured_data_text(structured_data)
        
        # Should extract business-relevant fields
        assert "Enterprise Software" in text
        assert "TechCorp" in text
        assert "Advanced business solution" in text
        
        # Should include price information
        assert "99.00" in text
    
    def test_filter_noise_entities(self, nlp_processor):
        """Test entity noise filtering."""
        entities = [
            "Enterprise Software",  # Good entity
            "TechCorp Solutions",   # Good entity
            "click",               # Noise word
            "here",                # Noise word
            "Home",                # Navigation
            "see",                 # Noise word
            "A",                   # Too short
            "$$$",                 # Mostly punctuation
            "Great Product Line",   # Good entity
            "menu"                 # Navigation
        ]
        
        filtered = nlp_processor.filter_noise_entities(entities)
        
        # Should keep good entities
        assert "Enterprise Software" in filtered
        assert "TechCorp Solutions" in filtered
        assert "Great Product Line" in filtered
        
        # Should remove noise
        assert "click" not in filtered
        assert "here" not in filtered
        assert "Home" not in filtered
        assert "see" not in filtered
        assert "A" not in filtered
        assert "$$$" not in filtered
    
    def test_calculate_content_importance_score(self, nlp_processor):
        """Test content importance scoring."""
        # Test different source fields
        title_score = nlp_processor.calculate_content_importance_score("Enterprise Software", "title")
        content_score = nlp_processor.calculate_content_importance_score("Enterprise Software", "content_text")
        
        assert title_score > content_score
        assert 0.0 <= title_score <= 1.0
        assert 0.0 <= content_score <= 1.0
        
        # Test content characteristics
        price_content = "Starting at $99 per month"
        price_score = nlp_processor.calculate_content_importance_score(price_content, "content_text")
        
        regular_content = "This is regular content"
        regular_score = nlp_processor.calculate_content_importance_score(regular_content, "content_text")
        
        # Price content should score higher
        assert price_score > regular_score
    
    def test_segment_content_with_noisy_input(self, nlp_processor, business_content):
        """Test content segmentation handles noisy input."""
        content = business_content.get_noisy_content()
        segments = nlp_processor.segment_content(content)
        
        # Should still extract segments
        assert "title" in segments
        assert "content_main" in segments
        
        # Content should be cleaned
        main_content = segments["content_main"]
        assert len(main_content) > 0
        
        # Should reduce noise but keep business content
        assert "DataFlow Analytics Platform" in main_content or "Data Analysis Services" in main_content

class TestNLPProcessorIntegration:
    """Integration tests for NLP processor with real content."""
    
    def test_process_ecommerce_content_end_to_end(self, nlp_processor, business_content):
        """Test complete processing of e-commerce content."""
        content = business_content.get_ecommerce_content()
        
        # Segment content
        segments = nlp_processor.segment_content(content)
        
        # Calculate importance scores
        title_importance = nlp_processor.calculate_content_importance_score(
            segments["title"], "title"
        )
        content_importance = nlp_processor.calculate_content_importance_score(
            segments["content_main"], "content_main"
        )
        
        # Title should be more important
        assert title_importance > content_importance
        
        # Both should be reasonably high for business content
        assert title_importance > 0.7
        assert content_importance > 0.4
    
    def test_process_service_content_end_to_end(self, nlp_processor, business_content):
        """Test complete processing of service business content."""
        content = business_content.get_service_business_content()
        
        segments = nlp_processor.segment_content(content)
        
        # Should extract service-related information
        title_clean = nlp_processor.clean_text(segments["title"])
        content_clean = nlp_processor.clean_text(segments["content_main"])
        
        assert "Digital Marketing Services" in title_clean
        assert "SEO" in content_clean or "Web Development" in content_clean
        
        # Should handle structured data
        if segments.get("structured_data"):
            assert len(segments["structured_data"]) > 0
    
    def test_handle_edge_cases(self, nlp_processor):
        """Test handling of edge cases and malformed input."""
        edge_cases = [
            {"title": None, "content_text": "Valid content"},
            {"title": "", "content_text": ""},
            {"title": "   ", "content_text": "   "},
            {"headings": [{"invalid": "structure"}]},
            {"structured_data": {"nested": {"deeply": {"nested": "value"}}}},
        ]
        
        for content in edge_cases:
            # Should not raise exceptions
            try:
                segments = nlp_processor.segment_content(content)
                assert isinstance(segments, dict)
            except Exception as e:
                pytest.fail(f"Failed to handle edge case {content}: {e}")
    
    def test_performance_with_large_content(self, nlp_processor):
        """Test performance with large content volumes."""
        # Create large content
        large_content = {
            "title": "Enterprise Software Solution",
            "content_text": "Business content. " * 1000,  # ~20KB of content
            "headings": [{"text": f"Heading {i}"} for i in range(50)]
        }
        
        # Should process without significant delay
        import time
        start_time = time.time()
        
        segments = nlp_processor.segment_content(large_content)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should complete in reasonable time (adjust threshold as needed)
        assert processing_time < 5.0  # 5 seconds max
        
        # Should still produce valid segments
        assert "content_main" in segments
        assert "content_secondary" in segments
        assert len(segments["content_main"]) > 0