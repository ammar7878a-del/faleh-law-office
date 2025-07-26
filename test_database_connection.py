#!/usr/bin/env python3
"""
سكريبت لاختبار الاتصال بقاعدة البيانات الخارجية
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

def test_database_connection():
    """اختبار الاتصال بقاعدة البيانات"""
    
    print("🔍 فحص إعدادات قاعدة البيانات...")
    
    # الحصول على رابط قاعدة البيانات من متغيرات البيئة
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        print("❌ لم يتم العثور على متغير DATABASE_URL")
        print("💡 يجب إضافة رابط قاعدة البيانات في متغيرات البيئة")
        print("📖 راجع ملف DATABASE_SETUP_GUIDE.md للتعليمات")
        return False
    
    print(f"✅ تم العثور على DATABASE_URL")
    
    # إخفاء كلمة المرور في العرض
    safe_url = database_url
    if '@' in safe_url and ':' in safe_url:
        parts = safe_url.split('@')
        if len(parts) == 2:
            user_part = parts[0].split('://')[-1]
            if ':' in user_part:
                user, password = user_part.split(':', 1)
                safe_url = safe_url.replace(f':{password}@', ':****@')
    
    print(f"🔗 رابط قاعدة البيانات: {safe_url}")
    
    # إصلاح رابط PostgreSQL إذا لزم الأمر
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
        print("🔧 تم إصلاح رابط PostgreSQL")
    
    try:
        print("🔄 محاولة الاتصال بقاعدة البيانات...")
        
        # إنشاء محرك قاعدة البيانات
        engine = create_engine(
            database_url,
            pool_pre_ping=True,
            pool_recycle=300,
            pool_timeout=20,
            max_overflow=0,
            connect_args={'sslmode': 'require'} if 'postgresql' in database_url else {}
        )
        
        # اختبار الاتصال
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1 as test"))
            test_value = result.fetchone()[0]
            
            if test_value == 1:
                print("✅ نجح الاتصال بقاعدة البيانات!")
                
                # اختبار إضافي: الحصول على معلومات قاعدة البيانات
                if 'postgresql' in database_url:
                    version_result = connection.execute(text("SELECT version()"))
                    version = version_result.fetchone()[0]
                    print(f"📊 نوع قاعدة البيانات: PostgreSQL")
                    print(f"📋 الإصدار: {version.split(',')[0]}")
                    
                    # فحص الجداول الموجودة
                    tables_result = connection.execute(text("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = 'public'
                    """))
                    tables = [row[0] for row in tables_result.fetchall()]
                    
                    if tables:
                        print(f"📋 الجداول الموجودة ({len(tables)}): {', '.join(tables)}")
                    else:
                        print("📋 لا توجد جداول (قاعدة بيانات جديدة)")
                
                return True
                
    except SQLAlchemyError as e:
        print(f"❌ خطأ في الاتصال بقاعدة البيانات:")
        print(f"   {str(e)}")
        
        # نصائح لحل المشاكل الشائعة
        error_str = str(e).lower()
        if 'password authentication failed' in error_str:
            print("💡 نصيحة: تأكد من صحة كلمة المرور في رابط قاعدة البيانات")
        elif 'could not connect to server' in error_str:
            print("💡 نصيحة: تأكد من صحة عنوان الخادم والمنفذ")
        elif 'database' in error_str and 'does not exist' in error_str:
            print("💡 نصيحة: تأكد من وجود قاعدة البيانات")
        elif 'ssl' in error_str:
            print("💡 نصيحة: مشكلة في شهادة SSL، تأكد من إعدادات الاتصال")
        
        return False
        
    except Exception as e:
        print(f"❌ خطأ غير متوقع: {str(e)}")
        return False

def main():
    """الدالة الرئيسية"""
    print("=" * 50)
    print("🧪 اختبار الاتصال بقاعدة البيانات")
    print("=" * 50)
    
    success = test_database_connection()
    
    print("=" * 50)
    if success:
        print("🎉 الاختبار نجح! قاعدة البيانات جاهزة للاستخدام")
        print("✅ البيانات ستكون محفوظة دائماً")
        print("🚀 يمكنك الآن تشغيل التطبيق بأمان")
    else:
        print("❌ فشل الاختبار! يجب إصلاح المشكلة أولاً")
        print("📖 راجع ملف DATABASE_SETUP_GUIDE.md للمساعدة")
        print("🔧 تأكد من إعداد متغير DATABASE_URL بشكل صحيح")
    print("=" * 50)
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
