#!/usr/bin/env python3
"""
ملف تشغيل مبسط لتشخيص المشاكل
"""

import sys
import traceback

def test_imports():
    """اختبار الاستيرادات"""
    print("🔍 اختبار الاستيرادات...")
    
    try:
        print("  - Flask...")
        from flask import Flask
        print("    ✅ Flask")
        
        print("  - Flask extensions...")
        from flask_sqlalchemy import SQLAlchemy
        from flask_login import LoginManager
        from flask_mail import Mail
        from flask_migrate import Migrate
        print("    ✅ Flask extensions")
        
        print("  - Flask-WTF...")
        from flask_wtf.csrf import CSRFProtect
        print("    ✅ Flask-WTF")
        
        print("  - Config...")
        from config import config
        print("    ✅ Config")
        
        print("  - App models...")
        from app.models import User
        print("    ✅ Models")
        
        return True
        
    except Exception as e:
        print(f"    ❌ خطأ في الاستيراد: {e}")
        traceback.print_exc()
        return False

def test_app_creation():
    """اختبار إنشاء التطبيق"""
    print("\n🏗️ اختبار إنشاء التطبيق...")
    
    try:
        from app import create_app
        app = create_app()
        print("    ✅ تم إنشاء التطبيق بنجاح")
        return app
        
    except Exception as e:
        print(f"    ❌ خطأ في إنشاء التطبيق: {e}")
        traceback.print_exc()
        return None

def test_database():
    """اختبار قاعدة البيانات"""
    print("\n🗄️ اختبار قاعدة البيانات...")
    
    try:
        from app import create_app, db
        app = create_app()
        
        with app.app_context():
            # اختبار الاتصال بقاعدة البيانات
            from app.models import User
            user_count = User.query.count()
            print(f"    ✅ عدد المستخدمين: {user_count}")
            return True
            
    except Exception as e:
        print(f"    ❌ خطأ في قاعدة البيانات: {e}")
        traceback.print_exc()
        return False

def run_app():
    """تشغيل التطبيق"""
    print("\n🚀 تشغيل التطبيق...")
    
    try:
        from app import create_app
        app = create_app()
        
        print("=" * 50)
        print("المحامي فالح بن عقاب آل عيسى")
        print("=" * 50)
        print("🌐 الرابط: http://127.0.0.1:5000")
        print("👤 مدير: admin / admin123")
        print("=" * 50)
        print("اضغط Ctrl+C لإيقاف التطبيق")
        print("=" * 50)
        
        app.run(debug=True, host='127.0.0.1', port=5000, use_reloader=False)
        
    except KeyboardInterrupt:
        print("\n👋 تم إيقاف التطبيق")
    except Exception as e:
        print(f"\n❌ خطأ في تشغيل التطبيق: {e}")
        traceback.print_exc()

def main():
    """الدالة الرئيسية"""
    print("🏛️ تشخيص نظام إدارة مكتب المحاماة")
    print("=" * 50)
    
    # اختبار الاستيرادات
    if not test_imports():
        print("\n❌ فشل في الاستيرادات. تحقق من تثبيت المتطلبات.")
        return
    
    # اختبار إنشاء التطبيق
    app = test_app_creation()
    if not app:
        print("\n❌ فشل في إنشاء التطبيق.")
        return
    
    # اختبار قاعدة البيانات
    if not test_database():
        print("\n❌ فشل في الاتصال بقاعدة البيانات.")
        return
    
    print("\n✅ جميع الاختبارات نجحت!")
    
    # تشغيل التطبيق
    run_app()

if __name__ == '__main__':
    main()
