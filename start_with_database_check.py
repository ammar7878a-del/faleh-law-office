#!/usr/bin/env python3
"""
سكريپت تشغيل محسن مع فحص قاعدة البيانات
"""

import os
import sys
import subprocess
import time
from datetime import datetime

def print_banner():
    """طباعة شعار التطبيق"""
    print("=" * 60)
    print("🏛️  نظام إدارة مكتب المحاماة")
    print("⚖️  Law Office Management System")
    print("=" * 60)
    print(f"🕐 وقت التشغيل: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

def check_database_setup():
    """فحص إعداد قاعدة البيانات"""
    print("🔍 فحص إعدادات قاعدة البيانات...")
    
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url and ('postgresql' in database_url or 'postgres' in database_url):
        print("✅ تم العثور على قاعدة بيانات خارجية!")
        print("🔒 البيانات محفوظة دائماً - لن تُحذف أبداً!")
        print("🎉 مشكلة فقدان البيانات محلولة!")
        
        # إخفاء كلمة المرور في العرض
        safe_url = database_url
        if '@' in safe_url and ':' in safe_url:
            parts = safe_url.split('@')
            if len(parts) == 2:
                user_part = parts[0].split('://')[-1]
                if ':' in user_part:
                    user, password = user_part.split(':', 1)
                    safe_url = safe_url.replace(f':{password}@', ':****@')
        
        print(f"🌐 الخادم: {safe_url.split('@')[1].split('/')[0] if '@' in safe_url else 'غير محدد'}")
        return True
    else:
        print("🚨 تحذير: لا توجد قاعدة بيانات خارجية!")
        print("⚠️  البيانات ستُحذف عند إعادة التشغيل!")
        print("💥 هذا يعني أن جميع البيانات ستفقد!")
        print("")
        print("🔧 لحل هذه المشكلة:")
        print("   1. راجع ملف QUICK_DATABASE_FIX.md")
        print("   2. أنشئ قاعدة بيانات مجانية على Supabase")
        print("   3. أضف متغير DATABASE_URL في إعدادات الخادم")
        print("   4. أعد تشغيل التطبيق")
        print("")
        print("🔗 رابط Supabase: https://supabase.com")
        print("📖 دليل سريع: QUICK_DATABASE_FIX.md")
        return False

def check_required_files():
    """فحص الملفات المطلوبة"""
    print("\n📁 فحص الملفات المطلوبة...")
    
    required_files = [
        'final_working.py',
        'requirements.txt'
    ]
    
    missing_files = []
    for file in required_files:
        if os.path.exists(file):
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file}")
            missing_files.append(file)
    
    if missing_files:
        print(f"\n❌ ملفات مفقودة: {', '.join(missing_files)}")
        return False
    
    return True

def install_requirements():
    """تثبيت المتطلبات"""
    print("\n📦 فحص وتثبيت المتطلبات...")
    
    try:
        # فحص إذا كانت المتطلبات مثبتة
        import flask
        import flask_sqlalchemy
        import flask_login
        print("   ✅ المتطلبات الأساسية مثبتة")
        return True
    except ImportError:
        print("   ⚠️ بعض المتطلبات غير مثبتة، محاولة التثبيت...")
        
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
            print("   ✅ تم تثبيت المتطلبات بنجاح")
            return True
        except subprocess.CalledProcessError as e:
            print(f"   ❌ فشل في تثبيت المتطلبات: {e}")
            return False

def create_directories():
    """إنشاء المجلدات المطلوبة"""
    print("\n📂 إنشاء المجلدات المطلوبة...")
    
    directories = [
        'uploads',
        'uploads/documents',
        'uploads/logos',
        'instance'
    ]
    
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            print(f"   ✅ {directory}")
        except Exception as e:
            print(f"   ❌ خطأ في إنشاء {directory}: {e}")

def show_startup_info(database_ok):
    """عرض معلومات التشغيل"""
    print("\n" + "=" * 60)
    print("🚀 معلومات التشغيل:")
    print("=" * 60)
    
    if database_ok:
        print("✅ قاعدة البيانات: محفوظة دائماً (PostgreSQL)")
        print("🔒 البيانات آمنة ولن تُحذف")
    else:
        print("⚠️  قاعدة البيانات: مؤقتة (SQLite)")
        print("💥 البيانات ستُحذف عند إعادة التشغيل!")
        print("🔧 يجب إعداد قاعدة بيانات خارجية")
    
    print(f"🌐 المنفذ: {os.environ.get('PORT', '5000')}")
    print(f"🔧 البيئة: {os.environ.get('FLASK_ENV', 'production')}")
    print("=" * 60)

def start_application():
    """تشغيل التطبيق"""
    print("🚀 بدء تشغيل التطبيق...")
    print("⏳ يرجى الانتظار...")
    print("")
    
    try:
        # تشغيل التطبيق
        if os.path.exists('final_working.py'):
            os.system(f'{sys.executable} final_working.py')
        else:
            print("❌ ملف التطبيق غير موجود!")
            return False
            
    except KeyboardInterrupt:
        print("\n\n🛑 تم إيقاف التطبيق بواسطة المستخدم")
        return True
    except Exception as e:
        print(f"\n❌ خطأ في تشغيل التطبيق: {e}")
        return False

def main():
    """الدالة الرئيسية"""
    print_banner()
    
    # فحص قاعدة البيانات
    database_ok = check_database_setup()
    
    # فحص الملفات المطلوبة
    if not check_required_files():
        print("\n❌ لا يمكن المتابعة بسبب ملفات مفقودة")
        input("\nاضغط Enter للخروج...")
        return
    
    # تثبيت المتطلبات
    if not install_requirements():
        print("\n❌ لا يمكن المتابعة بسبب مشاكل في المتطلبات")
        input("\nاضغط Enter للخروج...")
        return
    
    # إنشاء المجلدات
    create_directories()
    
    # عرض معلومات التشغيل
    show_startup_info(database_ok)
    
    if not database_ok:
        print("\n" + "🚨" * 20)
        print("تحذير مهم: البيانات ستُحذف عند إعادة التشغيل!")
        print("لحل هذه المشكلة، راجع ملف: QUICK_DATABASE_FIX.md")
        print("🚨" * 20)
        
        response = input("\nهل تريد المتابعة رغم ذلك؟ (y/n): ").lower()
        if response != 'y' and response != 'yes':
            print("تم إلغاء التشغيل.")
            return
    
    print("\n🎯 التطبيق جاهز للتشغيل!")
    input("اضغط Enter لبدء التشغيل...")
    
    # تشغيل التطبيق
    start_application()

if __name__ == "__main__":
    main()
