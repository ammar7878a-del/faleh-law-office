#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
سكريبت لإصلاح أسماء الملفات في قاعدة البيانات
"""

import os
import sqlite3
from datetime import datetime

def fix_database_filenames():
    """إصلاح أسماء الملفات في قاعدة البيانات"""
    
    # الاتصال بقاعدة البيانات
    db_path = 'instance/final_working_v2.db'
    if not os.path.exists(db_path):
        print(f"❌ قاعدة البيانات غير موجودة: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # الحصول على جميع المستندات
        cursor.execute("SELECT id, filename, original_filename FROM client_document WHERE filename IS NOT NULL")
        documents = cursor.fetchall()
        
        print(f"🔍 تم العثور على {len(documents)} مستند")
        
        fixed_count = 0
        
        for doc_id, filename, original_filename in documents:
            if filename:
                uploads_dir = 'uploads'
                current_path = os.path.join(uploads_dir, filename)
                fixed_filename = None

                # إذا كان الملف موجود بالاسم الحالي، لا نحتاج لإصلاح
                if os.path.exists(current_path):
                    print(f"✅ الملف موجود: {filename}")
                    continue

                # إذا كان الاسم لا يحتوي على نقطة، نبحث عن الملف بامتدادات مختلفة
                if '.' not in filename:
                    possible_extensions = ['jpg', 'jpeg', 'png', 'pdf', 'doc', 'docx', 'gif']

                    # البحث عن الملف بامتدادات مختلفة
                    for ext in possible_extensions:
                        test_filename = f"{filename}.{ext}"
                        test_path = os.path.join(uploads_dir, test_filename)

                        if os.path.exists(test_path):
                            fixed_filename = test_filename
                            print(f"✅ تم العثور على الملف: {filename} -> {fixed_filename}")
                            break

                    # إذا لم نجد الملف، نحاول استخدام الامتداد من الاسم الأصلي
                    if not fixed_filename and original_filename and '.' in original_filename:
                        original_ext = original_filename.rsplit('.', 1)[1].lower()
                        test_filename = f"{filename}.{original_ext}"
                        test_path = os.path.join(uploads_dir, test_filename)

                        if os.path.exists(test_path):
                            fixed_filename = test_filename
                            print(f"✅ تم إصلاح الملف باستخدام الامتداد الأصلي: {filename} -> {fixed_filename}")

                # البحث المباشر في الملفات الموجودة
                if not fixed_filename:
                    # قائمة الملفات الموجودة فعلياً
                    existing_files = os.listdir(uploads_dir)

                    # البحث عن ملف يحتوي على نفس الاسم
                    for existing_file in existing_files:
                        if os.path.isfile(os.path.join(uploads_dir, existing_file)):
                            # إزالة الامتداد من الملف الموجود للمقارنة
                            existing_base = existing_file.rsplit('.', 1)[0] if '.' in existing_file else existing_file

                            if filename == existing_base or filename in existing_file:
                                fixed_filename = existing_file
                                print(f"✅ تم العثور على الملف بالمطابقة: {filename} -> {fixed_filename}")
                                break

                # تحديث قاعدة البيانات
                if fixed_filename:
                    cursor.execute("UPDATE client_document SET filename = ? WHERE id = ?",
                                 (fixed_filename, doc_id))
                    fixed_count += 1
                else:
                    print(f"⚠️  لم يتم العثور على الملف: {filename}")
        
        # حفظ التغييرات
        conn.commit()
        print(f"\n🎉 تم إصلاح {fixed_count} ملف بنجاح!")
        
        # عرض الملفات المحدثة
        if fixed_count > 0:
            print("\n📋 الملفات المحدثة:")
            cursor.execute("SELECT id, filename, original_filename FROM client_document WHERE filename IS NOT NULL")
            updated_docs = cursor.fetchall()
            
            for doc_id, filename, original_filename in updated_docs:
                print(f"  ID: {doc_id} | {filename} | ({original_filename})")
    
    except Exception as e:
        print(f"❌ خطأ: {e}")
        conn.rollback()
    
    finally:
        conn.close()

def list_upload_files():
    """عرض قائمة بالملفات الموجودة في مجلد uploads"""
    uploads_dir = 'uploads'
    
    if not os.path.exists(uploads_dir):
        print(f"❌ مجلد uploads غير موجود")
        return
    
    print(f"\n📁 الملفات الموجودة في {uploads_dir}:")
    files = os.listdir(uploads_dir)
    
    for file in files:
        file_path = os.path.join(uploads_dir, file)
        if os.path.isfile(file_path):
            size = os.path.getsize(file_path)
            print(f"  📄 {file} ({size} bytes)")

if __name__ == '__main__':
    print("🔧 إصلاح أسماء الملفات في قاعدة البيانات")
    print("=" * 50)
    
    # عرض الملفات الموجودة
    list_upload_files()
    
    # إصلاح قاعدة البيانات
    fix_database_filenames()
    
    print("\n✅ انتهى الإصلاح!")
