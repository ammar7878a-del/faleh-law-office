#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Migration Script for User Roles
This script adds role and created_at columns to the user table
"""

import sqlite3
import os
from datetime import datetime

def migrate_user_roles():
    """Migrate the database to add user roles"""
    
    # Database file path
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'final_working_v2.db')
    
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return False
    
    print(f"🔄 Starting user roles migration for: {db_path}")
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check current schema of user table
        cursor.execute("PRAGMA table_info(user)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        print(f"📋 Current columns in user table: {column_names}")
        
        # Check if role column exists
        if 'role' not in column_names:
            print("➕ Adding role column to user table...")
            cursor.execute("ALTER TABLE user ADD COLUMN role TEXT DEFAULT 'lawyer'")
            print("✅ role column added successfully")
        else:
            print("✅ role column already exists")
        
        # Check if created_at column exists
        if 'created_at' not in column_names:
            print("➕ Adding created_at column to user table...")
            cursor.execute("ALTER TABLE user ADD COLUMN created_at DATETIME")
            print("✅ created_at column added successfully")
        else:
            print("✅ created_at column already exists")
        
        # Update existing users
        print("🔄 Updating existing users...")
        
        # Set admin role for the first user (usually admin)
        cursor.execute("SELECT id, username FROM user ORDER BY id LIMIT 1")
        first_user = cursor.fetchone()
        if first_user:
            cursor.execute("UPDATE user SET role = 'admin' WHERE id = ?", (first_user[0],))
            print(f"✅ Set user '{first_user[1]}' as admin")
        
        # Set created_at for users without it
        cursor.execute("UPDATE user SET created_at = ? WHERE created_at IS NULL", (datetime.now(),))
        
        # Commit changes
        conn.commit()
        
        # Verify the migration
        cursor.execute("PRAGMA table_info(user)")
        columns_after = cursor.fetchall()
        column_names_after = [col[1] for col in columns_after]
        
        print(f"📋 Columns after migration: {column_names_after}")
        
        # Test a simple query to ensure everything works
        cursor.execute("SELECT COUNT(*) FROM user")
        count = cursor.fetchone()[0]
        print(f"📊 Total users in database: {count}")
        
        # Show user roles
        cursor.execute("SELECT username, role FROM user")
        users = cursor.fetchall()
        print("👥 User roles:")
        for username, role in users:
            role_name = {
                'admin': 'مدير النظام',
                'lawyer': 'محامي',
                'secretary': 'سكرتير'
            }.get(role, role)
            print(f"   - {username}: {role_name}")
        
        # Close connection
        conn.close()
        
        print("✅ User roles migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

def check_user_schema():
    """Check the current user table schema"""
    
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'final_working_v2.db')
    
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("📊 User Table Schema:")
        print("=" * 50)
        
        # Get table info
        cursor.execute("PRAGMA table_info(user)")
        columns = cursor.fetchall()
        
        for col in columns:
            col_id, col_name, col_type, not_null, default_val, primary_key = col
            pk_marker = " (PRIMARY KEY)" if primary_key else ""
            null_marker = " NOT NULL" if not_null else ""
            default_marker = f" DEFAULT {default_val}" if default_val else ""
            print(f"   📝 {col_name}: {col_type}{null_marker}{default_marker}{pk_marker}")
        
        # Show current users
        print("\n👥 Current Users:")
        print("=" * 50)
        cursor.execute("SELECT id, username, first_name, last_name, role FROM user")
        users = cursor.fetchall()
        
        for user in users:
            user_id, username, first_name, last_name, role = user
            role_name = {
                'admin': 'مدير النظام',
                'lawyer': 'محامي',
                'secretary': 'سكرتير'
            }.get(role, role or 'غير محدد')
            print(f"   {user_id}. {username} ({first_name} {last_name}) - {role_name}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking schema: {e}")

if __name__ == '__main__':
    print("🚀 User Roles Migration Tool")
    print("=" * 50)
    
    # Check current schema
    print("\n1️⃣ Checking current user table schema...")
    check_user_schema()
    
    # Run migration
    print("\n2️⃣ Running user roles migration...")
    success = migrate_user_roles()
    
    if success:
        print("\n3️⃣ Verifying migration...")
        check_user_schema()
        print("\n🎉 Migration completed successfully!")
        print("Users now have roles and the system supports permissions!")
    else:
        print("\n❌ Migration failed. Please check the errors above.")
