#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Migration Script for Law Office Management System
This script adds missing columns to existing database tables
"""

import sqlite3
import os
from datetime import datetime

def migrate_database():
    """Migrate the database to add missing columns"""

    # Database file path - use absolute path
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'final_working_v2.db')
    
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return False
    
    print(f"🔄 Starting database migration for: {db_path}")
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check current schema of client_document table
        cursor.execute("PRAGMA table_info(client_document)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        print(f"📋 Current columns in client_document table: {column_names}")
        
        # Check if case_id column exists
        if 'case_id' not in column_names:
            print("➕ Adding case_id column to client_document table...")
            cursor.execute("ALTER TABLE client_document ADD COLUMN case_id INTEGER")
            print("✅ case_id column added successfully")
        else:
            print("✅ case_id column already exists")
        
        # Commit changes
        conn.commit()
        
        # Verify the migration
        cursor.execute("PRAGMA table_info(client_document)")
        columns_after = cursor.fetchall()
        column_names_after = [col[1] for col in columns_after]
        
        print(f"📋 Columns after migration: {column_names_after}")
        
        # Test a simple query to ensure everything works
        cursor.execute("SELECT COUNT(*) FROM client_document")
        count = cursor.fetchone()[0]
        print(f"📊 Total documents in database: {count}")
        
        # Close connection
        conn.close()
        
        print("✅ Database migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

def check_database_schema():
    """Check the current database schema"""

    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'final_working_v2.db')
    
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print("📊 Database Schema Information:")
        print("=" * 50)
        
        for table in tables:
            table_name = table[0]
            print(f"\n🗂️  Table: {table_name}")
            
            # Get table info
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            for col in columns:
                col_id, col_name, col_type, not_null, default_val, primary_key = col
                pk_marker = " (PRIMARY KEY)" if primary_key else ""
                null_marker = " NOT NULL" if not_null else ""
                default_marker = f" DEFAULT {default_val}" if default_val else ""
                print(f"   📝 {col_name}: {col_type}{null_marker}{default_marker}{pk_marker}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking schema: {e}")

if __name__ == '__main__':
    print("🚀 Law Office Database Migration Tool")
    print("=" * 50)
    
    # Check current schema
    print("\n1️⃣ Checking current database schema...")
    check_database_schema()
    
    # Run migration
    print("\n2️⃣ Running database migration...")
    success = migrate_database()
    
    if success:
        print("\n3️⃣ Verifying migration...")
        check_database_schema()
        print("\n🎉 Migration completed successfully!")
        print("You can now run the application without errors.")
    else:
        print("\n❌ Migration failed. Please check the errors above.")
