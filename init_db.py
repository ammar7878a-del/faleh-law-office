#!/usr/bin/env python3
"""
Script to initialize the database with sample data
"""

import os
import sys
from datetime import datetime, timedelta
from decimal import Decimal

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User, Client, Case, Appointment, Invoice, Document

def init_database():
    """Initialize the database with sample data"""
    
    app = create_app()
    
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Check if admin user already exists
        admin = User.query.filter_by(username='admin').first()
        if admin:
            print("Database already initialized!")
            return
        
        print("Initializing database...")
        
        # Create admin user
        admin = User(
            username='admin',
            email='admin@lawfirm.com',
            first_name='مدير',
            last_name='النظام',
            phone='0501234567',
            role='admin',
            is_active=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        
        # Create lawyer user
        lawyer = User(
            username='lawyer1',
            email='lawyer1@lawfirm.com',
            first_name='أحمد',
            last_name='المحامي',
            phone='0501234568',
            role='lawyer',
            is_active=True
        )
        lawyer.set_password('lawyer123')
        db.session.add(lawyer)
        
        # Create secretary user
        secretary = User(
            username='secretary1',
            email='secretary1@lawfirm.com',
            first_name='فاطمة',
            last_name='السكرتيرة',
            phone='0501234569',
            role='secretary',
            is_active=True
        )
        secretary.set_password('secretary123')
        db.session.add(secretary)
        
        # Commit users first to get their IDs
        db.session.commit()
        
        # Create sample clients
        clients_data = [
            {
                'first_name': 'محمد',
                'last_name': 'أحمد',
                'email': 'mohammed.ahmed@email.com',
                'phone': '0501111111',
                'mobile': '0551111111',
                'address': 'الرياض، حي النخيل',
                'national_id': '1234567890',
                'company': 'شركة التقنية المتقدمة'
            },
            {
                'first_name': 'سارة',
                'last_name': 'علي',
                'email': 'sara.ali@email.com',
                'phone': '0502222222',
                'mobile': '0552222222',
                'address': 'جدة، حي الروضة',
                'national_id': '2345678901',
                'company': 'مؤسسة التجارة الحديثة'
            },
            {
                'first_name': 'خالد',
                'last_name': 'محمد',
                'email': 'khalid.mohammed@email.com',
                'phone': '0503333333',
                'mobile': '0553333333',
                'address': 'الدمام، حي الشاطئ',
                'national_id': '3456789012'
            }
        ]
        
        clients = []
        for client_data in clients_data:
            client = Client(**client_data)
            db.session.add(client)
            clients.append(client)
        
        db.session.commit()
        
        # Create sample cases
        cases_data = [
            {
                'case_number': 'C2024-001',
                'title': 'قضية تجارية - نزاع عقد',
                'description': 'نزاع حول تنفيذ عقد توريد بين الشركات',
                'case_type': 'commercial',
                'status': 'active',
                'priority': 'high',
                'client_id': clients[0].id,
                'lawyer_id': lawyer.id,
                'court_name': 'المحكمة التجارية بالرياض',
                'judge_name': 'القاضي عبدالله السعد',
                'opposing_party': 'شركة المقاولات الكبرى',
                'start_date': datetime.now().date() - timedelta(days=30)
            },
            {
                'case_number': 'C2024-002',
                'title': 'قضية عمالية - فصل تعسفي',
                'description': 'دعوى فصل تعسفي ومطالبة بالتعويض',
                'case_type': 'labor',
                'status': 'active',
                'priority': 'medium',
                'client_id': clients[1].id,
                'lawyer_id': lawyer.id,
                'court_name': 'محكمة العمل بجدة',
                'start_date': datetime.now().date() - timedelta(days=15)
            },
            {
                'case_number': 'C2024-003',
                'title': 'قضية مدنية - تعويض أضرار',
                'description': 'مطالبة بتعويض عن أضرار حادث مروري',
                'case_type': 'civil',
                'status': 'closed',
                'priority': 'low',
                'client_id': clients[2].id,
                'lawyer_id': lawyer.id,
                'start_date': datetime.now().date() - timedelta(days=60),
                'end_date': datetime.now().date() - timedelta(days=5)
            }
        ]
        
        cases = []
        for case_data in cases_data:
            case = Case(**case_data)
            db.session.add(case)
            cases.append(case)
        
        db.session.commit()
        
        # Create sample appointments
        appointments_data = [
            {
                'title': 'جلسة محكمة - قضية تجارية',
                'description': 'الجلسة الأولى للقضية التجارية',
                'appointment_type': 'hearing',
                'start_time': datetime.now() + timedelta(days=7, hours=10),
                'end_time': datetime.now() + timedelta(days=7, hours=12),
                'location': 'المحكمة التجارية بالرياض - قاعة 3',
                'status': 'scheduled',
                'user_id': lawyer.id,
                'case_id': cases[0].id,
                'client_id': clients[0].id
            },
            {
                'title': 'اجتماع مع العميل',
                'description': 'مناقشة تطورات القضية العمالية',
                'appointment_type': 'meeting',
                'start_time': datetime.now() + timedelta(days=3, hours=14),
                'end_time': datetime.now() + timedelta(days=3, hours=15),
                'location': 'مكتب المحاماة',
                'status': 'scheduled',
                'user_id': lawyer.id,
                'case_id': cases[1].id,
                'client_id': clients[1].id
            }
        ]
        
        for appointment_data in appointments_data:
            appointment = Appointment(**appointment_data)
            db.session.add(appointment)
        
        # Create sample invoices
        invoices_data = [
            {
                'invoice_number': 'INV-2024-001',
                'description': 'أتعاب قانونية - قضية تجارية',
                'amount': Decimal('15000.00'),
                'tax_amount': Decimal('2250.00'),
                'total_amount': Decimal('17250.00'),
                'status': 'paid',
                'client_id': clients[0].id,
                'case_id': cases[0].id,
                'issue_date': datetime.now().date() - timedelta(days=20),
                'due_date': datetime.now().date() - timedelta(days=10),
                'paid_date': datetime.now().date() - timedelta(days=5),
                'payment_method': 'bank_transfer'
            },
            {
                'invoice_number': 'INV-2024-002',
                'description': 'أتعاب قانونية - قضية عمالية',
                'amount': Decimal('8000.00'),
                'tax_amount': Decimal('1200.00'),
                'total_amount': Decimal('9200.00'),
                'status': 'pending',
                'client_id': clients[1].id,
                'case_id': cases[1].id,
                'issue_date': datetime.now().date() - timedelta(days=10),
                'due_date': datetime.now().date() + timedelta(days=20)
            }
        ]
        
        for invoice_data in invoices_data:
            invoice = Invoice(**invoice_data)
            db.session.add(invoice)
        
        db.session.commit()
        
        print("Database initialized successfully!")
        print("\nDefault users created:")
        print("Admin: username='admin', password='admin123'")
        print("Lawyer: username='lawyer1', password='lawyer123'")
        print("Secretary: username='secretary1', password='secretary123'")
        print("\nSample data includes:")
        print(f"- {len(clients)} clients")
        print(f"- {len(cases)} cases")
        print(f"- {len(appointments_data)} appointments")
        print(f"- {len(invoices_data)} invoices")

if __name__ == '__main__':
    init_database()
