#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
إصلاح عدم تطابق أسماء الملفات
"""

import os
import sqlite3

def fix_filename_mismatch():
    """إصلاح عدم تطابق أسماء الملفات"""
    
    print("🔧 إصلاح عدم تطابق أسماء الملفات")
    print("=" * 50)
    
    # الحصول على الملفات الموجودة فعلياً
    uploads_dir = 'uploads'
    actual_files = []
    if os.path.exists(uploads_dir):
        for file in os.listdir(uploads_dir):
            file_path = os.path.join(uploads_dir, file)
            if os.path.isfile(file_path):
                actual_files.append(file)
    
    print(f"📁 الملفات الموجودة فعلياً ({len(actual_files)}):")
    for file in actual_files:
        print(f"  - {file}")
    
    # الاتصال بقاعدة البيانات
    db_path = 'instance/final_working_v2.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # الحصول على المستندات من قاعدة البيانات
        cursor.execute("SELECT id, filename, original_filename FROM client_document WHERE filename IS NOT NULL")
        db_documents = cursor.fetchall()
        
        print(f"\n📊 المستندات في قاعدة البيانات ({len(db_documents)}):")
        
        fixes = []
        for doc_id, db_filename, original_filename in db_documents:
            file_path = os.path.join(uploads_dir, db_filename)
            exists = os.path.exists(file_path)
            
            print(f"  {'✅' if exists else '❌'} ID: {doc_id} | {db_filename}")
            
            if not exists:
                # البحث عن ملف مطابق
                best_match = None
                
                # البحث بناءً على الاسم الأصلي
                if original_filename:
                    original_base = original_filename.rsplit('.', 1)[0] if '.' in original_filename else original_filename
                    for actual_file in actual_files:
                        if original_base.lower() in actual_file.lower():
                            best_match = actual_file
                            break
                
                # البحث بناءً على جزء من اسم الملف
                if not best_match:
                    db_base = db_filename.rsplit('.', 1)[0] if '.' in db_filename else db_filename
                    for actual_file in actual_files:
                        actual_base = actual_file.rsplit('.', 1)[0] if '.' in actual_file else actual_file
                        if db_base.lower() in actual_file.lower() or actual_base.lower() in db_filename.lower():
                            best_match = actual_file
                            break
                
                # البحث بناءً على التاريخ والوقت
                if not best_match:
                    # استخراج التاريخ من اسم الملف في قاعدة البيانات
                    import re
                    date_pattern = r'(\d{8}_\d{6})'
                    db_date_match = re.search(date_pattern, db_filename)
                    
                    if db_date_match:
                        db_date = db_date_match.group(1)
                        for actual_file in actual_files:
                            if db_date in actual_file:
                                best_match = actual_file
                                break
                
                if best_match:
                    fixes.append((doc_id, db_filename, best_match))
                    print(f"    💡 اقتراح إصلاح: {db_filename} -> {best_match}")
                else:
                    print(f"    ⚠️  لم يتم العثور على ملف مطابق")
        
        # تطبيق الإصلاحات
        if fixes:
            print(f"\n🔧 تطبيق الإصلاحات ({len(fixes)}):")
            for doc_id, old_filename, new_filename in fixes:
                cursor.execute("UPDATE client_document SET filename = ? WHERE id = ?", 
                             (new_filename, doc_id))
                print(f"  ✅ تم تحديث ID {doc_id}: {old_filename} -> {new_filename}")
            
            conn.commit()
            print(f"\n🎉 تم تطبيق {len(fixes)} إصلاح بنجاح!")
        else:
            print(f"\n✅ لا توجد إصلاحات مطلوبة")
        
        # التحقق النهائي
        print(f"\n🔍 التحقق النهائي:")
        cursor.execute("SELECT id, filename FROM client_document WHERE filename IS NOT NULL")
        final_check = cursor.fetchall()
        
        missing_count = 0
        for doc_id, filename in final_check:
            file_path = os.path.join(uploads_dir, filename)
            if not os.path.exists(file_path):
                missing_count += 1
                print(f"  ❌ لا يزال مفقود: ID {doc_id} -> {filename}")
        
        if missing_count == 0:
            print(f"  🎉 جميع الملفات موجودة الآن!")
        else:
            print(f"  ⚠️  {missing_count} ملف لا يزال مفقود")
    
    except Exception as e:
        print(f"❌ خطأ: {e}")
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == '__main__':
    fix_filename_mismatch()
    print(f"\n✅ انتهى الإصلاح!")
