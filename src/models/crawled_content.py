"""
Database models for crawled website content and related data.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, UTC
import uuid

from .database import Base

class CrawlJob(Base):
    """Track crawling jobs and their status."""
    __tablename__ = "crawl_jobs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    status = Column(String, nullable=False, default="pending")  # pending, running, completed, failed
    base_url = Column(String, nullable=False)
    
    # Progress tracking
    pages_crawled = Column(Integer, default=0)
    pages_failed = Column(Integer, default=0)
    total_pages_found = Column(Integer, default=0)
    
    # Timing
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    
    # Configuration used for this crawl
    max_pages = Column(Integer, default=50)
    delay_seconds = Column(Float, default=1.0)
    timeout_seconds = Column(Integer, default=30)
    respect_robots = Column(String, default="true")  # Store as string for JSON compatibility
    
    # Error information
    error_message = Column(Text, nullable=True)
    
    # Relationships
    project = relationship("Project", back_populates="crawl_jobs")
    crawled_pages = relationship("CrawledPage", back_populates="crawl_job", cascade="all, delete-orphan")

class CrawledPage(Base):
    """Store individual crawled pages and their content."""
    __tablename__ = "crawled_pages"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    crawl_job_id = Column(String, ForeignKey("crawl_jobs.id"), nullable=False)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    
    # Page identification
    url = Column(String, nullable=False, index=True)
    normalized_url = Column(String, nullable=False, index=True)
    
    # Basic metadata
    title = Column(String, nullable=True)
    meta_description = Column(Text, nullable=True)
    meta_keywords = Column(String, nullable=True)
    
    # Classification
    page_type = Column(String, nullable=True, index=True)
    confidence_score = Column(Float, nullable=True)
    
    # Status tracking
    status = Column(String, nullable=False, default="pending")  # pending, crawled, failed
    crawled_at = Column(DateTime, nullable=True)
    
    # Content storage (JSON fields for flexibility)
    content_text = Column(Text, nullable=True)  # Main extracted text content
    headings = Column(JSON, nullable=True)  # Heading hierarchy
    images = Column(JSON, nullable=True)  # Image information
    links = Column(JSON, nullable=True)  # Link information
    structured_data = Column(JSON, nullable=True)  # JSON-LD, microdata, etc.
    open_graph = Column(JSON, nullable=True)  # Open Graph metadata
    twitter_card = Column(JSON, nullable=True)  # Twitter Card metadata
    content_metrics = Column(JSON, nullable=True)  # Word count, reading time, etc.
    
    # Error information for failed pages
    error_message = Column(Text, nullable=True)
    http_status_code = Column(Integer, nullable=True)
    
    # Extraction metadata
    extraction_method = Column(String, nullable=True)  # 'playwright', 'beautifulsoup'
    extraction_time_ms = Column(Integer, nullable=True)  # Time taken to extract content
    
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    
    # Relationships
    crawl_job = relationship("CrawlJob", back_populates="crawled_pages")
    project = relationship("Project", back_populates="crawled_pages")
    content_sections = relationship("PageContentSection", back_populates="page", cascade="all, delete-orphan")

class PageContentSection(Base):
    """Store detailed content sections for advanced analysis."""
    __tablename__ = "page_content_sections"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    page_id = Column(String, ForeignKey("crawled_pages.id"), nullable=False)
    
    # Section identification
    section_type = Column(String, nullable=False)  # heading, paragraph, list, table, etc.
    section_order = Column(Integer, nullable=False)  # Order within the page
    parent_section_id = Column(String, ForeignKey("page_content_sections.id"), nullable=True)
    
    # Content
    content_text = Column(Text, nullable=False)
    content_html = Column(Text, nullable=True)  # Original HTML if needed
    
    # Metadata
    heading_level = Column(Integer, nullable=True)  # For headings (1-6)
    word_count = Column(Integer, nullable=True)
    character_count = Column(Integer, nullable=True)
    
    # Additional attributes (JSON for flexibility)
    attributes = Column(JSON, nullable=True)  # CSS classes, ids, other attributes
    
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    
    # Relationships
    page = relationship("CrawledPage", back_populates="content_sections")
    parent_section = relationship("PageContentSection", remote_side=[id])
    child_sections = relationship("PageContentSection")

# Add relationships to existing models
# This will be imported in the main project model file

def add_crawl_relationships():
    """Add crawl-related relationships to existing models."""
    # Import here to avoid circular imports
    from .project import Project
    
    # Add relationship to Project model
    if not hasattr(Project, 'crawl_jobs'):
        Project.crawl_jobs = relationship("CrawlJob", back_populates="project")
    
    if not hasattr(Project, 'crawled_pages'):
        Project.crawled_pages = relationship("CrawledPage", back_populates="project")

# Content extraction result data structure for type hints
from typing import TypedDict, List, Dict, Any, Optional

class ExtractedContent(TypedDict, total=False):
    """Type hint for extracted content structure."""
    url: str
    title: str
    meta_description: str
    meta_keywords: str
    headings: List[Dict[str, Any]]
    content: str
    structured_data: Dict[str, Any]
    open_graph: Dict[str, str]
    twitter_card: Dict[str, str]
    images: List[Dict[str, str]]
    links: List[Dict[str, str]]
    content_metrics: Dict[str, Any]
    extracted_at: Optional[float]
    error: Optional[str]

class CrawlProgress(TypedDict, total=False):
    """Type hint for crawl progress updates."""
    current_url: str
    pages_crawled: int
    pages_found: int
    status: str
    error: Optional[str]