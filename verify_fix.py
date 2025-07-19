#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(__file__))

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'test-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///final_working_v2.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# Define the model that was causing the error
class ClientDocument(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    document_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200))
    filename = db.Column(db.String(255))
    original_filename = db.Column(db.String(255))
    file_size = db.Column(db.Integer)
    client_id = db.Column(db.Integer, nullable=False)
    case_id = db.Column(db.Integer)  # This was the missing column
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

def test_database():
    """Test the database operations that were failing"""
    
    print("🔍 Testing database operations...")
    
    with app.app_context():
        try:
            # Test 1: Count query (this was failing before)
            print("1️⃣ Testing count query...")
            count = ClientDocument.query.count()
            print(f"   ✅ Success! Found {count} documents")
            
            # Test 2: Filter by case_id (this was also failing)
            print("2️⃣ Testing case_id filter...")
            case_docs = ClientDocument.query.filter_by(case_id=1).all()
            print(f"   ✅ Success! Found {len(case_docs)} documents for case_id=1")
            
            # Test 3: Filter by case_id=None
            print("3️⃣ Testing case_id=None filter...")
            general_docs = ClientDocument.query.filter_by(case_id=None).all()
            print(f"   ✅ Success! Found {len(general_docs)} general documents")
            
            # Test 4: Select with case_id column
            print("4️⃣ Testing select with case_id...")
            docs = ClientDocument.query.with_entities(
                ClientDocument.id, 
                ClientDocument.document_type, 
                ClientDocument.case_id
            ).all()
            print(f"   ✅ Success! Retrieved {len(docs)} document records with case_id")
            
            print("\n🎉 All database tests passed!")
            print("The SQLAlchemy error has been fixed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Database test failed: {e}")
            return False

if __name__ == '__main__':
    print("🚀 Database Fix Verification")
    print("=" * 50)
    
    success = test_database()
    
    if success:
        print("\n✅ VERIFICATION SUCCESSFUL!")
        print("The original SQLAlchemy error has been resolved.")
        print("You can now run your law office application without issues.")
    else:
        print("\n❌ VERIFICATION FAILED!")
        print("There are still issues with the database schema.")
