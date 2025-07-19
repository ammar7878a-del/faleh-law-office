#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
إصلاح اسم الملف الأخير
"""

import os
import sqlite3

def fix_latest_file():
    """إصلاح اسم الملف الأخير"""
    
    print("🔧 إصلاح اسم الملف الأخير")
    print("=" * 40)
    
    # الاتصال بقاعدة البيانات
    db_path = 'instance/final_working_v2.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # الحصول على آخر مستند
        cursor.execute("SELECT id, filename, original_filename FROM client_document ORDER BY id DESC LIMIT 1")
        result = cursor.fetchone()
        
        if result:
            doc_id, db_filename, original_filename = result
            print(f"📄 آخر مستند: ID {doc_id}")
            print(f"   - اسم الملف في قاعدة البيانات: {db_filename}")
            print(f"   - الاسم الأصلي: {original_filename}")
            
            # التحقق من الملفات الموجودة
            uploads_dir = 'uploads'
            actual_files = []
            if os.path.exists(uploads_dir):
                for file in os.listdir(uploads_dir):
                    if file.startswith('20250718_074702'):
                        actual_files.append(file)
            
            print(f"📁 الملفات الموجودة المطابقة:")
            for file in actual_files:
                print(f"   - {file}")
            
            # إصلاح اسم الملف
            if actual_files:
                correct_filename = actual_files[0]  # أخذ أول ملف مطابق
                
                if db_filename != correct_filename:
                    print(f"🔧 تحديث اسم الملف:")
                    print(f"   من: {db_filename}")
                    print(f"   إلى: {correct_filename}")
                    
                    cursor.execute("UPDATE client_document SET filename = ? WHERE id = ?", 
                                 (correct_filename, doc_id))
                    conn.commit()
                    print("✅ تم التحديث بنجاح!")
                else:
                    print("✅ اسم الملف صحيح بالفعل")
            else:
                print("❌ لم يتم العثور على ملفات مطابقة")
        else:
            print("❌ لا توجد مستندات في قاعدة البيانات")
    
    except Exception as e:
        print(f"❌ خطأ: {e}")
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == '__main__':
    fix_latest_file()
    print(f"\n✅ انتهى الإصلاح!")
