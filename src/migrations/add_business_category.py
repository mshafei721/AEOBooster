"""
Migration script to add business_category column to projects table.

Note: This column already exists in the current schema. This script is for
documentation purposes and future database migrations.

To run manually if needed:
python src/migrations/add_business_category.py
"""

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
import os

def run_migration():
    """Add business_category column to projects table if it doesn't exist."""
    
    # Get database URL from environment or use default
    database_url = os.getenv("DATABASE_URL", "sqlite:///./test.db")
    
    # Create engine
    engine = create_engine(database_url)
    
    try:
        with engine.connect() as conn:
            # Check if column already exists (SQLite specific)
            result = conn.execute(text("PRAGMA table_info(projects)"))
            columns = [row[1] for row in result]
            
            if 'business_category' not in columns:
                # Add the column
                conn.execute(text("""
                    ALTER TABLE projects 
                    ADD COLUMN business_category VARCHAR
                """))
                conn.commit()
                print("✅ Successfully added business_category column to projects table")
            else:
                print("ℹ️ business_category column already exists in projects table")
                
    except OperationalError as e:
        print(f"❌ Migration failed: {e}")
        
    finally:
        engine.dispose()

if __name__ == "__main__":
    run_migration()