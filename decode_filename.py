#!/usr/bin/env python3
"""
فك ترميز اسم الملف
"""

import urllib.parse

filename = "20250719_181630_%D8%A7%D9%82%D8%A7%D9%85%D8%A9_%D9%86%D8%B9%D9%85%D8%A7%D9%86_%D9%82%D8%AF%D9%8A%D9%85%D9%87.jpg"

print("🔍 فك ترميز اسم الملف:")
print(f"الأصلي: {filename}")

try:
    decoded = urllib.parse.unquote(filename, encoding='utf-8')
    print(f"بعد فك الترميز: {decoded}")
except Exception as e:
    print(f"خطأ في فك الترميز: {e}")

# التحقق من وجود الملف
import os

upload_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
print(f"\n📁 مجلد الرفع: {upload_folder}")
print(f"📁 موجود: {os.path.exists(upload_folder)}")

if os.path.exists(upload_folder):
    print("\n📄 الملفات الموجودة:")
    for file in os.listdir(upload_folder):
        if os.path.isfile(os.path.join(upload_folder, file)):
            print(f"   - {file}")
            
    # البحث عن الملف المطلوب
    search_names = [filename, decoded]
    
    print(f"\n🔍 البحث عن الملف:")
    for search_name in search_names:
        file_path = os.path.join(upload_folder, search_name)
        exists = os.path.exists(file_path)
        print(f"   {search_name}: {'✅ موجود' if exists else '❌ غير موجود'}")
