"""
Migration script to add proposal_draft and approval_status columns to RFP table
Run this before restarting the server
"""

from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/agent_system")
engine = create_engine(DATABASE_URL)

def migrate():
    """Add new columns for HITL approval workflow"""
    with engine.connect() as conn:
        try:
            # Add proposal_draft column
            conn.execute(text("""
                ALTER TABLE rfps 
                ADD COLUMN IF NOT EXISTS proposal_draft JSON
            """))
            print("✓ Added proposal_draft column")
            
            # Add approval_status column
            conn.execute(text("""
                ALTER TABLE rfps 
                ADD COLUMN IF NOT EXISTS approval_status VARCHAR DEFAULT 'pending'
            """))
            print("✓ Added approval_status column")
            
            # Update status column comment
            conn.execute(text("""
                COMMENT ON COLUMN rfps.status IS 'uploaded, analyzed, processed, awaiting_approval, approved'
            """))
            print("✓ Updated status column")
            
            conn.commit()
            print("\n✅ Migration completed successfully!")
            print("\nNew workflow:")
            print("1. POST /rfp/{rfp_id}/analyze - Generates draft proposal")
            print("2. GET /rfp/{rfp_id}/proposal-draft - View editable draft")
            print("3. POST /rfp/{rfp_id}/approve-proposal - Approve and generate PDF")
            
        except Exception as e:
            conn.rollback()
            print(f"❌ Migration failed: {e}")
            raise

if __name__ == "__main__":
    migrate()
