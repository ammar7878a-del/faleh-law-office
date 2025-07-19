#!/usr/bin/env python3
"""
اختبار إنشاء الروابط
"""

import sys
import os

# إضافة مجلد المشروع إلى المسار
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from final_working import app, ClientDocument, db
from flask import url_for

def test_url_generation():
    """اختبار إنشاء روابط الملفات"""
    
    with app.app_context():
        print("🔍 اختبار إنشاء روابط الملفات")
        print("=" * 50)
        
        # البحث عن المستند في قاعدة البيانات
        document = ClientDocument.query.filter_by(id=2).first()
        
        if not document:
            print("❌ لم يتم العثور على المستند")
            return
        
        print(f"📄 المستند الموجود:")
        print(f"   ID: {document.id}")
        print(f"   اسم الملف: {document.filename}")
        print(f"   الاسم الأصلي: {document.original_filename}")
        print(f"   العميل: {document.client_id}")
        
        # إنشاء الرابط باستخدام url_for
        try:
            url = url_for('simple_file', filename=document.filename)
            print(f"\n🔗 الرابط المُنشأ:")
            print(f"   {url}")
            
            # فك ترميز الرابط
            import urllib.parse
            decoded_url = urllib.parse.unquote(url, encoding='utf-8')
            print(f"   بعد فك الترميز: {decoded_url}")
            
        except Exception as e:
            print(f"❌ خطأ في إنشاء الرابط: {e}")
        
        # التحقق من وجود الملف
        upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
        file_path = os.path.join(upload_folder, document.filename)
        exists = os.path.exists(file_path)
        
        print(f"\n📁 التحقق من وجود الملف:")
        print(f"   المسار: {file_path}")
        print(f"   موجود: {'✅ نعم' if exists else '❌ لا'}")

if __name__ == '__main__':
    test_url_generation()
