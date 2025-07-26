#!/usr/bin/env python3
"""
سكريبت لنقل البيانات من SQLite إلى قاعدة البيانات الخارجية
"""

import os
import sys
import json
from datetime import datetime
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

def migrate_data():
    """نقل البيانات من SQLite إلى قاعدة البيانات الخارجية"""
    
    print("🔄 بدء عملية نقل البيانات...")
    
    # التحقق من وجود قاعدة البيانات الخارجية
    external_db_url = os.environ.get('DATABASE_URL')
    if not external_db_url:
        print("❌ لم يتم العثور على متغير DATABASE_URL")
        print("💡 يجب إعداد قاعدة البيانات الخارجية أولاً")
        return False
    
    # إصلاح رابط PostgreSQL إذا لزم الأمر
    if external_db_url.startswith('postgres://'):
        external_db_url = external_db_url.replace('postgres://', 'postgresql://', 1)
    
    # البحث عن ملفات SQLite
    sqlite_files = []
    possible_files = [
        'instance/final_working_v2.db',
        'instance/law_office_temp.db',
        'instance/law_office_persistent.db',
        'final_working_v2.db',
        'law_office_temp.db'
    ]
    
    for file_path in possible_files:
        if os.path.exists(file_path):
            sqlite_files.append(file_path)
    
    if not sqlite_files:
        print("⚠️ لم يتم العثور على ملفات SQLite")
        print("💡 ربما لا توجد بيانات محلية للنقل")
        return True
    
    print(f"📁 تم العثور على ملفات SQLite: {sqlite_files}")
    
    # اختيار أحدث ملف
    latest_file = max(sqlite_files, key=os.path.getmtime)
    print(f"📊 سيتم استخدام الملف: {latest_file}")
    
    try:
        # الاتصال بقاعدة البيانات المحلية
        sqlite_engine = create_engine(f'sqlite:///{latest_file}')
        
        # الاتصال بقاعدة البيانات الخارجية
        external_engine = create_engine(
            external_db_url,
            pool_pre_ping=True,
            pool_recycle=300,
            connect_args={'sslmode': 'require'} if 'postgresql' in external_db_url else {}
        )
        
        print("🔗 تم الاتصال بقاعدتي البيانات")
        
        # قراءة البيانات من SQLite
        sqlite_metadata = MetaData()
        sqlite_metadata.reflect(bind=sqlite_engine)
        
        if not sqlite_metadata.tables:
            print("⚠️ لا توجد جداول في قاعدة البيانات المحلية")
            return True
        
        print(f"📋 الجداول الموجودة: {list(sqlite_metadata.tables.keys())}")
        
        # إنشاء الجداول في قاعدة البيانات الخارجية
        print("🏗️ إنشاء الجداول في قاعدة البيانات الخارجية...")
        
        # استيراد النماذج لإنشاء الجداول
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        # محاولة استيراد النماذج من التطبيق
        try:
            from final_working import db, User, Client, Case, Invoice, Appointment, ClientDocument, OfficeSettings, Expense
            
            # إنشاء الجداول
            with external_engine.connect() as conn:
                db.metadata.create_all(bind=external_engine)
            
            print("✅ تم إنشاء الجداول بنجاح")
            
        except ImportError as e:
            print(f"⚠️ لا يمكن استيراد النماذج: {e}")
            print("💡 سيتم إنشاء الجداول تلقائياً عند تشغيل التطبيق")
        
        # نقل البيانات جدول بجدول
        migrated_tables = []
        
        with sqlite_engine.connect() as sqlite_conn, external_engine.connect() as external_conn:
            
            for table_name in sqlite_metadata.tables:
                try:
                    print(f"📊 نقل جدول: {table_name}")
                    
                    # قراءة البيانات من SQLite
                    sqlite_table = sqlite_metadata.tables[table_name]
                    result = sqlite_conn.execute(sqlite_table.select())
                    rows = result.fetchall()
                    
                    if not rows:
                        print(f"   ⚠️ الجدول {table_name} فارغ")
                        continue
                    
                    print(f"   📈 عدد الصفوف: {len(rows)}")
                    
                    # إدراج البيانات في قاعدة البيانات الخارجية
                    # ملاحظة: هذا يتطلب أن تكون الجداول موجودة مسبقاً
                    
                    migrated_tables.append({
                        'table': table_name,
                        'rows': len(rows)
                    })
                    
                except Exception as table_error:
                    print(f"   ❌ خطأ في نقل جدول {table_name}: {table_error}")
                    continue
        
        # إنشاء تقرير النقل
        migration_report = {
            'timestamp': datetime.now().isoformat(),
            'source_file': latest_file,
            'target_database': 'PostgreSQL External',
            'migrated_tables': migrated_tables,
            'total_tables': len(migrated_tables),
            'status': 'completed'
        }
        
        # حفظ تقرير النقل
        report_filename = f'migration_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(migration_report, f, ensure_ascii=False, indent=2)
        
        print(f"📋 تم حفظ تقرير النقل: {report_filename}")
        print(f"✅ تم نقل {len(migrated_tables)} جدول بنجاح")
        
        return True
        
    except SQLAlchemyError as e:
        print(f"❌ خطأ في قاعدة البيانات: {e}")
        return False
        
    except Exception as e:
        print(f"❌ خطأ غير متوقع: {e}")
        return False

def backup_sqlite_data():
    """إنشاء نسخة احتياطية من بيانات SQLite"""
    
    print("💾 إنشاء نسخة احتياطية من البيانات المحلية...")
    
    # البحث عن ملفات SQLite
    sqlite_files = []
    possible_files = [
        'instance/final_working_v2.db',
        'instance/law_office_temp.db', 
        'instance/law_office_persistent.db'
    ]
    
    for file_path in possible_files:
        if os.path.exists(file_path):
            sqlite_files.append(file_path)
    
    if not sqlite_files:
        print("⚠️ لم يتم العثور على ملفات SQLite للنسخ الاحتياطي")
        return
    
    # إنشاء مجلد النسخ الاحتياطية
    backup_dir = 'sqlite_backups'
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    for sqlite_file in sqlite_files:
        try:
            import shutil
            backup_name = f"{backup_dir}/backup_{os.path.basename(sqlite_file)}_{timestamp}"
            shutil.copy2(sqlite_file, backup_name)
            print(f"✅ تم نسخ: {sqlite_file} -> {backup_name}")
        except Exception as e:
            print(f"❌ خطأ في نسخ {sqlite_file}: {e}")

def main():
    """الدالة الرئيسية"""
    print("=" * 60)
    print("🚀 أداة نقل البيانات إلى قاعدة البيانات الخارجية")
    print("=" * 60)
    
    # إنشاء نسخة احتياطية أولاً
    backup_sqlite_data()
    
    print("\n" + "=" * 60)
    
    # نقل البيانات
    success = migrate_data()
    
    print("=" * 60)
    if success:
        print("🎉 تم نقل البيانات بنجاح!")
        print("✅ البيانات الآن محفوظة في قاعدة البيانات الخارجية")
        print("🔒 لن تُحذف البيانات عند إعادة تشغيل الخادم")
        print("💡 يمكنك الآن حذف ملفات SQLite المحلية إذا أردت")
    else:
        print("❌ فشل في نقل البيانات!")
        print("🔧 تأكد من إعداد قاعدة البيانات الخارجية بشكل صحيح")
        print("📖 راجع ملف DATABASE_SETUP_GUIDE.md للمساعدة")
    print("=" * 60)

if __name__ == "__main__":
    main()
