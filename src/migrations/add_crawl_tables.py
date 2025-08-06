"""
Migration script to create crawl-related tables.

Creates tables for:
- crawl_jobs: Track crawling jobs and their status
- crawled_pages: Store individual crawled pages and content
- page_content_sections: Detailed content sections for advanced analysis

To run: python src/migrations/add_crawl_tables.py
"""

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """Create crawl-related tables if they don't exist."""
    
    # Get database URL from environment or use default
    database_url = os.getenv("DATABASE_URL", "sqlite:///./test.db")
    
    # Create engine
    engine = create_engine(database_url)
    
    try:
        with engine.connect() as conn:
            # Check if tables exist
            existing_tables = []
            
            if "sqlite" in database_url.lower():
                # SQLite specific query
                result = conn.execute(text("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name IN ('crawl_jobs', 'crawled_pages', 'page_content_sections')
                """))
                existing_tables = [row[0] for row in result]
            else:
                # PostgreSQL specific query (for future)
                result = conn.execute(text("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name IN ('crawl_jobs', 'crawled_pages', 'page_content_sections')
                """))
                existing_tables = [row[0] for row in result]
            
            # Create crawl_jobs table
            if 'crawl_jobs' not in existing_tables:
                conn.execute(text("""
                    CREATE TABLE crawl_jobs (
                        id VARCHAR PRIMARY KEY,
                        project_id VARCHAR NOT NULL,
                        status VARCHAR NOT NULL DEFAULT 'pending',
                        base_url VARCHAR NOT NULL,
                        pages_crawled INTEGER DEFAULT 0,
                        pages_failed INTEGER DEFAULT 0,
                        total_pages_found INTEGER DEFAULT 0,
                        started_at DATETIME,
                        completed_at DATETIME,
                        created_at DATETIME NOT NULL,
                        max_pages INTEGER DEFAULT 50,
                        delay_seconds REAL DEFAULT 1.0,
                        timeout_seconds INTEGER DEFAULT 30,
                        respect_robots VARCHAR DEFAULT 'true',
                        error_message TEXT,
                        FOREIGN KEY (project_id) REFERENCES projects(id)
                    )
                """))
                logger.info("✅ Created crawl_jobs table")
            else:
                logger.info("ℹ️ crawl_jobs table already exists")
            
            # Create crawled_pages table
            if 'crawled_pages' not in existing_tables:
                conn.execute(text("""
                    CREATE TABLE crawled_pages (
                        id VARCHAR PRIMARY KEY,
                        crawl_job_id VARCHAR NOT NULL,
                        project_id VARCHAR NOT NULL,
                        url VARCHAR NOT NULL,
                        normalized_url VARCHAR NOT NULL,
                        title VARCHAR,
                        meta_description TEXT,
                        meta_keywords VARCHAR,
                        page_type VARCHAR,
                        confidence_score REAL,
                        status VARCHAR NOT NULL DEFAULT 'pending',
                        crawled_at DATETIME,
                        content_text TEXT,
                        headings TEXT,  -- JSON stored as TEXT
                        images TEXT,    -- JSON stored as TEXT
                        links TEXT,     -- JSON stored as TEXT
                        structured_data TEXT,  -- JSON stored as TEXT
                        open_graph TEXT,       -- JSON stored as TEXT
                        twitter_card TEXT,     -- JSON stored as TEXT
                        content_metrics TEXT,  -- JSON stored as TEXT
                        error_message TEXT,
                        http_status_code INTEGER,
                        extraction_method VARCHAR,
                        extraction_time_ms INTEGER,
                        created_at DATETIME NOT NULL,
                        updated_at DATETIME NOT NULL,
                        FOREIGN KEY (crawl_job_id) REFERENCES crawl_jobs(id),
                        FOREIGN KEY (project_id) REFERENCES projects(id)
                    )
                """))
                
                # Create indices for better performance
                conn.execute(text("CREATE INDEX idx_crawled_pages_url ON crawled_pages(url)"))
                conn.execute(text("CREATE INDEX idx_crawled_pages_normalized_url ON crawled_pages(normalized_url)"))
                conn.execute(text("CREATE INDEX idx_crawled_pages_page_type ON crawled_pages(page_type)"))
                conn.execute(text("CREATE INDEX idx_crawled_pages_project_id ON crawled_pages(project_id)"))
                conn.execute(text("CREATE INDEX idx_crawled_pages_status ON crawled_pages(status)"))
                
                logger.info("✅ Created crawled_pages table with indices")
            else:
                logger.info("ℹ️ crawled_pages table already exists")
            
            # Create page_content_sections table
            if 'page_content_sections' not in existing_tables:
                conn.execute(text("""
                    CREATE TABLE page_content_sections (
                        id VARCHAR PRIMARY KEY,
                        page_id VARCHAR NOT NULL,
                        section_type VARCHAR NOT NULL,
                        section_order INTEGER NOT NULL,
                        parent_section_id VARCHAR,
                        content_text TEXT NOT NULL,
                        content_html TEXT,
                        heading_level INTEGER,
                        word_count INTEGER,
                        character_count INTEGER,
                        attributes TEXT,  -- JSON stored as TEXT
                        created_at DATETIME NOT NULL,
                        FOREIGN KEY (page_id) REFERENCES crawled_pages(id),
                        FOREIGN KEY (parent_section_id) REFERENCES page_content_sections(id)
                    )
                """))
                
                # Create index for better performance
                conn.execute(text("CREATE INDEX idx_page_content_sections_page_id ON page_content_sections(page_id)"))
                conn.execute(text("CREATE INDEX idx_page_content_sections_type ON page_content_sections(section_type)"))
                
                logger.info("✅ Created page_content_sections table with indices")
            else:
                logger.info("ℹ️ page_content_sections table already exists")
            
            conn.commit()
            logger.info("🎉 Migration completed successfully!")
            
    except OperationalError as e:
        logger.error(f"❌ Migration failed: {e}")
        raise
        
    finally:
        engine.dispose()

if __name__ == "__main__":
    run_migration()