"""
Entity service for database operations and entity management.
"""
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from datetime import datetime
import logging
import asyncio

from ..models.entity import Entity, EntityRelation, EntityExtractionResult, ExtractedEntity
from ..models.database import get_db
from ..models.crawled_content import CrawledPage
from .entity_extractor import EntityExtractor

logger = logging.getLogger(__name__)

class EntityService:
    """Service for managing entity extraction and database operations."""
    
    def __init__(self):
        """Initialize the entity service."""
        self.extractor = EntityExtractor()
        
    async def extract_and_store_entities(
        self, 
        project_id: str, 
        min_confidence: float = 0.5,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Extract entities from all crawled pages for a project and store them.
        
        Args:
            project_id: Project identifier
            min_confidence: Minimum confidence threshold for entities
            db: Optional database session
            
        Returns:
            Dictionary with extraction results and statistics
        """
        if db is None:
            db = next(get_db())
            
        try:
            # Get all crawled pages for the project
            pages = db.query(CrawledPage).filter(
                and_(
                    CrawledPage.project_id == project_id,
                    CrawledPage.status == "crawled"
                )
            ).all()
            
            if not pages:
                return {
                    "status": "no_pages",
                    "message": "No crawled pages found for project",
                    "entities_extracted": 0,
                    "pages_processed": 0
                }
            
            # Convert pages to dict format for extractor
            page_data = []
            for page in pages:
                page_dict = {
                    "id": page.id,
                    "title": page.title,
                    "meta_description": page.meta_description,
                    "content_text": page.content_text,
                    "headings": page.headings or [],
                    "structured_data": page.structured_data or {}
                }
                page_data.append(page_dict)
                
            # Extract entities from all pages
            extraction_results = await self.extractor.extract_entities_from_project(
                project_id, page_data, min_confidence
            )
            
            # Store entities in database
            total_entities = 0
            successful_pages = 0
            failed_pages = 0
            
            for result in extraction_results:
                if result.get("error"):
                    failed_pages += 1
                    logger.warning(f"Extraction failed for page {result.get('page_id')}: {result['error']}")
                    continue
                    
                try:
                    entities_stored = self._store_entities(db, result)
                    total_entities += entities_stored
                    successful_pages += 1
                except Exception as e:
                    failed_pages += 1
                    logger.error(f"Failed to store entities for page {result.get('page_id')}: {e}")
            
            # Commit all changes
            db.commit()
            
            # Create entity relationships
            await self._create_entity_relationships(project_id, db)
            
            return {
                "status": "completed",
                "entities_extracted": total_entities,
                "pages_processed": len(pages),
                "successful_pages": successful_pages,
                "failed_pages": failed_pages,
                "extraction_results": extraction_results
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Entity extraction and storage failed for project {project_id}: {e}")
            raise
        finally:
            db.close()
    
    def _store_entities(self, db: Session, extraction_result: EntityExtractionResult) -> int:
        """
        Store extracted entities in the database with deduplication.
        
        Args:
            db: Database session
            extraction_result: Extraction result containing entities
            
        Returns:
            Number of entities stored
        """
        if not extraction_result.get("entities"):
            return 0
            
        project_id = extraction_result["project_id"]
        page_id = extraction_result.get("page_id")
        
        entities_stored = 0
        
        for entity_data in extraction_result["entities"]:
            try:
                # Check if entity already exists (deduplication)
                existing_entity = db.query(Entity).filter(
                    and_(
                        Entity.project_id == project_id,
                        Entity.normalized_value == entity_data["normalized_value"],
                        Entity.entity_type == entity_data["entity_type"]
                    )
                ).first()
                
                if existing_entity:
                    # Update existing entity with higher confidence or frequency
                    if entity_data["confidence_score"] > existing_entity.confidence_score:
                        existing_entity.confidence_score = entity_data["confidence_score"]
                        existing_entity.context = entity_data.get("context", "")
                        
                    existing_entity.frequency += 1
                    existing_entity.updated_at = datetime.utcnow()
                    
                else:
                    # Create new entity
                    entity = Entity(
                        project_id=project_id,
                        page_id=page_id,
                        entity_type=entity_data["entity_type"],
                        value=entity_data["value"],
                        normalized_value=entity_data["normalized_value"],
                        confidence_score=entity_data["confidence_score"],
                        frequency=1,
                        context=entity_data.get("context", ""),
                        extraction_method=entity_data.get("extraction_method", "spacy")
                    )
                    
                    db.add(entity)
                    entities_stored += 1
                    
            except Exception as e:
                logger.error(f"Failed to store entity {entity_data.get('value')}: {e}")
                continue
                
        return entities_stored
    
    async def _create_entity_relationships(self, project_id: str, db: Session):
        """
        Create relationships between entities based on co-occurrence and patterns.
        
        Args:
            project_id: Project identifier
            db: Database session
        """
        try:
            # Get all entities for the project
            entities = db.query(Entity).filter(Entity.project_id == project_id).all()
            
            if len(entities) < 2:
                return
                
            # Create relationships based on simple rules
            for i, entity1 in enumerate(entities):
                for entity2 in entities[i+1:]:
                    relationship = self._determine_relationship(entity1, entity2)
                    if relationship:
                        # Check if relationship already exists
                        existing = db.query(EntityRelation).filter(
                            and_(
                                EntityRelation.entity_id == entity1.id,
                                EntityRelation.related_entity_id == entity2.id,
                                EntityRelation.relation_type == relationship["type"]
                            )
                        ).first()
                        
                        if not existing:
                            relation = EntityRelation(
                                entity_id=entity1.id,
                                related_entity_id=entity2.id,
                                relation_type=relationship["type"],
                                confidence=relationship["confidence"],
                                description=relationship.get("description", "")
                            )
                            db.add(relation)
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Failed to create entity relationships for project {project_id}: {e}")
    
    def _determine_relationship(self, entity1: Entity, entity2: Entity) -> Optional[Dict[str, Any]]:
        """
        Determine relationship between two entities.
        
        Args:
            entity1: First entity
            entity2: Second entity
            
        Returns:
            Relationship dictionary or None
        """
        # Brand-Product relationships
        if entity1.entity_type == "brand" and entity2.entity_type == "product":
            return {
                "type": "offers",
                "confidence": 0.7,
                "description": f"{entity1.value} offers {entity2.value}"
            }
        
        # Product-Feature relationships 
        if entity1.entity_type == "product" and entity2.entity_type == "feature":
            return {
                "type": "has_feature",
                "confidence": 0.6,
                "description": f"{entity1.value} has feature {entity2.value}"
            }
            
        # Service-Location relationships
        if entity1.entity_type == "service" and entity2.entity_type == "location":
            return {
                "type": "available_in", 
                "confidence": 0.5,
                "description": f"{entity1.value} available in {entity2.value}"
            }
            
        # Similar entities (potential synonyms)
        similarity = self._calculate_similarity(entity1.normalized_value, entity2.normalized_value)
        if similarity > 0.8 and entity1.entity_type == entity2.entity_type:
            return {
                "type": "similar",
                "confidence": similarity,
                "description": f"Similar entities: {entity1.value} and {entity2.value}"
            }
            
        return None
    
    def _calculate_similarity(self, value1: str, value2: str) -> float:
        """Calculate similarity between two entity values."""
        # Simple Jaccard similarity for now
        set1 = set(value1.lower().split())
        set2 = set(value2.lower().split())
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0
    
    def get_entities_for_project(
        self, 
        project_id: str,
        entity_type: Optional[str] = None,
        min_confidence: float = 0.0,
        limit: int = 50,
        offset: int = 0,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Get entities for a project with filtering and pagination.
        
        Args:
            project_id: Project identifier
            entity_type: Optional entity type filter
            min_confidence: Minimum confidence filter
            limit: Maximum number of results
            offset: Offset for pagination
            db: Optional database session
            
        Returns:
            Dictionary with entities and metadata
        """
        if db is None:
            db = next(get_db())
            
        try:
            # Build query
            query = db.query(Entity).filter(Entity.project_id == project_id)
            
            if entity_type:
                query = query.filter(Entity.entity_type == entity_type)
                
            if min_confidence > 0:
                query = query.filter(Entity.confidence_score >= min_confidence)
                
            # Get total count
            total_count = query.count()
            
            # Get paginated results ordered by confidence
            entities = query.order_by(desc(Entity.confidence_score)).offset(offset).limit(limit).all()
            
            # Convert to response format
            entity_list = []
            for entity in entities:
                entity_dict = {
                    "id": entity.id,
                    "type": entity.entity_type,
                    "value": entity.value,
                    "confidence_score": entity.confidence_score,
                    "frequency": entity.frequency,
                    "context": entity.context,
                    "extraction_method": entity.extraction_method,
                    "created_at": entity.created_at.isoformat()
                }
                entity_list.append(entity_dict)
            
            # Get statistics by type
            stats_query = db.query(
                Entity.entity_type,
                func.count(Entity.id).label("count"),
                func.avg(Entity.confidence_score).label("avg_confidence")
            ).filter(Entity.project_id == project_id).group_by(Entity.entity_type)
            
            stats = {}
            for stat in stats_query.all():
                stats[stat.entity_type] = {
                    "count": stat.count,
                    "avg_confidence": round(float(stat.avg_confidence), 2)
                }
            
            return {
                "entities": entity_list,
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "stats": stats
            }
            
        except Exception as e:
            logger.error(f"Failed to get entities for project {project_id}: {e}")
            raise
        finally:
            db.close()
    
    def delete_entities_for_project(self, project_id: str, db: Optional[Session] = None):
        """
        Delete all entities for a project.
        
        Args:
            project_id: Project identifier
            db: Optional database session
        """
        if db is None:
            db = next(get_db())
            
        try:
            # Delete entity relations first (foreign key constraint)
            entity_ids = db.query(Entity.id).filter(Entity.project_id == project_id).all()
            entity_id_list = [e.id for e in entity_ids]
            
            if entity_id_list:
                db.query(EntityRelation).filter(
                    or_(
                        EntityRelation.entity_id.in_(entity_id_list),
                        EntityRelation.related_entity_id.in_(entity_id_list)
                    )
                ).delete(synchronize_session=False)
                
                # Delete entities
                deleted_count = db.query(Entity).filter(Entity.project_id == project_id).delete()
                
                db.commit()
                logger.info(f"Deleted {deleted_count} entities for project {project_id}")
                
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to delete entities for project {project_id}: {e}")
            raise
        finally:
            db.close()