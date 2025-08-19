# backend/create_db.py
from app.database import engine, Base, test_connection
from app.models import *  # Import all models
import sys

def recreate_tables():
    """Drop and recreate all database tables with updated schema"""
    try:
        print("🔍 Testing database connection...")
        if not test_connection():
            print("❌ Failed to connect to database")
            sys.exit(1)
        
        print("⚠️  WARNING: This will delete all existing data!")
        print("🗑️  Dropping all existing tables...")
        Base.metadata.drop_all(bind=engine)
        
        print("🏗️  Creating all tables with updated schema...")
        Base.metadata.create_all(bind=engine)
        print("✅ Database schema updated successfully!")
        
        # Print created tables
        print("\n📋 Updated tables:")
        for table in Base.metadata.tables.keys():
            print(f"  - {table}")
            
    except Exception as e:
        print(f"❌ Error updating database schema: {e}")
        sys.exit(1)

if __name__ == "__main__":
    recreate_tables()
