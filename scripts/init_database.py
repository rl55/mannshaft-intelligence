#!/usr/bin/env python3
"""
Database Initialization Script
Creates SQLite database with schema
"""

import sys
import sqlite3
from pathlib import Path


def init_database():
    """Initialize SQLite database with schema"""
    
    # Paths
    db_path = Path("data/agent_cache.db")
    schema_path = Path("db/schema.sql")
    
    if not schema_path.exists():
        print(f"❌ Schema file not found: {schema_path}")
        return 1
    
    # Create data directory
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Read schema
    with open(schema_path) as f:
        schema_sql = f.read()
    
    # Create database
    print(f"📊 Creating database: {db_path}")
    
    try:
        conn = sqlite3.connect(str(db_path))
        conn.executescript(schema_sql)
        conn.commit()
        conn.close()
        
        print("✅ Database initialized successfully")
        
        # Verify tables
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        print(f"✅ Created {len(tables)} tables")
        
        return 0
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(init_database())