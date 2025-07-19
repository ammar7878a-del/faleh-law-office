#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
إصلاح امتداد الملف
"""

import os
import sqlite3

def fix_filename_extension():
    """إصلاح امتداد الملف"""
    
    print("🔧 إصلاح امتداد الملف")
    print("=" * 40)
    
    # الاتصال بقاعدة البيانات
    db_path = 'instance/final_working_v2.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # تحديث اسم الملف في قاعدة البيانات
        old_filename = '20250718_074702_docx'
        new_filename = '20250718_074702.docx'
        
        cursor.execute("UPDATE client_document SET filename = ? WHERE filename = ?", 
                     (new_filename, old_filename))
        
        if cursor.rowcount > 0:
            conn.commit()
            print(f"✅ تم تحديث اسم الملف:")
            print(f"   من: {old_filename}")
            print(f"   إلى: {new_filename}")
        else:
            print("❌ لم يتم العثور على الملف في قاعدة البيانات")
        
        # التحقق من النتيجة
        cursor.execute("SELECT id, filename, original_filename FROM client_document WHERE id = 8")
        result = cursor.fetchone()
        
        if result:
            doc_id, filename, original_filename = result
            print(f"\n📄 المستند بعد التحديث:")
            print(f"   - ID: {doc_id}")
            print(f"   - اسم الملف: {filename}")
            print(f"   - الاسم الأصلي: {original_filename}")
            
            # التحقق من وجود الملف
            file_path = os.path.join('uploads', filename)
            if os.path.exists(file_path):
                print(f"   - الملف موجود: ✅")
                print(f"   - الحجم: {os.path.getsize(file_path)} bytes")
            else:
                print(f"   - الملف موجود: ❌")
    
    except Exception as e:
        print(f"❌ خطأ: {e}")
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == '__main__':
    fix_filename_extension()
    print(f"\n✅ انتهى الإصلاح!")
