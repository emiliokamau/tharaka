"""
Database Migration Script
Fixes missing columns in the health_record table
"""

import sqlite3
import os

def migrate_database():
    """Add missing columns to health_record table"""
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'drivers.db')
    
    if not os.path.exists(db_path):
        print("Database not found. It will be created with the correct schema.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check existing columns
    cursor.execute("PRAGMA table_info(health_record)")
    columns = [col[1] for col in cursor.fetchall()]
    print(f"Current columns: {columns}")
    
    # Add missing columns
    migrations = []
    
    if 'tiredness_level' not in columns:
        migrations.append("ALTER TABLE health_record ADD COLUMN tiredness_level INTEGER")
        print("Adding tiredness_level column...")
    
    if 'sleep_hours' not in columns:
        migrations.append("ALTER TABLE health_record ADD COLUMN sleep_hours FLOAT")
        print("Adding sleep_hours column...")
    
    # Execute migrations
    for migration in migrations:
        try:
            cursor.execute(migration)
            print(f"Executed: {migration}")
        except Exception as e:
            print(f"Error: {e}")
    
    conn.commit()
    
    # Verify columns again
    cursor.execute("PRAGMA table_info(health_record)")
    columns = [col[1] for col in cursor.fetchall()]
    print(f"Updated columns: {columns}")
    
    conn.close()
    print("✅ Database migration complete!")

if __name__ == '__main__':
    migrate_database()
