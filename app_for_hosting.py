#!/usr/bin/env python3
"""
نظام إدارة مكتب المحاماة - نسخة للاستضافة الخارجية
المحامي فالح بن عقاب آل عيسى
"""

import os
import sys

# إضافة المجلد الحالي للمسار
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# استيراد التطبيق الأساسي
from final_working import app, db, User

if __name__ == '__main__':
    # إعدادات للاستضافة الخارجية
    port = int(os.environ.get('PORT', 8080))
    host = os.environ.get('HOST', '0.0.0.0')
    debug_mode = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    with app.app_context():
        db.create_all()
        
        if User.query.count() == 0:
            admin = User(username='admin', first_name='مدير', last_name='النظام')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("✅ تم إنشاء المستخدم الافتراضي")
    
    print("="*50)
    print("🚀 نظام إدارة مكتب المحاماة")
    print("📧 المحامي فالح بن عقاب آل عيسى")
    print("="*50)
    print(f"🌐 الخادم يعمل على: http://{host}:{port}")
    print("👤 بيانات الدخول: admin / admin123")
    print("="*50)
    
    try:
        print("🔄 بدء تشغيل الخادم...")
        app.run(debug=debug_mode, host=host, port=port)
    except Exception as e:
        print(f"❌ خطأ في تشغيل الخادم: {e}")
        print("💡 تأكد من أن البورت غير مستخدم من برنامج آخر")
