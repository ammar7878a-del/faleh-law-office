#!/usr/bin/env python3
"""
فحص قاعدة البيانات للملفات
"""

import sqlite3
import os

# الاتصال بقاعدة البيانات
db_path = 'instance/final_working_v2.db'
if not os.path.exists(db_path):
    print(f"❌ قاعدة البيانات غير موجودة: {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("🔍 البحث في قاعدة البيانات عن الملفات:")
print("=" * 50)

# البحث عن جميع المستندات
cursor.execute("""
    SELECT id, filename, original_filename, client_id, created_at 
    FROM client_document 
    WHERE filename IS NOT NULL 
    ORDER BY created_at DESC 
    LIMIT 10
""")

documents = cursor.fetchall()

if documents:
    print("📄 آخر 10 مستندات:")
    for doc in documents:
        doc_id, filename, original_filename, client_id, created_at = doc
        print(f"   ID: {doc_id}")
        print(f"   اسم الملف: {filename}")
        print(f"   الاسم الأصلي: {original_filename}")
        print(f"   العميل: {client_id}")
        print(f"   التاريخ: {created_at}")
        
        # التحقق من وجود الملف
        upload_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
        file_path = os.path.join(upload_folder, filename)
        exists = os.path.exists(file_path)
        print(f"   الملف موجود: {'✅ نعم' if exists else '❌ لا'}")
        print("-" * 30)
else:
    print("❌ لا توجد مستندات في قاعدة البيانات")

# البحث عن الملف المحدد
search_filename = "اقامة_نعمان_قديمه"
print(f"\n🔍 البحث عن الملفات التي تحتوي على: {search_filename}")

cursor.execute("""
    SELECT id, filename, original_filename, client_id 
    FROM client_document 
    WHERE filename LIKE ? OR original_filename LIKE ?
""", (f'%{search_filename}%', f'%{search_filename}%'))

matching_docs = cursor.fetchall()

if matching_docs:
    print("📄 الملفات المطابقة:")
    for doc in matching_docs:
        doc_id, filename, original_filename, client_id = doc
        print(f"   ID: {doc_id}, ملف: {filename}, أصلي: {original_filename}, عميل: {client_id}")
else:
    print("❌ لا توجد ملفات مطابقة")

conn.close()
