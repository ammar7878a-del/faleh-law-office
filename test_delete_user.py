#!/usr/bin/env python3
"""
اختبار وظيفة حذف المستخدمين
"""

import os
import sys
import unittest
from app import create_app, db
from app.models import User, Case, Appointment
from flask_login import login_user

class TestDeleteUser(unittest.TestCase):
    def setUp(self):
        """إعداد البيئة للاختبار"""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        
        # إنشاء قاعدة البيانات
        db.create_all()
        
        # إنشاء مستخدم مدير للاختبار
        self.admin_user = User(
            username='test_admin',
            email='admin@test.com',
            first_name='مدير',
            last_name='اختبار',
            role='admin'
        )
        self.admin_user.set_password('admin123')
        db.session.add(self.admin_user)
        
        # إنشاء مستخدم عادي للحذف
        self.test_user = User(
            username='test_user',
            email='user@test.com',
            first_name='مستخدم',
            last_name='اختبار',
            role='lawyer'
        )
        self.test_user.set_password('user123')
        db.session.add(self.test_user)
        
        db.session.commit()
    
    def tearDown(self):
        """تنظيف البيئة بعد الاختبار"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def login_as_admin(self):
        """تسجيل الدخول كمدير"""
        return self.client.post('/auth/login', data={
            'username': 'test_admin',
            'password': 'admin123'
        }, follow_redirects=True)
    
    def test_delete_user_success(self):
        """اختبار حذف مستخدم بنجاح"""
        with self.client.session_transaction() as sess:
            sess['_user_id'] = str(self.admin_user.id)
            sess['_fresh'] = True

        # التأكد من وجود المستخدم
        user = User.query.filter_by(username='test_user').first()
        self.assertIsNotNone(user)

        # حذف المستخدم مع تعطيل CSRF للاختبار
        with self.app.test_request_context():
            response = self.client.post(f'/auth/delete_user/{user.id}',
                                      follow_redirects=True,
                                      environ_base={'HTTP_X_CSRF_TOKEN': 'test'})

        # التأكد من حذف المستخدم
        deleted_user = User.query.filter_by(username='test_user').first()
        self.assertIsNone(deleted_user)
    
    def test_delete_user_unauthorized(self):
        """اختبار منع حذف المستخدم بدون صلاحية"""
        # إنشاء مستخدم عادي
        regular_user = User(
            username='regular_user',
            email='regular@test.com',
            first_name='عادي',
            last_name='مستخدم',
            role='lawyer'
        )
        regular_user.set_password('regular123')
        db.session.add(regular_user)
        db.session.commit()
        
        # تسجيل الدخول كمستخدم عادي
        self.client.post('/auth/login', data={
            'username': 'regular_user',
            'password': 'regular123'
        })
        
        # محاولة حذف مستخدم آخر
        response = self.client.post(f'/auth/delete_user/{self.test_user.id}', 
                                  follow_redirects=True)
        
        # التحقق من رفض العملية
        self.assertEqual(response.status_code, 200)
        
        # التأكد من عدم حذف المستخدم
        user = User.query.filter_by(username='test_user').first()
        self.assertIsNotNone(user)
    
    def test_delete_self_prevention(self):
        """اختبار منع المدير من حذف نفسه"""
        # تسجيل الدخول كمدير
        self.login_as_admin()
        
        # محاولة حذف النفس
        response = self.client.post(f'/auth/delete_user/{self.admin_user.id}', 
                                  follow_redirects=True)
        
        # التحقق من رفض العملية
        self.assertEqual(response.status_code, 200)
        
        # التأكد من عدم حذف المدير
        admin = User.query.filter_by(username='test_admin').first()
        self.assertIsNotNone(admin)

if __name__ == '__main__':
    print("🧪 تشغيل اختبارات حذف المستخدمين...")
    unittest.main(verbosity=2)
