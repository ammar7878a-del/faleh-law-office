#!/usr/bin/env python3
"""
WSGI Entry Point for Law Office Management System
نقطة دخول WSGI لنظام إدارة مكتب المحاماة

هذا الملف مطلوب للاستضافات التي تدعم Python مثل:
- Heroku
- Railway
- PythonAnywhere
- DigitalOcean App Platform
"""

import os
import sys

# إضافة المجلد الحالي للمسار
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# استيراد التطبيق
try:
    from final_working import app
    print("✅ تم تحميل التطبيق بنجاح")
except ImportError as e:
    print(f"❌ خطأ في تحميل التطبيق: {e}")
    # إنشاء تطبيق بديل في حالة الخطأ
    from flask import Flask
    app = Flask(__name__)
    
    @app.route('/')
    def error_page():
        return '''
        <html dir="rtl">
        <head>
            <meta charset="utf-8">
            <title>خطأ في التحميل</title>
            <style>
                body { font-family: Arial; text-align: center; padding: 50px; }
                .error { color: red; background: #ffe6e6; padding: 20px; border-radius: 10px; }
            </style>
        </head>
        <body>
            <h1>🚨 خطأ في تحميل النظام</h1>
            <div class="error">
                <p>لم يتم العثور على ملف final_working.py</p>
                <p>تأكد من رفع جميع الملفات المطلوبة</p>
            </div>
        </body>
        </html>
        '''

# إعداد قاعدة البيانات
try:
    with app.app_context():
        from final_working import db, User
        db.create_all()
        
        # إنشاء مستخدم افتراضي إذا لم يوجد
        if User.query.count() == 0:
            admin = User(username='admin', first_name='مدير', last_name='النظام')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("✅ تم إنشاء المستخدم الافتراضي")
except Exception as e:
    print(f"⚠️ تحذير في إعداد قاعدة البيانات: {e}")

# تصدير التطبيق للـ WSGI server
application = app

if __name__ == "__main__":
    # للتشغيل المحلي
    port = int(os.environ.get('PORT', 8080))
    host = os.environ.get('HOST', '0.0.0.0')
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    print("="*50)
    print("🚀 نظام إدارة مكتب المحاماة")
    print("📧 المحامي فالح بن عقاب آل عيسى")
    print("="*50)
    print(f"🌐 الخادم: http://{host}:{port}")
    print("👤 المستخدم: admin")
    print("🔑 كلمة المرور: admin123")
    print("="*50)
    
    app.run(host=host, port=port, debug=debug)
