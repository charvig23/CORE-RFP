"""
Migration script to convert integer IDs to UUIDs for agents and tools
WARNING: This will drop existing data!
"""
from sqlalchemy import text
from database import engine, Base
from models import Tool, Agent, RFP, Conversation, AgentExecution

def migrate_to_uuid():
    print("=" * 60)
    print("Migrating to UUID IDs")
    print("WARNING: This will delete all existing agents and tools!")
    print("=" * 60)
    
    print("\nProceeding with migration...")
    
    with engine.connect() as conn:
        print("\nStep 1: Dropping dependent tables...")
        
        try:
            conn.execute(text("DROP TABLE IF EXISTS agent_executions CASCADE"))
            print("✓ Dropped agent_executions table")
        except Exception as e:
            print(f"  Note: {e}")
        
        try:
            conn.execute(text("DROP TABLE IF EXISTS conversations CASCADE"))
            print("✓ Dropped conversations table")
        except Exception as e:
            print(f"  Note: {e}")
        
        try:
            conn.execute(text("DROP TABLE IF EXISTS rfps CASCADE"))
            print("✓ Dropped rfps table")
        except Exception as e:
            print(f"  Note: {e}")
        
        print("\nStep 2: Dropping agents and tools tables...")
        
        try:
            conn.execute(text("DROP TABLE IF EXISTS agents CASCADE"))
            print("✓ Dropped agents table")
        except Exception as e:
            print(f"  Note: {e}")
        
        try:
            conn.execute(text("DROP TABLE IF EXISTS tools CASCADE"))
            print("✓ Dropped tools table")
        except Exception as e:
            print(f"  Note: {e}")
        
        conn.commit()
    
    print("\nStep 3: Creating all tables with UUID...")
    Base.metadata.create_all(bind=engine)
    print("✓ All tables created with UUID")
    
    print("\n" + "=" * 60)
    print("Migration Complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Create tools via POST /tools/create")
    print("2. Create agents via POST /agents/create")
    print("3. Assign tools to agents via POST /agents/{agent_id}/add-tools")
    print("\nIDs will now be UUIDs like: 550e8400-e29b-41d4-a716-446655440000")

if __name__ == "__main__":
    try:
        migrate_to_uuid()
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
