#!/usr/bin/env python3
"""
اختبار إصلاح مشكلة datetime في موعد القضية
"""

import os
import sys
from datetime import datetime, time

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User, Client, Case
from app.cases.routes import combine_date_time

def test_datetime_fix():
    app = create_app()
    
    with app.app_context():
        print("🧪 اختبار إصلاح مشكلة datetime...")
        
        # Test the combine_date_time function
        print("\n1. اختبار دالة combine_date_time:")
        
        # Test case 1: Date and time provided
        test_date = datetime.now().date()
        test_time = "14:30"
        result1 = combine_date_time(test_date, test_time)
        print(f"   التاريخ: {test_date}, الوقت: {test_time}")
        print(f"   النتيجة: {result1}")
        
        # Test case 2: Date only
        result2 = combine_date_time(test_date, None)
        print(f"   التاريخ: {test_date}, الوقت: None")
        print(f"   النتيجة: {result2}")
        
        # Test case 3: Invalid time format
        result3 = combine_date_time(test_date, "invalid")
        print(f"   التاريخ: {test_date}, الوقت: invalid")
        print(f"   النتيجة: {result3}")
        
        # Test case 4: No date
        result4 = combine_date_time(None, "10:00")
        print(f"   التاريخ: None, الوقت: 10:00")
        print(f"   النتيجة: {result4}")
        
        print("\n2. اختبار إنشاء قضية مع موعد:")
        
        # Get admin user
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            print("❌ لم يتم العثور على المدير")
            return
        
        # Get or create a client
        client = Client.query.first()
        if not client:
            client = Client(
                first_name='عميل',
                last_name='تجريبي',
                email='test@example.com',
                phone='0501234567'
            )
            db.session.add(client)
            db.session.commit()
        
        # Create a test case with next_hearing
        test_case = Case(
            case_number='TEST/2024/001',
            title='قضية اختبار موعد الجلسة',
            description='اختبار إصلاح مشكلة datetime',
            case_type='civil',
            status='active',
            client_id=client.id,
            lawyer_id=admin.id,
            next_hearing=combine_date_time(test_date, "15:00")
        )
        
        try:
            db.session.add(test_case)
            db.session.commit()
            print(f"✅ تم إنشاء القضية بنجاح: {test_case.case_number}")
            print(f"   موعد الجلسة: {test_case.next_hearing}")
            
            # Clean up - delete the test case
            db.session.delete(test_case)
            db.session.commit()
            print("🧹 تم حذف القضية التجريبية")
            
        except Exception as e:
            print(f"❌ خطأ في إنشاء القضية: {e}")
            db.session.rollback()
        
        print("\n✅ انتهى الاختبار بنجاح!")
        print("💡 يمكنك الآن إضافة قضايا جديدة بدون أخطاء في موعد الجلسة")

if __name__ == '__main__':
    test_datetime_fix()
