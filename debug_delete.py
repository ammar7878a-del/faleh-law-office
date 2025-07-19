#!/usr/bin/env python3
"""
اختبار مباشر لوظيفة حذف المستخدمين
"""

import requests
import sys

def test_delete_route():
    """اختبار route الحذف مباشرة"""
    print("🔍 اختبار route حذف المستخدمين...")
    
    base_url = "http://localhost:5000"
    
    try:
        # اختبار الوصول للصفحة الرئيسية
        response = requests.get(base_url, timeout=5)
        if response.status_code == 200:
            print("✅ التطبيق يعمل على localhost:5000")
        else:
            print(f"❌ مشكلة في الوصول للتطبيق: {response.status_code}")
            return
        
        # اختبار الوصول لصفحة تسجيل الدخول
        login_response = requests.get(f"{base_url}/auth/login", timeout=5)
        if login_response.status_code == 200:
            print("✅ صفحة تسجيل الدخول تعمل")
        else:
            print(f"❌ مشكلة في صفحة تسجيل الدخول: {login_response.status_code}")
        
        # اختبار route الحذف (بدون تسجيل دخول - يجب أن يعيد توجيه)
        delete_response = requests.post(f"{base_url}/auth/delete_user/1", timeout=5, allow_redirects=False)
        if delete_response.status_code in [302, 401, 403]:
            print("✅ route الحذف موجود ويتطلب تسجيل دخول")
        else:
            print(f"❌ مشكلة في route الحذف: {delete_response.status_code}")
        
    except requests.exceptions.ConnectionError:
        print("❌ لا يمكن الاتصال بالتطبيق. تأكد من تشغيل التطبيق على localhost:5000")
        return
    except Exception as e:
        print(f"❌ خطأ: {e}")
        return
    
    print("\n📋 التحقق من الملفات:")
    
    # التحقق من وجود الملفات
    import os
    files_to_check = [
        "app/auth/routes.py",
        "app/templates/auth/users.html",
        "app/__init__.py"
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"✅ {file_path} موجود")
        else:
            print(f"❌ {file_path} غير موجود")
    
    print("\n🔧 للتحقق من المشكلة:")
    print("1. تأكد من تسجيل الدخول كمدير")
    print("2. انتقل إلى /auth/users")
    print("3. ابحث عن زر الحذف الأحمر")
    print("4. تحقق من console المتصفح للأخطاء")

if __name__ == '__main__':
    test_delete_route()
