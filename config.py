import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'law_office.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Mail settings
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # Upload settings
    UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Cloudinary settings
    CLOUDINARY_CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME')
    CLOUDINARY_API_KEY = os.environ.get('CLOUDINARY_API_KEY')
    CLOUDINARY_API_SECRET = os.environ.get('CLOUDINARY_API_SECRET')
    
    # Pagination
    POSTS_PER_PAGE = 10
    
    # Languages
    LANGUAGES = ['ar', 'en']
    
    @staticmethod
    def init_app(app):
        # Enhanced database connection diagnostics
        database_url = os.environ.get('DATABASE_URL')
        
        if not database_url:
            print("🚨 خطأ: متغير DATABASE_URL غير موجود!")
            print("📋 الحلول المقترحة:")
            print("   1. تأكد من إعداد DATABASE_URL في Render.com")
            print("   2. راجع ملف DATABASE_SETUP_GUIDE.md")
            print("   3. تحقق من إعدادات Supabase")
            return
            
        if database_url.startswith('sqlite://'):
            print("⚠️  تحذير: يتم استخدام SQLite المحلي")
            print("💾 البيانات ستُحذف عند إعادة التشغيل!")
            print("🔗 لإعداد قاعدة بيانات خارجية، راجع DATABASE_SETUP_GUIDE.md")
            return
            
        # Test PostgreSQL connection
        try:
            import psycopg2
            # Parse connection string
            if 'postgresql://' in database_url or 'postgres://' in database_url:
                # Fix postgres:// to postgresql://
                if database_url.startswith('postgres://'):
                    database_url = database_url.replace('postgres://', 'postgresql://', 1)
                    
                print("🔍 محاولة الاتصال بقاعدة البيانات الخارجية...")
                
                # Extract host for validation
                if '@' in database_url:
                    host_part = database_url.split('@')[1].split(':')[0]
                    print(f"🌐 المضيف: {host_part}")
                    
                    # Validate host format
                    if '.supabase.co' in host_part:
                        if 'pooler' in host_part:
                            print("📡 نوع الاتصال: Connection Pooler")
                        else:
                            print("📡 نوع الاتصال: Direct Connection")
                            
                        # Check for common host name issues
                        if host_part.count('-') < 3:
                            print("⚠️  تحذير: اسم المضيف قد يكون غير مكتمل")
                            print("💡 تأكد من نسخ رابط الاتصال كاملاً من Supabase")
                            
                # Test actual connection
                conn = psycopg2.connect(database_url)
                conn.close()
                print("✅ تم الاتصال بقاعدة البيانات الخارجية بنجاح!")
                print("🎉 جميع البيانات محفوظة ومؤمنة")
                
        except ImportError:
            print("⚠️  مكتبة psycopg2 غير مثبتة")
            print("📦 قم بتثبيتها: pip install psycopg2-binary")
        except Exception as e:
            error_msg = str(e)
            print("❌ فشل الاتصال بقاعدة البيانات الخارجية")
            print(f"🔍 تفاصيل الخطأ: {error_msg}")
            
            # Specific error handling
            if 'could not translate host name' in error_msg:
                print("\n🚨 مشكلة في اسم المضيف:")
                print("   1. تحقق من رابط DATABASE_URL في Render.com")
                print("   2. انسخ رابط جديد من Supabase Settings > Database")
                print("   3. تأكد من اكتمال الرابط (لا توجد أحرف مقطوعة)")
                print("   4. جرب استخدام Direct Connection بدلاً من Pooler")
            elif 'authentication failed' in error_msg:
                print("\n🔐 مشكلة في المصادقة:")
                print("   1. تحقق من كلمة المرور في رابط الاتصال")
                print("   2. أعد إنشاء كلمة مرور جديدة في Supabase")
            elif 'timeout' in error_msg:
                print("\n⏱️  مشكلة في المهلة الزمنية:")
                print("   1. تحقق من اتصال الشبكة")
                print("   2. جرب منطقة Supabase مختلفة")
                
            print("\n🔄 التراجع إلى SQLite المؤقت...")
            print("💾 البيانات ستُحذف عند إعادة التشغيل!")

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
    
    @staticmethod
    def init_app(app):
        Config.init_app(app)
        
        # Additional production checks
        database_url = os.environ.get('DATABASE_URL')
        if not database_url or database_url.startswith('sqlite://'):
            print("🚨 خطأ في الإنتاج: لا توجد قاعدة بيانات خارجية!")
            print("📖 يجب إعداد DATABASE_URL في متغيرات البيئة")
            print("🔗 راجع DATABASE_SETUP_GUIDE.md للحصول على التعليمات")
        else:
            print("✅ الإنتاج: تم الاتصال بقاعدة البيانات الخارجية")
            print(f"🔗 قاعدة البيانات: {database_url.split('@')[1] if '@' in database_url else 'مخفية'}")
            
        # Check required environment variables
        required_vars = ['DATABASE_URL', 'SECRET_KEY']
        missing_vars = [var for var in required_vars if not os.environ.get(var)]
        if missing_vars:
            print(f"⚠️  متغيرات البيئة المفقودة: {', '.join(missing_vars)}")
        else:
            print("✅ جميع متغيرات البيئة المطلوبة متوفرة")

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
