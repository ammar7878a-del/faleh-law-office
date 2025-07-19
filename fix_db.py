import sqlite3
import os

# Database path
db_path = os.path.join('faleh', 'instance', 'final_working_v2.db')

print(f"Database path: {db_path}")
print(f"Database exists: {os.path.exists(db_path)}")

if os.path.exists(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check current columns
        cursor.execute("PRAGMA table_info(client_document)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        print(f"Current columns: {column_names}")
        
        if 'case_id' not in column_names:
            print("Adding case_id column...")
            cursor.execute("ALTER TABLE client_document ADD COLUMN case_id INTEGER")
            conn.commit()
            print("Column added successfully!")
        else:
            print("case_id column already exists")
        
        # Test query
        cursor.execute("SELECT COUNT(*) FROM client_document")
        count = cursor.fetchone()[0]
        print(f"Total documents: {count}")
        
        conn.close()
        print("Migration completed!")
        
    except Exception as e:
        print(f"Error: {e}")
else:
    print("Database file not found!")
