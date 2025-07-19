#!/usr/bin/env python3
"""
Quick start script for the Law Office Management System
"""

import os
import sys
import subprocess

def check_python_version():
    """Check if Python version is 3.8 or higher"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 أو أحدث مطلوب")
        print(f"الإصدار الحالي: {sys.version}")
        return False
    return True

def check_virtual_env():
    """Check if virtual environment is activated"""
    return hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)

def install_requirements():
    """Install required packages"""
    print("📦 تثبيت المتطلبات...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("✅ تم تثبيت المتطلبات بنجاح")
        return True
    except subprocess.CalledProcessError:
        print("❌ فشل في تثبيت المتطلبات")
        return False

def setup_database():
    """Initialize the database"""
    print("🗄️ إعداد قاعدة البيانات...")
    try:
        subprocess.check_call([sys.executable, 'init_db.py'])
        print("✅ تم إعداد قاعدة البيانات بنجاح")
        return True
    except subprocess.CalledProcessError:
        print("❌ فشل في إعداد قاعدة البيانات")
        return False

def create_upload_directories():
    """Create upload directories"""
    print("📁 إنشاء مجلدات الرفع...")
    directories = [
        'uploads',
        'uploads/documents',
        'uploads/avatars'
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"✅ تم إنشاء مجلد: {directory}")

def run_application():
    """Run the Flask application"""
    print("🚀 تشغيل التطبيق...")
    print("=" * 50)
    print("المحامي فالح بن عقاب آل عيسى - محاماة واستشارات قانونية")
    print("=" * 50)
    print("🌐 الرابط: http://localhost:5000")
    print("👤 المستخدمون الافتراضيون:")
    print("   - مدير: admin / admin123")
    print("   - محامي: lawyer1 / lawyer123")
    print("   - سكرتير: secretary1 / secretary123")
    print("=" * 50)
    print("اضغط Ctrl+C لإيقاف التطبيق")
    print("=" * 50)

    try:
        # Import and run the app directly
        from app import create_app
        app = create_app()
        app.run(debug=True, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n👋 تم إيقاف التطبيق")
    except Exception as e:
        print(f"❌ فشل في تشغيل التطبيق: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main function"""
    print("🏛️ المحامي فالح بن عقاب آل عيسى")
    print("=" * 40)
    
    # Check Python version
    if not check_python_version():
        return
    
    # Check virtual environment
    if not check_virtual_env():
        print("⚠️ تحذير: لم يتم تفعيل البيئة الافتراضية")
        print("يُنصح بإنشاء وتفعيل بيئة افتراضية أولاً")
        response = input("هل تريد المتابعة؟ (y/n): ")
        if response.lower() != 'y':
            return
    
    # Check if this is first run
    if not os.path.exists('law_office.db'):
        print("🔧 الإعداد الأولي...")
        
        # Install requirements
        if not install_requirements():
            return
        
        # Setup database
        if not setup_database():
            return
        
        # Create upload directories
        create_upload_directories()
        
        print("✅ تم الإعداد الأولي بنجاح!")
        print()
    
    # Run application
    run_application()

if __name__ == '__main__':
    main()
