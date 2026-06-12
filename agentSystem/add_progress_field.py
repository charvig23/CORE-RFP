"""Add current_progress field to RFPs table"""
from sqlalchemy import create_engine, Column, JSON, text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def add_progress_column():
    """Add current_progress JSON column to rfps table"""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Check if column exists
        check_query = text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='rfps' AND column_name='current_progress'
        """)
        result = conn.execute(check_query)
        exists = result.fetchone() is not None
        
        if not exists:
            print("Adding current_progress column to rfps table...")
            alter_query = text("""
                ALTER TABLE rfps 
                ADD COLUMN current_progress JSON NULL
            """)
            conn.execute(alter_query)
            conn.commit()
            print("✓ Successfully added current_progress column")
        else:
            print("✓ current_progress column already exists")

if __name__ == "__main__":
    print("Starting migration...")
    add_progress_column()
    print("Migration complete!")
