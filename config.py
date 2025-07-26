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
    
    # Pagination
    POSTS_PER_PAGE = 10
    
    # Languages
    LANGUAGES = ['ar', 'en']
    
    @staticmethod
    def init_app(app):
        # Check if external database is configured
        database_url = os.environ.get('DATABASE_URL')
        if not database_url or database_url.startswith('sqlite://'):
            print("⚠️  تحذير: لا توجد قاعدة بيانات خارجية!")
            print("📖 لحل هذه المشكلة، راجع ملف DATABASE_SETUP_GUIDE.md")
            print("🔗 وقم بإعداد Supabase كما هو موضح في الدليل")
            print("💾 البيانات ستُحذف عند إعادة التشغيل!")
        else:
            print("✅ تم الاتصال بقاعدة البيانات الخارجية بنجاح")
            print(f"🔗 قاعدة البيانات: {database_url[:50]}...")
        pass

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
