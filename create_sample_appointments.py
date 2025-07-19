#!/usr/bin/env python3
"""
إنشاء بيانات تجريبية للمواعيد لاختبار النظام
"""

import os
import sys
from datetime import datetime, timedelta

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User, Client, Case, Appointment

def create_sample_appointments():
    app = create_app()
    
    with app.app_context():
        print("إنشاء بيانات تجريبية للمواعيد...")
        
        # Get existing users, clients, and cases
        admin = User.query.filter_by(username='admin').first()
        lawyer = User.query.filter_by(role='lawyer').first()
        
        if not admin:
            print("خطأ: لم يتم العثور على المدير")
            return
        
        # Create sample clients if they don't exist
        clients = Client.query.all()
        if not clients:
            print("إنشاء عملاء تجريبيين...")
            client1 = Client(
                first_name='أحمد',
                last_name='محمد',
                email='ahmed@example.com',
                phone='0501234567',
                address='الرياض، المملكة العربية السعودية'
            )
            client2 = Client(
                first_name='فاطمة',
                last_name='علي',
                email='fatima@example.com',
                phone='0501234568',
                address='جدة، المملكة العربية السعودية'
            )
            db.session.add(client1)
            db.session.add(client2)
            db.session.commit()
            clients = [client1, client2]
        
        # Create sample cases if they don't exist
        cases = Case.query.all()
        if not cases:
            print("إنشاء قضايا تجريبية...")
            case1 = Case(
                case_number='2024/001',
                title='قضية عقد عمل',
                description='نزاع حول عقد عمل',
                case_type='labor',
                status='active',
                client_id=clients[0].id,
                lawyer_id=lawyer.id if lawyer else admin.id
            )
            case2 = Case(
                case_number='2024/002',
                title='قضية عقار',
                description='نزاع حول ملكية عقار',
                case_type='real_estate',
                status='active',
                client_id=clients[1].id,
                lawyer_id=lawyer.id if lawyer else admin.id
            )
            db.session.add(case1)
            db.session.add(case2)
            db.session.commit()
            cases = [case1, case2]
        
        # Check if appointments already exist
        existing_appointments = Appointment.query.count()
        if existing_appointments > 0:
            print(f"يوجد {existing_appointments} موعد بالفعل")
            return
        
        # Create sample appointments
        now = datetime.now()
        
        appointments_data = [
            {
                'title': 'جلسة محكمة - قضية عقد العمل',
                'description': 'جلسة استماع أولى في قضية عقد العمل',
                'appointment_type': 'hearing',
                'start_time': now + timedelta(days=2, hours=10),
                'end_time': now + timedelta(days=2, hours=12),
                'location': 'محكمة العمل - الرياض',
                'case_id': cases[0].id,
                'user_id': lawyer.id if lawyer else admin.id,
                'status': 'scheduled'
            },
            {
                'title': 'اجتماع مع العميل أحمد محمد',
                'description': 'مناقشة تطورات القضية وجمع المستندات',
                'appointment_type': 'meeting',
                'start_time': now + timedelta(days=1, hours=14),
                'end_time': now + timedelta(days=1, hours=15),
                'location': 'مكتب المحاماة',
                'case_id': cases[0].id,
                'user_id': lawyer.id if lawyer else admin.id,
                'status': 'scheduled'
            },
            {
                'title': 'استشارة قانونية - فاطمة علي',
                'description': 'استشارة حول قضية العقار',
                'appointment_type': 'consultation',
                'start_time': now + timedelta(days=3, hours=16),
                'end_time': now + timedelta(days=3, hours=17),
                'location': 'مكتب المحاماة',
                'case_id': cases[1].id,
                'user_id': lawyer.id if lawyer else admin.id,
                'status': 'scheduled'
            },
            {
                'title': 'جلسة محكمة - قضية العقار',
                'description': 'جلسة نظر الدعوى',
                'appointment_type': 'hearing',
                'start_time': now + timedelta(days=7, hours=9),
                'end_time': now + timedelta(days=7, hours=11),
                'location': 'محكمة الأحوال الشخصية - جدة',
                'case_id': cases[1].id,
                'user_id': lawyer.id if lawyer else admin.id,
                'status': 'scheduled'
            },
            {
                'title': 'مراجعة المستندات',
                'description': 'مراجعة وتحضير المستندات للجلسة القادمة',
                'appointment_type': 'other',
                'start_time': now + timedelta(hours=2),
                'end_time': now + timedelta(hours=4),
                'location': 'مكتب المحاماة',
                'user_id': admin.id,
                'status': 'scheduled'
            }
        ]
        
        print("إنشاء المواعيد التجريبية...")
        for appointment_data in appointments_data:
            appointment = Appointment(**appointment_data)
            db.session.add(appointment)
        
        db.session.commit()
        print(f"تم إنشاء {len(appointments_data)} موعد تجريبي بنجاح!")
        
        # Display created appointments
        print("\nالمواعيد المنشأة:")
        for appointment in Appointment.query.all():
            print(f"- {appointment.title} ({appointment.start_time.strftime('%Y-%m-%d %H:%M')})")

if __name__ == '__main__':
    create_sample_appointments()
