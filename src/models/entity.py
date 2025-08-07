"""
Database models for entity extraction and storage.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float, Index
from sqlalchemy.orm import relationship
from datetime import datetime, UTC
import uuid

from .database import Base

class Entity(Base):
    """Store extracted business entities with relationships to projects and pages."""
    __tablename__ = "entities"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"), nullable=False, index=True)
    page_id = Column(String, ForeignKey("crawled_pages.id"), nullable=True)
    
    # Entity classification
    entity_type = Column(String, nullable=False, index=True)  # product, service, brand, feature, location, price
    value = Column(String, nullable=False, index=True)  # the extracted entity text
    normalized_value = Column(String, nullable=False, index=True)  # normalized version for deduplication
    
    # Quality metrics
    confidence_score = Column(Float, nullable=False, default=0.0)  # 0.0 to 1.0
    frequency = Column(Integer, nullable=False, default=1)  # how often it appears across pages
    
    # Context information
    context = Column(Text, nullable=True)  # surrounding text for validation
    extraction_method = Column(String, nullable=False)  # 'spacy', 'regex', 'pattern'
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    
    # Relationships
    project = relationship("Project", back_populates="entities")
    page = relationship("CrawledPage", back_populates="entities")
    
    # Relationships for entity relations
    parent_relations = relationship(
        "EntityRelation", 
        foreign_keys="EntityRelation.entity_id",
        back_populates="entity",
        cascade="all, delete-orphan"
    )
    child_relations = relationship(
        "EntityRelation",
        foreign_keys="EntityRelation.related_entity_id", 
        back_populates="related_entity",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<Entity(type='{self.entity_type}', value='{self.value}', confidence={self.confidence_score})>"

class EntityRelation(Base):
    """Store relationships between entities."""
    __tablename__ = "entity_relations"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    entity_id = Column(String, ForeignKey("entities.id"), nullable=False)
    related_entity_id = Column(String, ForeignKey("entities.id"), nullable=False)
    
    # Relationship classification
    relation_type = Column(String, nullable=False)  # parent, child, synonym, related
    confidence = Column(Float, nullable=False, default=0.0)  # confidence in this relationship
    
    # Context
    description = Column(String, nullable=True)  # human-readable description of the relationship
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    
    # Relationships
    entity = relationship("Entity", foreign_keys=[entity_id], back_populates="parent_relations")
    related_entity = relationship("Entity", foreign_keys=[related_entity_id], back_populates="child_relations")
    
    def __repr__(self):
        return f"<EntityRelation(type='{self.relation_type}', confidence={self.confidence})>"

# Create composite indexes for performance
Index('idx_entity_type_confidence', Entity.entity_type, Entity.confidence_score.desc())
Index('idx_entity_project_type', Entity.project_id, Entity.entity_type)
Index('idx_entity_value_normalized', Entity.normalized_value, Entity.entity_type)

# Add relationships to existing models
def add_entity_relationships():
    """Add entity-related relationships to existing models."""
    # Import here to avoid circular imports
    from .project import Project
    from .crawled_content import CrawledPage
    
    # Add relationship to Project model
    if not hasattr(Project, 'entities'):
        Project.entities = relationship("Entity", back_populates="project")
    
    # Add relationship to CrawledPage model 
    if not hasattr(CrawledPage, 'entities'):
        CrawledPage.entities = relationship("Entity", back_populates="page")

# Type definitions for entity extraction results
from typing import TypedDict, List, Dict, Any, Optional

class ExtractedEntity(TypedDict, total=False):
    """Type hint for individual extracted entity."""
    value: str
    normalized_value: str
    entity_type: str
    confidence_score: float
    context: str
    extraction_method: str
    page_id: Optional[str]

class EntityExtractionResult(TypedDict, total=False):
    """Type hint for entity extraction results."""
    project_id: str
    page_id: Optional[str]
    entities: List[ExtractedEntity]
    processing_time_ms: float
    entities_found: int
    extraction_method: str
    error: Optional[str]