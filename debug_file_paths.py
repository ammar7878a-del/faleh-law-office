#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
سكريبت لتشخيص مسارات الملفات والعثور على المشكلة
"""

import os
import sqlite3
from datetime import datetime

def debug_file_paths():
    """تشخيص مسارات الملفات"""
    
    print("🔍 تشخيص مسارات الملفات")
    print("=" * 50)
    
    # 1. فحص الملفات الموجودة فعلياً
    uploads_dir = 'uploads'
    print(f"\n📁 الملفات الموجودة في {uploads_dir}:")
    
    actual_files = []
    if os.path.exists(uploads_dir):
        for file in os.listdir(uploads_dir):
            file_path = os.path.join(uploads_dir, file)
            if os.path.isfile(file_path):
                actual_files.append(file)
                size = os.path.getsize(file_path)
                print(f"  ✅ {file} ({size} bytes)")
    
    # 2. فحص قاعدة البيانات
    db_path = 'instance/final_working_v2.db'
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"\n📊 المستندات في قاعدة البيانات:")
        cursor.execute("SELECT id, filename, original_filename FROM client_document WHERE filename IS NOT NULL")
        db_files = cursor.fetchall()
        
        for doc_id, filename, original_filename in db_files:
            file_path = os.path.join(uploads_dir, filename)
            exists = "✅" if os.path.exists(file_path) else "❌"
            print(f"  {exists} ID: {doc_id} | {filename} | ({original_filename})")
            
            # إذا كان الملف غير موجود، ابحث عن بدائل
            if not os.path.exists(file_path):
                print(f"    🔍 البحث عن بدائل للملف: {filename}")
                
                # البحث في الملفات الموجودة
                for actual_file in actual_files:
                    if filename.lower() in actual_file.lower() or actual_file.lower() in filename.lower():
                        print(f"    💡 ملف مشابه موجود: {actual_file}")
                
                # البحث بناءً على الاسم الأصلي
                if original_filename:
                    for actual_file in actual_files:
                        if original_filename.lower() in actual_file.lower():
                            print(f"    💡 ملف بالاسم الأصلي: {actual_file}")
        
        conn.close()
    
    # 3. البحث عن الملف المحدد في الخطأ
    problem_file = "20250718_033530.jpg"
    print(f"\n🎯 البحث عن الملف المشكل: {problem_file}")
    
    problem_path = os.path.join(uploads_dir, problem_file)
    if os.path.exists(problem_path):
        print(f"  ✅ الملف موجود: {problem_path}")
        size = os.path.getsize(problem_path)
        print(f"  📏 الحجم: {size} bytes")
    else:
        print(f"  ❌ الملف غير موجود: {problem_path}")
        
        # البحث عن ملفات مشابهة
        print("  🔍 البحث عن ملفات مشابهة:")
        for file in actual_files:
            if "20250718_033530" in file:
                print(f"    💡 ملف مشابه: {file}")

def check_database_integrity():
    """فحص تكامل قاعدة البيانات"""
    
    print(f"\n🔧 فحص تكامل قاعدة البيانات")
    print("-" * 30)
    
    db_path = 'instance/final_working_v2.db'
    if not os.path.exists(db_path):
        print(f"❌ قاعدة البيانات غير موجودة: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # فحص جدول client_document
        cursor.execute("SELECT COUNT(*) FROM client_document")
        total_docs = cursor.fetchone()[0]
        print(f"📊 إجمالي المستندات: {total_docs}")
        
        # فحص المستندات بدون ملفات
        cursor.execute("SELECT COUNT(*) FROM client_document WHERE filename IS NULL OR filename = ''")
        docs_without_files = cursor.fetchone()[0]
        print(f"📊 مستندات بدون ملفات: {docs_without_files}")
        
        # فحص المستندات مع ملفات غير موجودة
        cursor.execute("SELECT id, filename FROM client_document WHERE filename IS NOT NULL AND filename != ''")
        docs_with_files = cursor.fetchall()
        
        missing_files = 0
        for doc_id, filename in docs_with_files:
            file_path = os.path.join('uploads', filename)
            if not os.path.exists(file_path):
                missing_files += 1
                print(f"❌ ملف مفقود: ID {doc_id} -> {filename}")
        
        print(f"📊 ملفات مفقودة: {missing_files}")
        
    except Exception as e:
        print(f"❌ خطأ في فحص قاعدة البيانات: {e}")
    
    finally:
        conn.close()

if __name__ == '__main__':
    debug_file_paths()
    check_database_integrity()
    
    print(f"\n✅ انتهى التشخيص!")
