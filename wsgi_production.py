#!/usr/bin/env python3
"""
ملف WSGI للنشر الإنتاجي
يحل مشكلة تحذير خادم التطوير
"""

import os
import sys
from datetime import datetime

# إضافة المجلد الحالي إلى مسار Python
sys.path.insert(0, os.path.dirname(__file__))

def create_app():
    """إنشاء وإعداد التطبيق للنشر الإنتاجي"""
    
    print("🚀 بدء تشغيل النظام في وضع الإنتاج...")
    print(f"🕐 الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # استيراد التطبيق
    try:
        from final_working import app, db, User, OfficeSettings, Expense
        print("✅ تم تحميل التطبيق بنجاح")
    except ImportError as e:
        print(f"❌ خطأ في استيراد التطبيق: {e}")
        raise
    
    # إعداد التطبيق
    with app.app_context():
        try:
            # إنشاء الجداول
            db.create_all()
            print("✅ تم إنشاء/تحديث جداول قاعدة البيانات")
            
            # إنشاء مستخدم افتراضي إذا لم يكن موجوداً
            if User.query.count() == 0:
                admin_user = User(
                    username='admin',
                    first_name='مدير',
                    last_name='النظام',
                    email='admin@lawoffice.com',
                    role='admin'
                )
                admin_user.set_password('admin123')
                db.session.add(admin_user)
                db.session.commit()
                print("✅ تم إنشاء مستخدم المدير الافتراضي:")
                print("   اسم المستخدم: admin")
                print("   كلمة المرور: admin123")
            else:
                # تحديث المستخدم الأول ليكون مدير إذا لم يكن له دور
                first_user = User.query.first()
                if first_user and not first_user.role:
                    first_user.role = 'admin'
                    db.session.commit()
                    print("✅ تم تحديث المستخدم الأول ليكون مدير")
            
            # إنشاء إعدادات المكتب الافتراضية
            if OfficeSettings.query.count() == 0:
                default_settings = OfficeSettings(
                    office_name='مكتب فالح آل عيسى للمحاماة',
                    office_name_en='Faleh Al-Issa Law Office',
                    address='الرياض، المملكة العربية السعودية',
                    city='الرياض',
                    country='المملكة العربية السعودية',
                    currency='ريال',
                    language='ar',
                    timezone='Asia/Riyadh',
                    description='مكتب محاماة متخصص في جميع الخدمات القانونية'
                )
                db.session.add(default_settings)
                db.session.commit()
                print("✅ تم إنشاء إعدادات المكتب الافتراضية")
            
            # إنشاء بعض المصروفات التجريبية
            if Expense.query.count() == 0:
                sample_expenses = [
                    Expense(
                        title='أوراق وقرطاسية',
                        description='شراء أوراق طباعة وأقلام ومستلزمات مكتبية',
                        amount=250.00,
                        category='مكتبية',
                        expense_date=datetime.now(),
                        vendor='مكتبة الرياض',
                        payment_method='نقدي',
                        created_by=1
                    ),
                    Expense(
                        title='اشتراك الإنترنت',
                        description='فاتورة الإنترنت الشهرية',
                        amount=300.00,
                        category='اتصالات',
                        expense_date=datetime.now(),
                        vendor='شركة الاتصالات',
                        payment_method='تحويل بنكي',
                        created_by=1
                    )
                ]
                
                for expense in sample_expenses:
                    db.session.add(expense)
                db.session.commit()
                print("✅ تم إنشاء مصروفات تجريبية")
                
        except Exception as e:
            print(f"⚠️ تحذير في إعداد قاعدة البيانات: {e}")
    
    # تفعيل النسخ الاحتياطي التلقائي
    try:
        from final_working import start_backup_scheduler
        start_backup_scheduler()
        print("✅ تم تفعيل النسخ الاحتياطي التلقائي")
    except Exception as backup_error:
        print(f"⚠️ تحذير: لم يتم تفعيل النسخ الاحتياطي: {backup_error}")
    
    print("🎉 التطبيق جاهز للعمل في وضع الإنتاج!")
    print("="*50)
    
    return app

# إنشاء التطبيق للنشر الإنتاجي
application = create_app()

# للتوافق مع Gunicorn
app = application

if __name__ == "__main__":
    # للاختبار المحلي فقط
    port = int(os.environ.get('PORT', 5000))
    application.run(host='0.0.0.0', port=port, debug=False)
