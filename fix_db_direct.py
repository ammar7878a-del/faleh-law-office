#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
إصلاح مباشر لقاعدة البيانات
"""

import sqlite3
import os

def fix_database():
    """إصلاح مباشر لأسماء الملفات"""
    
    db_path = 'instance/final_working_v2.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # إصلاح الملفات المحددة
        fixes = [
            ('20250718_033507_docx', '20250718_033507.docx'),
            ('20250718_033530_jpg', '20250718_033530.jpg')
        ]
        
        for old_name, new_name in fixes:
            # التحقق من وجود الملف الجديد
            new_path = os.path.join('uploads', new_name)
            if os.path.exists(new_path):
                # تحديث قاعدة البيانات
                cursor.execute("UPDATE client_document SET filename = ? WHERE filename = ?", 
                             (new_name, old_name))
                print(f"✅ تم تحديث: {old_name} -> {new_name}")
            else:
                print(f"❌ الملف غير موجود: {new_name}")
        
        # حفظ التغييرات
        conn.commit()
        
        # عرض النتائج
        cursor.execute("SELECT id, filename, original_filename FROM client_document")
        docs = cursor.fetchall()
        
        print(f"\n📋 جميع المستندات في قاعدة البيانات:")
        for doc_id, filename, original_filename in docs:
            file_exists = "✅" if os.path.exists(os.path.join('uploads', filename)) else "❌"
            print(f"  {file_exists} ID: {doc_id} | {filename} | ({original_filename})")
        
    except Exception as e:
        print(f"❌ خطأ: {e}")
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == '__main__':
    print("🔧 إصلاح مباشر لقاعدة البيانات")
    print("=" * 40)
    fix_database()
    print("\n✅ انتهى الإصلاح!")
