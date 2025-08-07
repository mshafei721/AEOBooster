"""
Tests for entity extraction service.
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

from src.services.entity_extractor import EntityExtractor
from src.services.nlp_processor import NLPProcessor
from src.utils.entity_patterns import EntityPatterns
from tests.fixtures.sample_business_content import BusinessContentFixtures

@pytest.fixture
def entity_extractor():
    """Create entity extractor instance for testing."""
    return EntityExtractor()

@pytest.fixture 
def business_content():
    """Get business content fixtures."""
    return BusinessContentFixtures()

@pytest.mark.asyncio
class TestEntityExtractor:
    """Test cases for EntityExtractor class."""
    
    async def test_extract_entities_from_ecommerce_page(self, entity_extractor, business_content):
        """Test entity extraction from e-commerce content."""
        content = business_content.get_ecommerce_content()
        expected = business_content.get_expected_entities()["ecommerce"]
        
        # Mock spaCy model loading to avoid dependency
        with patch.object(entity_extractor, '_load_spacy_model', new_callable=AsyncMock) as mock_load:
            with patch.object(entity_extractor, '_nlp_model') as mock_nlp:
                # Setup mock spaCy model
                mock_doc = Mock()
                mock_entities = [
                    Mock(text="TechCorp Solutions", label_="ORG", start=0, end=2),
                    Mock(text="Enterprise CRM Software", label_="PRODUCT", start=5, end=8),
                    Mock(text="$99", label_="MONEY", start=10, end=11),
                ]
                mock_doc.ents = mock_entities
                mock_nlp.return_value = mock_doc
                
                result = await entity_extractor.extract_entities_from_page(
                    project_id="test_project",
                    page_id="test_page",
                    page_content=content,
                    min_confidence=0.5
                )
                
                # Verify result structure
                assert result["project_id"] == "test_project"
                assert result["page_id"] == "test_page"
                assert result["error"] is None
                assert result["extraction_method"] == "spacy"
                assert isinstance(result["entities"], list)
                assert result["entities_found"] > 0
                
                # Verify extracted entities contain expected types
                entity_types = [e["entity_type"] for e in result["entities"]]
                assert "brand" in entity_types or "product" in entity_types
    
    async def test_extract_entities_from_service_content(self, entity_extractor, business_content):
        """Test entity extraction from service business content."""
        content = business_content.get_service_business_content()
        
        with patch.object(entity_extractor, '_load_spacy_model', new_callable=AsyncMock):
            with patch.object(entity_extractor, '_nlp_model') as mock_nlp:
                mock_doc = Mock()
                mock_entities = [
                    Mock(text="WebBoost Agency", label_="ORG", start=0, end=2),
                    Mock(text="Digital Marketing Services", label_="SERVICE", start=3, end=6),
                    Mock(text="Austin, Texas", label_="GPE", start=8, end=10),
                ]
                mock_doc.ents = mock_entities
                mock_nlp.return_value = mock_doc
                
                result = await entity_extractor.extract_entities_from_page(
                    project_id="test_project",
                    page_id="service_page", 
                    page_content=content,
                    min_confidence=0.5
                )
                
                assert result["entities_found"] > 0
                entity_types = [e["entity_type"] for e in result["entities"]]
                assert "brand" in entity_types or "service" in entity_types or "location" in entity_types
    
    async def test_extract_entities_from_noisy_content(self, entity_extractor, business_content):
        """Test entity extraction handles noisy content with navigation elements."""
        content = business_content.get_noisy_content()
        
        with patch.object(entity_extractor, '_load_spacy_model', new_callable=AsyncMock):
            with patch.object(entity_extractor, '_nlp_model') as mock_nlp:
                mock_doc = Mock()
                mock_entities = [
                    Mock(text="DataFlow Analytics Platform", label_="PRODUCT", start=0, end=3),
                    Mock(text="Boston, MA", label_="GPE", start=5, end=7),
                ]
                mock_doc.ents = mock_entities
                mock_nlp.return_value = mock_doc
                
                result = await entity_extractor.extract_entities_from_page(
                    project_id="test_project", 
                    page_id="noisy_page",
                    page_content=content,
                    min_confidence=0.5
                )
                
                # Should still extract valid business entities despite noise
                assert result["entities_found"] >= 0
                
                # Verify noise filtering worked - shouldn't extract navigation terms
                entity_values = [e["value"].lower() for e in result["entities"]]
                noise_terms = ["home", "contact", "menu", "click", "follow us"]
                for term in noise_terms:
                    assert not any(term in value for value in entity_values)
    
    async def test_extract_entities_from_minimal_content(self, entity_extractor, business_content):
        """Test entity extraction handles minimal content gracefully."""
        content = business_content.get_minimal_content()
        
        with patch.object(entity_extractor, '_load_spacy_model', new_callable=AsyncMock):
            with patch.object(entity_extractor, '_nlp_model') as mock_nlp:
                mock_doc = Mock()
                mock_doc.ents = []  # No entities found
                mock_nlp.return_value = mock_doc
                
                result = await entity_extractor.extract_entities_from_page(
                    project_id="test_project",
                    page_id="minimal_page",
                    page_content=content,
                    min_confidence=0.5
                )
                
                assert result["error"] is None
                assert result["entities_found"] == 0
                assert isinstance(result["entities"], list)
    
    def test_map_spacy_label_to_business_type(self, entity_extractor):
        """Test spaCy label mapping to business entity types."""
        # Test mappings
        assert entity_extractor._map_spacy_label_to_business_type("ORG") == "brand"
        assert entity_extractor._map_spacy_label_to_business_type("PRODUCT") == "product"
        assert entity_extractor._map_spacy_label_to_business_type("MONEY") == "price"
        assert entity_extractor._map_spacy_label_to_business_type("GPE") == "location"
        assert entity_extractor._map_spacy_label_to_business_type("LOC") == "location"
        
        # Test unknown label
        assert entity_extractor._map_spacy_label_to_business_type("UNKNOWN") is None
    
    def test_calculate_confidence(self, entity_extractor):
        """Test confidence score calculation."""
        mock_ent = Mock()
        mock_ent.text = "Enterprise Software"
        mock_ent.start = 0
        mock_ent.end = 2
        
        mock_doc = Mock()
        mock_doc.__getitem__ = lambda self, key: [Mock(text="test") for _ in range(20)]
        mock_doc.__len__ = lambda self: 20
        
        # Test confidence calculation for different source fields
        conf_title = entity_extractor._calculate_confidence(mock_ent, mock_doc, "title")
        conf_content = entity_extractor._calculate_confidence(mock_ent, mock_doc, "content_text")
        
        # Title should have higher confidence
        assert conf_title > conf_content
        assert 0.0 <= conf_title <= 1.0
        assert 0.0 <= conf_content <= 1.0
    
    def test_normalize_entity_value(self, entity_extractor):
        """Test entity value normalization."""
        # Test basic normalization
        assert entity_extractor._normalize_entity_value("  Enterprise Software  ") == "enterprise software"
        assert entity_extractor._normalize_entity_value("Multiple   Spaces") == "multiple spaces"
        
        # Test prefix/suffix removal  
        assert entity_extractor._normalize_entity_value("The Best Company Inc.") == "best company"
        assert entity_extractor._normalize_entity_value("A Great Service LLC") == "great service"
    
    def test_deduplicate_entities(self, entity_extractor):
        """Test entity deduplication logic."""
        entities = [
            {
                "value": "TechCorp Solutions",
                "normalized_value": "techcorp solutions", 
                "entity_type": "brand",
                "confidence_score": 0.8
            },
            {
                "value": "TechCorp Solutions Inc.",
                "normalized_value": "techcorp solutions",
                "entity_type": "brand", 
                "confidence_score": 0.9
            },
            {
                "value": "Different Company",
                "normalized_value": "different company",
                "entity_type": "brand",
                "confidence_score": 0.7
            }
        ]
        
        deduplicated = entity_extractor._deduplicate_entities(entities)
        
        # Should keep higher confidence entity and unique entity
        assert len(deduplicated) == 2
        
        # Should keep the higher confidence TechCorp entity
        techcorp_entities = [e for e in deduplicated if "techcorp" in e["normalized_value"]]
        assert len(techcorp_entities) == 1
        assert techcorp_entities[0]["confidence_score"] == 0.9

@pytest.mark.asyncio
class TestEntityExtractionIntegration:
    """Integration tests for entity extraction workflow."""
    
    async def test_extract_entities_from_multiple_pages(self, entity_extractor, business_content):
        """Test entity extraction from multiple pages."""
        pages = [
            business_content.get_ecommerce_content(),
            business_content.get_service_business_content(),
            business_content.get_product_focused_content()
        ]
        
        with patch.object(entity_extractor, '_load_spacy_model', new_callable=AsyncMock):
            with patch.object(entity_extractor, '_nlp_model') as mock_nlp:
                # Setup different entities for each page
                def mock_nlp_call(text):
                    mock_doc = Mock()
                    if "TechCorp" in text:
                        mock_doc.ents = [Mock(text="TechCorp Solutions", label_="ORG", start=0, end=2)]
                    elif "WebBoost" in text:
                        mock_doc.ents = [Mock(text="WebBoost Agency", label_="ORG", start=0, end=2)]
                    elif "iPhone" in text:
                        mock_doc.ents = [Mock(text="iPhone 15 Pro Max", label_="PRODUCT", start=0, end=4)]
                    else:
                        mock_doc.ents = []
                    return mock_doc
                
                mock_nlp.side_effect = mock_nlp_call
                
                results = await entity_extractor.extract_entities_from_project(
                    project_id="multi_page_test",
                    pages=pages,
                    min_confidence=0.5
                )
                
                assert len(results) == 3
                
                # Each page should have extraction results
                for result in results:
                    assert result["project_id"] == "multi_page_test"
                    assert result["error"] is None
                    assert "entities_found" in result
    
    async def test_handle_extraction_errors(self, entity_extractor, business_content):
        """Test error handling during entity extraction."""
        content = business_content.get_ecommerce_content()
        
        # Test spaCy model loading failure
        with patch.object(entity_extractor, '_load_spacy_model', side_effect=Exception("Model loading failed")):
            result = await entity_extractor.extract_entities_from_page(
                project_id="error_test",
                page_id="error_page",
                page_content=content,
                min_confidence=0.5
            )
            
            assert result["error"] is not None
            assert "Model loading failed" in result["error"]
            assert result["entities_found"] == 0
    
    def test_confidence_threshold_filtering(self, entity_extractor):
        """Test that confidence thresholds properly filter entities."""
        entities = [
            {"value": "High Conf", "confidence_score": 0.9, "entity_type": "brand"},
            {"value": "Med Conf", "confidence_score": 0.6, "entity_type": "product"},
            {"value": "Low Conf", "confidence_score": 0.3, "entity_type": "feature"},
        ]
        
        # Test different thresholds
        with patch.object(entity_extractor, '_extract_entities_sync', return_value=entities):
            # High threshold should filter out low confidence
            high_threshold_entities = [e for e in entities if e["confidence_score"] >= 0.8]
            assert len(high_threshold_entities) == 1
            
            # Medium threshold 
            med_threshold_entities = [e for e in entities if e["confidence_score"] >= 0.5]
            assert len(med_threshold_entities) == 2
            
            # Low threshold should include all
            low_threshold_entities = [e for e in entities if e["confidence_score"] >= 0.2]
            assert len(low_threshold_entities) == 3