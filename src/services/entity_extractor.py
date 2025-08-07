"""
Entity extraction service using spaCy NLP for business entity recognition.
"""
import spacy
import re
from typing import List, Dict, Optional, Tuple, Any
import logging
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor

from ..models.entity import ExtractedEntity, EntityExtractionResult
from .nlp_processor import NLPProcessor
from ..utils.entity_patterns import EntityPatterns

logger = logging.getLogger(__name__)

class EntityExtractor:
    """Main entity extraction service using spaCy NLP."""
    
    def __init__(self):
        """Initialize the entity extractor with spaCy model."""
        self.nlp_processor = NLPProcessor()
        self.entity_patterns = EntityPatterns()
        self._nlp_model = None
        self._executor = ThreadPoolExecutor(max_workers=4)
        
    async def _load_spacy_model(self):
        """Load spaCy model in background thread."""
        if self._nlp_model is None:
            try:
                # Load in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                self._nlp_model = await loop.run_in_executor(
                    self._executor, 
                    self._load_model_sync
                )
                logger.info("spaCy model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load spaCy model: {e}")
                raise
                
    def _load_model_sync(self):
        """Synchronously load spaCy model."""
        try:
            # Try to load en_core_web_lg first
            nlp = spacy.load("en_core_web_lg")
        except OSError:
            # Fallback to en_core_web_sm if lg not available
            logger.warning("en_core_web_lg not found, falling back to en_core_web_sm")
            nlp = spacy.load("en_core_web_sm")
        
        # Add EntityRuler for business patterns
        if "entity_ruler" not in nlp.pipe_names:
            ruler = nlp.add_pipe("entity_ruler", before="ner")
            patterns = self.entity_patterns.get_patterns()
            if patterns:
                ruler.add_patterns(patterns)
                
        return nlp
            
    async def extract_entities_from_page(
        self, 
        project_id: str,
        page_id: str,
        page_content: Dict[str, Any],
        min_confidence: float = 0.5
    ) -> EntityExtractionResult:
        """
        Extract entities from a single crawled page.
        
        Args:
            project_id: Project identifier
            page_id: Page identifier 
            page_content: Crawled page content with fields like content_text, title, etc.
            min_confidence: Minimum confidence threshold for entities
            
        Returns:
            EntityExtractionResult with extracted entities
        """
        start_time = datetime.now()
        
        try:
            # Load spaCy model if not loaded
            await self._load_spacy_model()
            
            # Process content in background thread
            loop = asyncio.get_event_loop()
            entities = await loop.run_in_executor(
                self._executor,
                self._extract_entities_sync,
                project_id,
                page_id, 
                page_content,
                min_confidence
            )
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return EntityExtractionResult(
                project_id=project_id,
                page_id=page_id,
                entities=entities,
                processing_time_ms=processing_time,
                entities_found=len(entities),
                extraction_method="spacy",
                error=None
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            logger.error(f"Entity extraction failed for page {page_id}: {e}")
            
            return EntityExtractionResult(
                project_id=project_id,
                page_id=page_id,
                entities=[],
                processing_time_ms=processing_time,
                entities_found=0,
                extraction_method="spacy",
                error=str(e)
            )
    
    def _extract_entities_sync(
        self,
        project_id: str,
        page_id: str,
        page_content: Dict[str, Any],
        min_confidence: float
    ) -> List[ExtractedEntity]:
        """Synchronous entity extraction logic."""
        entities = []
        
        # Process different content fields
        content_fields = {
            'title': page_content.get('title', ''),
            'meta_description': page_content.get('meta_description', ''),
            'content_text': page_content.get('content_text', ''),
            'headings': self._extract_text_from_headings(page_content.get('headings', []))
        }
        
        for field_name, content in content_fields.items():
            if content and len(content.strip()) > 0:
                field_entities = self._extract_from_text(
                    content, 
                    field_name,
                    page_id,
                    min_confidence
                )
                entities.extend(field_entities)
        
        # Deduplicate and merge entities
        entities = self._deduplicate_entities(entities)
        
        return entities
    
    def _extract_text_from_headings(self, headings: List[Dict]) -> str:
        """Extract text from headings structure."""
        if not headings:
            return ""
            
        heading_texts = []
        for heading in headings:
            if isinstance(heading, dict) and 'text' in heading:
                heading_texts.append(heading['text'])
            elif isinstance(heading, str):
                heading_texts.append(heading)
                
        return " ".join(heading_texts)
    
    def _extract_from_text(
        self, 
        text: str, 
        source_field: str,
        page_id: str,
        min_confidence: float
    ) -> List[ExtractedEntity]:
        """Extract entities from a text using spaCy and patterns."""
        if not text or len(text.strip()) == 0:
            return []
            
        # Clean and preprocess text
        cleaned_text = self.nlp_processor.clean_text(text)
        
        # Process with spaCy
        doc = self._nlp_model(cleaned_text)
        
        entities = []
        
        # Extract named entities
        for ent in doc.ents:
            entity_type = self._map_spacy_label_to_business_type(ent.label_)
            if entity_type:
                confidence = self._calculate_confidence(ent, doc, source_field)
                if confidence >= min_confidence:
                    entities.append(ExtractedEntity(
                        value=ent.text,
                        normalized_value=self._normalize_entity_value(ent.text),
                        entity_type=entity_type,
                        confidence_score=confidence,
                        context=self._get_entity_context(ent, doc),
                        extraction_method="spacy_ner",
                        page_id=page_id
                    ))
        
        # Extract using custom patterns
        pattern_entities = self._extract_using_patterns(
            text, source_field, page_id, min_confidence
        )
        entities.extend(pattern_entities)
        
        return entities
    
    def _map_spacy_label_to_business_type(self, spacy_label: str) -> Optional[str]:
        """Map spaCy entity labels to business entity types."""
        label_mapping = {
            'ORG': 'brand',
            'PRODUCT': 'product',
            'MONEY': 'price', 
            'GPE': 'location',
            'LOC': 'location',
            'PERSON': 'brand',  # Could be founder, spokesperson
            'WORK_OF_ART': 'product',
            'EVENT': 'service',
        }
        return label_mapping.get(spacy_label)
    
    def _calculate_confidence(self, ent, doc, source_field: str) -> float:
        """Calculate confidence score for extracted entity."""
        base_confidence = 0.7  # Base confidence for spaCy entities
        
        # Adjust based on source field
        field_weights = {
            'title': 0.3,
            'headings': 0.2, 
            'meta_description': 0.1,
            'content_text': 0.0
        }
        
        confidence = base_confidence + field_weights.get(source_field, 0.0)
        
        # Adjust based on entity length (longer entities often more specific)
        if len(ent.text.split()) > 1:
            confidence += 0.1
            
        # Adjust based on capitalization (proper nouns often more important)
        if ent.text[0].isupper():
            confidence += 0.1
            
        return min(confidence, 1.0)
    
    def _get_entity_context(self, ent, doc, context_window: int = 10) -> str:
        """Get surrounding context for an entity."""
        start_idx = max(0, ent.start - context_window)
        end_idx = min(len(doc), ent.end + context_window)
        
        context_tokens = [token.text for token in doc[start_idx:end_idx]]
        return " ".join(context_tokens)
    
    def _extract_using_patterns(
        self, 
        text: str, 
        source_field: str,
        page_id: str, 
        min_confidence: float
    ) -> List[ExtractedEntity]:
        """Extract entities using regex patterns."""
        entities = []
        
        patterns = self.entity_patterns.get_regex_patterns()
        
        for entity_type, pattern_list in patterns.items():
            for pattern, confidence_modifier in pattern_list:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                
                for match in matches:
                    base_confidence = 0.6 + confidence_modifier
                    
                    # Adjust confidence based on source field
                    if source_field == 'title':
                        base_confidence += 0.2
                    elif source_field == 'headings':
                        base_confidence += 0.1
                        
                    if base_confidence >= min_confidence:
                        entities.append(ExtractedEntity(
                            value=match.group().strip(),
                            normalized_value=self._normalize_entity_value(match.group().strip()),
                            entity_type=entity_type,
                            confidence_score=min(base_confidence, 1.0),
                            context=self._get_match_context(match, text),
                            extraction_method="regex_pattern",
                            page_id=page_id
                        ))
        
        return entities
    
    def _get_match_context(self, match, text: str, context_window: int = 50) -> str:
        """Get context around a regex match."""
        start = max(0, match.start() - context_window)
        end = min(len(text), match.end() + context_window)
        return text[start:end].strip()
    
    def _normalize_entity_value(self, value: str) -> str:
        """Normalize entity value for deduplication."""
        # Remove extra whitespace, convert to lowercase
        normalized = re.sub(r'\s+', ' ', value.lower().strip())
        
        # Remove common prefixes/suffixes
        normalized = re.sub(r'^(the|a|an)\s+', '', normalized)
        normalized = re.sub(r'\s+(inc|llc|corp|ltd|co)\.?$', '', normalized)
        
        return normalized
    
    def _deduplicate_entities(self, entities: List[ExtractedEntity]) -> List[ExtractedEntity]:
        """Deduplicate entities based on normalized values."""
        seen = {}
        deduplicated = []
        
        for entity in entities:
            key = (entity['normalized_value'], entity['entity_type'])
            
            if key not in seen:
                seen[key] = entity
                deduplicated.append(entity)
            else:
                # Keep the entity with higher confidence
                if entity['confidence_score'] > seen[key]['confidence_score']:
                    # Remove old entity from deduplicated list
                    deduplicated = [e for e in deduplicated if not (
                        e['normalized_value'] == entity['normalized_value'] and
                        e['entity_type'] == entity['entity_type']
                    )]
                    seen[key] = entity
                    deduplicated.append(entity)
        
        return deduplicated
    
    async def extract_entities_from_project(
        self, 
        project_id: str,
        pages: List[Dict[str, Any]], 
        min_confidence: float = 0.5
    ) -> List[EntityExtractionResult]:
        """
        Extract entities from all pages in a project.
        
        Args:
            project_id: Project identifier
            pages: List of crawled page data
            min_confidence: Minimum confidence threshold
            
        Returns:
            List of EntityExtractionResult for each page
        """
        results = []
        
        for page_data in pages:
            page_id = page_data.get('id')
            if page_id:
                result = await self.extract_entities_from_page(
                    project_id, page_id, page_data, min_confidence
                )
                results.append(result)
                
        return results
    
    def __del__(self):
        """Cleanup executor on deletion."""
        if hasattr(self, '_executor'):
            self._executor.shutdown(wait=False)