#!/usr/bin/env python3
"""
نظام النسخ الاحتياطي التلقائي
يحفظ البيانات في GitHub كنسخة احتياطية
"""

import os
import json
import sqlite3
from datetime import datetime
import subprocess
import shutil
from pathlib import Path

def export_database_to_json():
    """تصدير قاعدة البيانات إلى JSON"""
    try:
        # الاتصال بقاعدة البيانات
        db_path = 'final_working_v2.db'
        if not os.path.exists(db_path):
            print("❌ قاعدة البيانات غير موجودة")
            return None
            
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # للحصول على النتائج كـ dictionary
        cursor = conn.cursor()
        
        backup_data = {
            'timestamp': datetime.now().isoformat(),
            'tables': {}
        }
        
        # الحصول على قائمة الجداول
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table['name']
            if table_name.startswith('sqlite_'):
                continue  # تجاهل جداول النظام
                
            print(f"📊 تصدير جدول: {table_name}")
            
            # الحصول على بيانات الجدول
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            
            # تحويل البيانات إلى قائمة من القواميس
            backup_data['tables'][table_name] = []
            for row in rows:
                row_dict = {}
                for key in row.keys():
                    value = row[key]
                    # تحويل التواريخ إلى نص
                    if isinstance(value, datetime):
                        value = value.isoformat()
                    row_dict[key] = value
                backup_data['tables'][table_name].append(row_dict)
        
        conn.close()
        
        # حفظ النسخة الاحتياطية
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'backup_{timestamp}.json'
        
        with open(backup_filename, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ تم تصدير قاعدة البيانات إلى: {backup_filename}")
        return backup_filename
        
    except Exception as e:
        print(f"❌ خطأ في تصدير قاعدة البيانات: {e}")
        return None

def backup_uploads_folder():
    """نسخ احتياطي لمجلد الملفات المرفوعة"""
    try:
        uploads_dir = 'uploads'
        if not os.path.exists(uploads_dir):
            print("❌ مجلد الملفات غير موجود")
            return None
            
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = f'uploads_backup_{timestamp}'
        
        # نسخ المجلد
        shutil.copytree(uploads_dir, backup_dir)
        
        # إنشاء ملف معلومات
        info_file = os.path.join(backup_dir, 'backup_info.txt')
        with open(info_file, 'w', encoding='utf-8') as f:
            f.write(f"نسخة احتياطية من مجلد الملفات\n")
            f.write(f"التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"عدد الملفات: {len(list(Path(uploads_dir).rglob('*')))}\n")
        
        print(f"✅ تم نسخ مجلد الملفات إلى: {backup_dir}")
        return backup_dir
        
    except Exception as e:
        print(f"❌ خطأ في نسخ مجلد الملفات: {e}")
        return None

def create_full_backup():
    """إنشاء نسخة احتياطية كاملة"""
    print("🔄 بدء إنشاء النسخة الاحتياطية...")
    
    # تصدير قاعدة البيانات
    db_backup = export_database_to_json()
    
    # نسخ الملفات
    files_backup = backup_uploads_folder()
    
    # إنشاء ملف تقرير
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = f'backup_report_{timestamp}.txt'
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("📋 تقرير النسخة الاحتياطية\n")
        f.write("=" * 40 + "\n")
        f.write(f"التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"قاعدة البيانات: {'✅ نجح' if db_backup else '❌ فشل'}\n")
        f.write(f"الملفات: {'✅ نجح' if files_backup else '❌ فشل'}\n")
        
        if db_backup:
            f.write(f"ملف قاعدة البيانات: {db_backup}\n")
        if files_backup:
            f.write(f"مجلد الملفات: {files_backup}\n")
    
    print(f"📋 تم إنشاء تقرير النسخة الاحتياطية: {report_file}")
    
    return {
        'database': db_backup,
        'files': files_backup,
        'report': report_file,
        'success': bool(db_backup or files_backup)
    }

def restore_from_backup(backup_file):
    """استعادة البيانات من نسخة احتياطية"""
    try:
        if not os.path.exists(backup_file):
            print(f"❌ ملف النسخة الاحتياطية غير موجود: {backup_file}")
            return False
            
        print(f"🔄 استعادة البيانات من: {backup_file}")
        
        with open(backup_file, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        
        # الاتصال بقاعدة البيانات
        conn = sqlite3.connect('final_working_v2.db')
        cursor = conn.cursor()
        
        # استعادة البيانات لكل جدول
        for table_name, rows in backup_data['tables'].items():
            if not rows:
                continue
                
            print(f"📊 استعادة جدول: {table_name}")
            
            # حذف البيانات الحالية
            cursor.execute(f"DELETE FROM {table_name}")
            
            # إدراج البيانات المستعادة
            for row in rows:
                columns = ', '.join(row.keys())
                placeholders = ', '.join(['?' for _ in row.keys()])
                values = list(row.values())
                
                cursor.execute(f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})", values)
        
        conn.commit()
        conn.close()
        
        print("✅ تم استعادة البيانات بنجاح")
        return True
        
    except Exception as e:
        print(f"❌ خطأ في استعادة البيانات: {e}")
        return False

def auto_backup():
    """نسخ احتياطي تلقائي"""
    print("🤖 تشغيل النسخ الاحتياطي التلقائي...")
    
    result = create_full_backup()
    
    if result['success']:
        print("✅ تم إنشاء النسخة الاحتياطية بنجاح")
        
        # محاولة رفع النسخة الاحتياطية إلى Git (إذا كان متاح)
        try:
            subprocess.run(['git', 'add', '.'], check=True, capture_output=True)
            subprocess.run(['git', 'commit', '-m', f'Auto backup {datetime.now().strftime("%Y-%m-%d %H:%M")}'], 
                         check=True, capture_output=True)
            print("✅ تم رفع النسخة الاحتياطية إلى Git")
        except:
            print("⚠️ لم يتم رفع النسخة الاحتياطية إلى Git")
    else:
        print("❌ فشل في إنشاء النسخة الاحتياطية")
    
    return result

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'backup':
            create_full_backup()
        elif command == 'restore' and len(sys.argv) > 2:
            restore_from_backup(sys.argv[2])
        elif command == 'auto':
            auto_backup()
        else:
            print("الاستخدام:")
            print("  python backup_system.py backup     - إنشاء نسخة احتياطية")
            print("  python backup_system.py restore <file> - استعادة من نسخة احتياطية")
            print("  python backup_system.py auto       - نسخ احتياطي تلقائي")
    else:
        create_full_backup()
