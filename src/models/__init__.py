# Models package initialization
from .database import Base, get_db, SessionLocal, engine
from .project import User, Project
from .crawled_content import CrawlJob, CrawledPage, PageContentSection, add_crawl_relationships
from .entity import Entity, EntityRelation, add_entity_relationships

# Initialize relationships
add_crawl_relationships()
add_entity_relationships()

__all__ = [
    "Base", "get_db", "SessionLocal", "engine",
    "User", "Project", 
    "CrawlJob", "CrawledPage", "PageContentSection",
    "Entity", "EntityRelation"
]