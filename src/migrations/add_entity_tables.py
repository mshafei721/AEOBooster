"""
Database migration to add entity extraction tables.
"""
from sqlalchemy import text
from src.models.database import engine, Base
from src.models.entity import Entity, EntityRelation
import logging

logger = logging.getLogger(__name__)

def upgrade():
    """Add entity extraction tables to the database."""
    try:
        # Create the tables
        Base.metadata.create_all(bind=engine, tables=[Entity.__table__, EntityRelation.__table__])
        logger.info("Entity tables created successfully")
        
        # Add indexes for performance
        with engine.connect() as connection:
            # Create composite indexes for better query performance
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_entity_type_confidence ON entities(entity_type, confidence_score DESC);",
                "CREATE INDEX IF NOT EXISTS idx_entity_project_type ON entities(project_id, entity_type);", 
                "CREATE INDEX IF NOT EXISTS idx_entity_value_normalized ON entities(normalized_value, entity_type);",
                "CREATE INDEX IF NOT EXISTS idx_entity_page_id ON entities(page_id);",
                "CREATE INDEX IF NOT EXISTS idx_entity_relations_entity ON entity_relations(entity_id);",
                "CREATE INDEX IF NOT EXISTS idx_entity_relations_related ON entity_relations(related_entity_id);",
            ]
            
            for index_sql in indexes:
                try:
                    connection.execute(text(index_sql))
                    connection.commit()
                except Exception as e:
                    logger.warning(f"Index creation failed (may already exist): {e}")
                    
        logger.info("Entity table indexes created successfully")
        
    except Exception as e:
        logger.error(f"Failed to create entity tables: {e}")
        raise

def downgrade():
    """Remove entity extraction tables from the database."""
    try:
        # Drop the tables
        EntityRelation.__table__.drop(bind=engine, checkfirst=True)
        Entity.__table__.drop(bind=engine, checkfirst=True)
        logger.info("Entity tables dropped successfully")
        
    except Exception as e:
        logger.error(f"Failed to drop entity tables: {e}")
        raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    upgrade()