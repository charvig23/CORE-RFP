"""
Database migration script to update existing tables with new columns
"""
from sqlalchemy import text
from database import engine, Base
from models import Tool, Agent, RFP, Conversation, AgentExecution

def migrate_database():
    print("=" * 60)
    print("Running Database Migration")
    print("=" * 60)
    
    with engine.connect() as conn:
        print("\nStep 1: Checking and adding missing columns...")
        
        # Add tool_type column to tools table if not exists
        try:
            conn.execute(text("""
                ALTER TABLE tools 
                ADD COLUMN IF NOT EXISTS tool_type VARCHAR DEFAULT 'function'
            """))
            conn.commit()
            print("✓ Added tool_type column to tools table")
        except Exception as e:
            print(f"  Note: {e}")
        
        # Add parameters column to tools table if not exists
        try:
            conn.execute(text("""
                ALTER TABLE tools 
                ADD COLUMN IF NOT EXISTS parameters JSON
            """))
            conn.commit()
            print("✓ Added parameters column to tools table")
        except Exception as e:
            print(f"  Note: {e}")
        
        # Add created_at column to tools table if not exists
        try:
            conn.execute(text("""
                ALTER TABLE tools 
                ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW()
            """))
            conn.commit()
            print("✓ Added created_at column to tools table")
        except Exception as e:
            print(f"  Note: {e}")
        
        # Add role column to agents table if not exists
        try:
            conn.execute(text("""
                ALTER TABLE agents 
                ADD COLUMN IF NOT EXISTS role VARCHAR
            """))
            conn.commit()
            print("✓ Added role column to agents table")
        except Exception as e:
            print(f"  Note: {e}")
        
        # Add system_prompt column to agents table if not exists
        try:
            conn.execute(text("""
                ALTER TABLE agents 
                ADD COLUMN IF NOT EXISTS system_prompt TEXT
            """))
            conn.commit()
            print("✓ Added system_prompt column to agents table")
        except Exception as e:
            print(f"  Note: {e}")
        
        # Rename tools column to tool_ids in agents table
        try:
            # Check if tools column exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='agents' AND column_name='tools'
            """))
            if result.fetchone():
                conn.execute(text("""
                    ALTER TABLE agents 
                    RENAME COLUMN tools TO tool_ids
                """))
                conn.commit()
                print("✓ Renamed tools column to tool_ids in agents table")
        except Exception as e:
            print(f"  Note: {e}")
        
        # Add tool_ids column if it doesn't exist
        try:
            conn.execute(text("""
                ALTER TABLE agents 
                ADD COLUMN IF NOT EXISTS tool_ids JSON
            """))
            conn.commit()
            print("✓ Added tool_ids column to agents table")
        except Exception as e:
            print(f"  Note: {e}")
        
        # Add created_at column to agents table if not exists
        try:
            conn.execute(text("""
                ALTER TABLE agents 
                ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW()
            """))
            conn.commit()
            print("✓ Added created_at column to agents table")
        except Exception as e:
            print(f"  Note: {e}")
        
        # Add new columns to rfps table
        try:
            conn.execute(text("""
                ALTER TABLE rfps 
                ADD COLUMN IF NOT EXISTS title VARCHAR,
                ADD COLUMN IF NOT EXISTS file_path VARCHAR,
                ADD COLUMN IF NOT EXISTS status VARCHAR DEFAULT 'uploaded',
                ADD COLUMN IF NOT EXISTS sales_summary JSON,
                ADD COLUMN IF NOT EXISTS technical_matches JSON,
                ADD COLUMN IF NOT EXISTS pricing_data JSON,
                ADD COLUMN IF NOT EXISTS final_proposal TEXT,
                ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW()
            """))
            conn.commit()
            print("✓ Added missing columns to rfps table")
        except Exception as e:
            print(f"  Note: {e}")
        
        # Add new columns to conversations table
        try:
            conn.execute(text("""
                ALTER TABLE conversations 
                ADD COLUMN IF NOT EXISTS agent_id INTEGER REFERENCES agents(id),
                ADD COLUMN IF NOT EXISTS rfp_id INTEGER REFERENCES rfps(id),
                ADD COLUMN IF NOT EXISTS tool_calls JSON,
                ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW()
            """))
            conn.commit()
            print("✓ Added missing columns to conversations table")
        except Exception as e:
            print(f"  Note: {e}")
        
        # Drop old agent_name column from conversations if exists
        try:
            conn.execute(text("""
                ALTER TABLE conversations 
                DROP COLUMN IF EXISTS agent_name
            """))
            conn.commit()
            print("✓ Removed agent_name column from conversations table")
        except Exception as e:
            print(f"  Note: {e}")
    
    print("\nStep 2: Creating missing tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ All tables created/verified")
    
    print("\n" + "=" * 60)
    print("Migration Complete!")
    print("=" * 60)
    print("\nYou can now run: python setup_agents.py")

if __name__ == "__main__":
    try:
        migrate_database()
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
