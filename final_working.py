#!/usr/bin/env python3

# إعداد دعم PostgreSQL باستخدام pg8000
import sys

from flask import Flask, render_template_string, request, redirect, url_for, flash, send_from_directory, abort
from flask_sqlalchemy import SQLAlchemy
# تعطيل مؤقت لنظام تسجيل الدخول
# from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from functools import wraps
import os
import mimetypes
import threading
import time
import json

app = Flask(__name__)

# نظام تسجيل الدخول الحقيقي
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'يرجى تسجيل الدخول للوصول لهذه الصفحة'
login_manager.login_message_category = 'info'
app.config['SECRET_KEY'] = 'final-working-key'

# إعدادات قاعدة البيانات - استخدام قاعدة بيانات خارجية دائماً
DATABASE_URL = os.environ.get('DATABASE_URL')

def setup_database():
    """إعداد قاعدة البيانات مع فحص شامل"""
    global DATABASE_URL

    print("🔍 فحص إعدادات قاعدة البيانات...")

    if DATABASE_URL and ('postgresql' in DATABASE_URL or 'postgres' in DATABASE_URL):
        # استخدام PostgreSQL للحفظ الدائم
        try:
            # إصلاح رابط PostgreSQL إذا لزم الأمر
            if DATABASE_URL.startswith('postgres://'):
                DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
                print("🔧 تم إصلاح رابط PostgreSQL")

            # اختبار الاتصال أولاً
            from sqlalchemy import create_engine, text
            test_engine = create_engine(
                DATABASE_URL,
                pool_pre_ping=True,
                pool_recycle=300,
                pool_timeout=20,
                max_overflow=0,
                connect_args={'sslmode': 'require'}
            )

            # اختبار الاتصال
            with test_engine.connect() as conn:
                conn.execute(text("SELECT 1"))

            # إعدادات PostgreSQL مع psycopg2
            app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
            app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
                'pool_pre_ping': True,
                'pool_recycle': 300,
                'pool_timeout': 20,
                'max_overflow': 0,
                'connect_args': {
                    'sslmode': 'require'
                }
            }

            print(f"🗄️ ✅ استخدام قاعدة بيانات خارجية: PostgreSQL")
            print(f"🔒 البيانات محفوظة دائماً - لن تُحذف أبداً!")
            print(f"🎉 مشكلة فقدان البيانات محلولة نهائياً!")
            print(f"🌐 الخادم: {DATABASE_URL.split('@')[1].split('/')[0] if '@' in DATABASE_URL else 'غير محدد'}")

            return True

        except Exception as pg_error:
            print(f"❌ خطأ في الاتصال بـ PostgreSQL: {pg_error}")
            print(f"🔧 التحقق من:")
            print(f"   - صحة رابط قاعدة البيانات")
            print(f"   - كلمة المرور")
            print(f"   - الاتصال بالإنترنت")
            print(f"⚠️ التراجع إلى SQLite المؤقت...")

            # التراجع إلى SQLite
            app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///emergency_backup.db'
            print(f"⚠️ تم التراجع إلى SQLite (emergency_backup.db)")
            return False

    else:
        # تحذير: لا توجد قاعدة بيانات خارجية
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///law_office_temp.db'
        print(f"🚨 تحذير: لا توجد قاعدة بيانات خارجية!")
        print(f"⚠️ البيانات ستُحذف عند إعادة التشغيل!")
        print(f"💡 لحل هذه المشكلة:")
        print(f"   1. راجع ملف DATABASE_SETUP_GUIDE.md")
        print(f"   2. أنشئ قاعدة بيانات مجانية على Supabase")
        print(f"   3. أضف متغير DATABASE_URL في إعدادات الخادم")
        print(f"🔗 رابط Supabase: https://supabase.com")
        return False

# تشغيل إعداد قاعدة البيانات
database_setup_success = setup_database()

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

def get_database_status():
    """الحصول على حالة قاعدة البيانات للعرض في الواجهة"""
    status = {
        'type': 'غير محدد',
        'status': 'غير متصل',
        'persistent': False,
        'warning': None,
        'server': 'غير محدد'
    }

    try:
        db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')

        if 'postgresql' in db_uri:
            status['type'] = 'PostgreSQL (خارجي)'
            status['persistent'] = True
            status['status'] = 'متصل ✅'

            # استخراج معلومات الخادم
            if '@' in db_uri:
                server_part = db_uri.split('@')[1].split('/')[0]
                status['server'] = server_part

        elif 'sqlite' in db_uri:
            status['type'] = 'SQLite (محلي)'
            status['persistent'] = False
            status['status'] = 'متصل ⚠️'
            status['warning'] = 'البيانات ستُحذف عند إعادة التشغيل!'

            # اسم ملف قاعدة البيانات
            if '///' in db_uri:
                db_file = db_uri.split('///')[-1]
                status['server'] = f'ملف محلي: {db_file}'

        # فحص الاتصال الفعلي
        try:
            with db.engine.connect() as conn:
                conn.execute(db.text("SELECT 1"))
            status['connection_test'] = 'نجح ✅'
        except:
            status['connection_test'] = 'فشل ❌'
            status['status'] = 'خطأ في الاتصال'

    except Exception as e:
        status['status'] = f'خطأ: {str(e)}'

    return status

# إضافة دالة حالة قاعدة البيانات للـ templates
@app.template_global()
def get_db_status():
    """إرجاع حالة قاعدة البيانات للاستخدام في templates"""
    return get_database_status()

# إعدادات رفع الملفات - للخادم السحابي
# استخدام مجلد uploads في نفس مجلد التطبيق
try:
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    # في حالة تشغيل الكود من سطر الأوامر
    CURRENT_DIR = os.getcwd()
UPLOAD_FOLDER = os.path.join(CURRENT_DIR, 'uploads')
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# إنشاء مجلد الرفع إذا لم يكن موجوداً
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
    # إنشاء المجلدات الفرعية
    os.makedirs(os.path.join(UPLOAD_FOLDER, 'documents'), exist_ok=True)
    os.makedirs(os.path.join(UPLOAD_FOLDER, 'logos'), exist_ok=True)

print(f"🔧 مجلد الرفع المحدد: {UPLOAD_FOLDER}")
print(f"🔧 المجلد موجود: {os.path.exists(UPLOAD_FOLDER)}")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def safe_filename_with_timestamp(original_filename):
    """
    إنشاء اسم ملف آمن مع timestamp مع الحفاظ على الامتداد
    """
    if not original_filename:
        return None

    # فصل الاسم والامتداد
    if '.' in original_filename:
        name_part, extension = original_filename.rsplit('.', 1)
        extension = extension.lower()
    else:
        name_part = original_filename
        extension = ''

    # تنظيف اسم الملف (إزالة الأحرف الخطيرة)
    import re
    safe_name = re.sub(r'[^\w\s-]', '', name_part)
    safe_name = re.sub(r'[-\s]+', '_', safe_name)
    safe_name = safe_name.strip('_')

    # إذا كان الاسم فارغ بعد التنظيف، استخدم اسم افتراضي
    if not safe_name:
        safe_name = 'file'

    # إضافة timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # تجميع اسم الملف النهائي
    if extension:
        final_filename = f"{timestamp}_{safe_name}.{extension}"
    else:
        final_filename = f"{timestamp}_{safe_name}"

    return final_filename

def riyal_symbol():
    """رمز الريال السعودي القديم المألوف"""
    return '<span style="font-weight: bold; font-size: 1.1em;">﷼</span>'

# فلتر Jinja2 مخصص للتعامل مع القيم الفارغة
@app.template_filter('safe_upper')
def safe_upper(value):
    """تحويل النص إلى أحرف كبيرة بأمان"""
    if value:
        return str(value).upper()
    return 'ملف'

# إضافة دالة رمز الريال للـ templates
@app.template_global()
def riyal_svg():
    """إرجاع رمز الريال السعودي كـ SVG"""
    return riyal_symbol()

# دالة مساعدة للتحقق من الصلاحيات في templates
@app.template_global()
def user_has_permission(permission):
    """فحص صلاحية المستخدم الحالي - آمن للاستخدام في templates"""
    # تعطيل مؤقت - إرجاع True لجميع الصلاحيات
    return True
    # from flask_login import current_user
    # if not current_user.is_authenticated:
    #     return False
    # return current_user.has_permission(permission)

# current_user متاح تلقائياً مع flask-login

# دالة مؤقتة لتجاوز فحص تسجيل الدخول
def temp_login_bypass():
    """تجاوز مؤقت لفحص تسجيل الدخول"""
    pass

# استبدال login_required مؤقتاً
def temp_login_required(f):
    """استبدال مؤقت لـ login_required"""
    return f

# فلتر لاستبدال كلمة ريال بالرمز
@app.template_filter('replace_riyal')
def replace_riyal(text):
    """استبدال كلمة ريال بالرمز"""
    if text and 'ريال' in str(text):
        return str(text).replace('ريال', riyal_symbol())
    return text

# إضافة دالة navbar للـ templates
@app.template_global()
def get_navbar_brand_global():
    """إرجاع navbar brand للاستخدام في templates"""
    return get_navbar_brand()

db = SQLAlchemy(app)

# سيتم إنشاء الجداول في النهاية بعد تعريف جميع النماذج

# نظام النسخ الاحتياطي التلقائي
def auto_backup_database():
    """نسخ احتياطي تلقائي لقاعدة البيانات"""
    try:
        print("🔄 بدء النسخ الاحتياطي التلقائي...")

        # تصدير البيانات إلى JSON
        backup_data = {
            'timestamp': datetime.now().isoformat(),
            'tables': {}
        }

        # تصدير جدول المستخدمين
        users = User.query.all()
        backup_data['tables']['users'] = []
        for user in users:
            backup_data['tables']['users'].append({
                'id': user.id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'phone': user.phone,
                'role': user.role,
                'is_active': user.is_active,
                'password_hash': user.password_hash,
                'created_at': user.created_at.isoformat() if user.created_at else None
            })

        # تصدير جدول العملاء
        clients = Client.query.all()
        backup_data['tables']['clients'] = []
        for client in clients:
            backup_data['tables']['clients'].append({
                'id': client.id,
                'first_name': client.first_name,
                'last_name': client.last_name,
                'email': client.email,
                'phone': client.phone,
                'national_id': client.national_id,
                'address': client.address,
                'created_at': client.created_at.isoformat() if client.created_at else None
            })

        # تصدير جدول القضايا
        cases = Case.query.all()
        backup_data['tables']['cases'] = []
        for case in cases:
            backup_data['tables']['cases'].append({
                'id': case.id,
                'title': case.title,
                'description': case.description,
                'status': case.status,
                'client_id': case.client_id,
                'created_at': case.created_at.isoformat() if case.created_at else None
            })

        # تصدير جدول الفواتير
        invoices = Invoice.query.all()
        backup_data['tables']['invoices'] = []
        for invoice in invoices:
            backup_data['tables']['invoices'].append({
                'id': invoice.id,
                'invoice_number': invoice.invoice_number,
                'client_id': invoice.client_id,
                'case_id': invoice.case_id,
                'amount': float(invoice.amount) if invoice.amount else 0,
                'status': invoice.status,
                'created_at': invoice.created_at.isoformat() if invoice.created_at else None
            })

        # حفظ النسخة الاحتياطية
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'auto_backup_{timestamp}.json'

        with open(backup_filename, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)

        print(f"✅ تم إنشاء نسخة احتياطية: {backup_filename}")

        # حذف النسخ القديمة (الاحتفاظ بآخر 5 نسخ فقط)
        import glob
        backup_files = sorted(glob.glob('auto_backup_*.json'), reverse=True)
        for old_backup in backup_files[5:]:
            try:
                os.remove(old_backup)
                print(f"🗑️ تم حذف النسخة القديمة: {old_backup}")
            except:
                pass

    except Exception as e:
        print(f"❌ خطأ في النسخ الاحتياطي: {e}")

def start_backup_scheduler():
    """بدء جدولة النسخ الاحتياطي"""
    def backup_loop():
        while True:
            try:
                # نسخ احتياطي كل 5 دقائق
                time.sleep(5 * 60)  # 5 دقائق
                with app.app_context():
                    auto_backup_database()
            except Exception as e:
                print(f"❌ خطأ في جدولة النسخ الاحتياطي: {e}")
                time.sleep(60)  # انتظار دقيقة قبل المحاولة مرة أخرى

    # تشغيل النسخ الاحتياطي في thread منفصل
    backup_thread = threading.Thread(target=backup_loop, daemon=True)
    backup_thread.start()
    print("🤖 تم تفعيل النسخ الاحتياطي التلقائي (كل 6 ساعات)")

# تعطيل نظام تسجيل الدخول مؤقتاً
# login_manager = LoginManager()
# login_manager.init_app(app)
# login_manager.login_view = 'login'

# تعطيل مؤقت للـ Decorators
def permission_required(permission):
    """تعطيل مؤقت للتحقق من الصلاحيات"""
    def decorator(f):
        return f
    return decorator

def admin_required(f):
    """فحص صلاحية المدير - مفعل"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('يجب تسجيل الدخول أولاً', 'danger')
            return redirect(url_for('login'))

        if current_user.role != 'admin':
            flash('عذراً، هذه الصفحة متاحة للمدير فقط. ليس لديك صلاحية للوصول إليها.', 'danger')
            return redirect(url_for('index'))

        return f(*args, **kwargs)
    return decorated_function

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    password_hash = db.Column(db.String(128))
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    role = db.Column(db.String(20), default='lawyer', nullable=False)  # admin, lawyer, secretary
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def role_name(self):
        """إرجاع اسم الدور باللغة العربية"""
        roles = {
            'admin': 'مدير النظام',
            'lawyer': 'محامي',
            'secretary': 'سكرتير'
        }
        return roles.get(self.role, 'غير محدد')

    def has_permission(self, permission):
        """فحص صلاحية المستخدم"""
        permissions = {
            'admin': [
                'manage_users', 'manage_clients', 'manage_cases',
                'manage_appointments', 'manage_invoices', 'manage_documents',
                'view_reports', 'delete_data', 'system_settings'
            ],
            'lawyer': [
                'manage_clients', 'manage_cases', 'manage_appointments',
                'manage_invoices', 'manage_documents', 'view_reports'
            ],
            'secretary': [
                'view_clients', 'manage_appointments', 'view_cases',
                'manage_documents', 'view_invoices'
            ]
        }
        return permission in permissions.get(self.role, [])

    def is_admin(self):
        """فحص إذا كان المستخدم مدير"""
        return self.role == 'admin'

    def is_lawyer(self):
        """فحص إذا كان المستخدم محامي"""
        return self.role == 'lawyer'

    def is_secretary(self):
        """فحص إذا كان المستخدم سكرتير"""
        return self.role == 'secretary'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    national_id = db.Column(db.String(20))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

class ClientDocument(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    document_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200))
    filename = db.Column(db.String(255))  # اسم الملف المرفوع
    original_filename = db.Column(db.String(255))  # الاسم الأصلي للملف
    file_size = db.Column(db.Integer)  # حجم الملف بالبايت
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    case_id = db.Column(db.Integer, db.ForeignKey('case.id'))  # ربط المستند بقضية
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    client = db.relationship('Client', backref='client_documents')
    case = db.relationship('Case', backref='case_documents')

    @property
    def file_extension(self):
        if self.filename and '.' in self.filename:
            parts = self.filename.rsplit('.', 1)
            if len(parts) > 1:
                return parts[1].lower()
        return None

    @property
    def is_image(self):
        return self.file_extension and self.file_extension in ['png', 'jpg', 'jpeg', 'gif']

    @property
    def is_pdf(self):
        return self.file_extension and self.file_extension == 'pdf'

    @property
    def file_size_mb(self):
        if self.file_size:
            return round(self.file_size / (1024 * 1024), 2)
        return 0

    @property
    def is_word(self):
        return self.file_extension and self.file_extension in ['doc', 'docx']

    @property
    def is_excel(self):
        return self.file_extension and self.file_extension in ['xls', 'xlsx']

    @property
    def is_powerpoint(self):
        return self.file_extension and self.file_extension in ['ppt', 'pptx']

    @property
    def is_office_document(self):
        return self.is_word or self.is_excel or self.is_powerpoint

    @property
    def file_icon(self):
        if self.is_image:
            return "🖼️"
        elif self.is_pdf:
            return "📄"
        elif self.is_word:
            return "📝"
        elif self.is_excel:
            return "📊"
        elif self.is_powerpoint:
            return "📽️"
        else:
            return "📁"

    @property
    def can_preview(self):
        """هل يمكن معاينة الملف في المتصفح؟"""
        return self.is_image or self.is_pdf

class Case(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    case_number = db.Column(db.String(50), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    case_type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='active')
    description = db.Column(db.Text)
    court_name = db.Column(db.String(100))
    judge_name = db.Column(db.String(100))
    next_hearing_date = db.Column(db.DateTime)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    client = db.relationship('Client', backref='cases')

    @property
    def status_badge(self):
        status_colors = {
            'active': 'success',
            'closed': 'secondary',
            'pending': 'warning',
            'cancelled': 'danger'
        }
        return status_colors.get(self.status, 'primary')

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    appointment_date = db.Column(db.DateTime, nullable=False)
    duration_minutes = db.Column(db.Integer, default=60)
    location = db.Column(db.String(200))
    status = db.Column(db.String(20), default='scheduled')
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'))
    case_id = db.Column(db.Integer, db.ForeignKey('case.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    client = db.relationship('Client', backref='appointments')
    case = db.relationship('Case', backref='appointments')

    @property
    def status_badge(self):
        status_colors = {
            'scheduled': 'primary',
            'completed': 'success',
            'cancelled': 'danger',
            'rescheduled': 'warning'
        }
        return status_colors.get(self.status, 'secondary')

    @property
    def is_past(self):
        return self.appointment_date < datetime.now()

    @property
    def is_today(self):
        today = datetime.now().date()
        return self.appointment_date.date() == today

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    case_id = db.Column(db.Integer, db.ForeignKey('case.id'))
    issue_date = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime)
    description = db.Column(db.Text)
    amount = db.Column(db.Float, nullable=False)
    tax_amount = db.Column(db.Float, default=0)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, paid, overdue, cancelled
    payment_date = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    client = db.relationship('Client', backref='invoices')
    case = db.relationship('Case', backref='invoices')

    @property
    def status_badge(self):
        status_colors = {
            'pending': 'warning',
            'paid': 'success',
            'partial': 'info',
            'overdue': 'danger',
            'cancelled': 'secondary'
        }
        return status_colors.get(self.status, 'primary')

    @property
    def paid_amount(self):
        return sum(payment.amount for payment in self.payments)

    @property
    def remaining_amount(self):
        return self.total_amount - self.paid_amount

    @property
    def payment_percentage(self):
        if self.total_amount > 0:
            return (self.paid_amount / self.total_amount) * 100
        return 0

class InvoicePayment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    payment_method = db.Column(db.String(50), default='cash')  # cash, bank_transfer, check, card
    reference_number = db.Column(db.String(100))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    invoice = db.relationship('Invoice', backref='payments')

    @property
    def is_overdue(self):
        if self.status == 'paid' or not self.due_date:
            return False
        return datetime.now() > self.due_date

class OfficeSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    office_name = db.Column(db.String(200), nullable=False, default='مكتب المحاماة')
    office_name_en = db.Column(db.String(200), default='Law Office')
    address = db.Column(db.Text)
    city = db.Column(db.String(100))
    postal_code = db.Column(db.String(20))
    country = db.Column(db.String(100), default='المملكة العربية السعودية')

    # معلومات التسجيل
    commercial_register = db.Column(db.String(50))  # السجل التجاري
    tax_number = db.Column(db.String(50))  # الرقم الضريبي
    license_number = db.Column(db.String(50))  # رقم الترخيص

    # معلومات الاتصال
    phone_1 = db.Column(db.String(20))  # الهاتف الأساسي
    phone_2 = db.Column(db.String(20))  # هاتف إضافي
    fax = db.Column(db.String(20))  # الفاكس
    email = db.Column(db.String(120))  # البريد الإلكتروني
    website = db.Column(db.String(200))  # الموقع الإلكتروني

    # معلومات إضافية
    logo_path = db.Column(db.String(200))  # مسار الشعار
    established_year = db.Column(db.Integer)  # سنة التأسيس
    description = db.Column(db.Text)  # وصف المكتب

    # إعدادات النظام
    currency = db.Column(db.String(10), default='ريال')
    language = db.Column(db.String(10), default='ar')
    timezone = db.Column(db.String(50), default='Asia/Riyadh')

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @staticmethod
    def get_settings():
        """الحصول على إعدادات المكتب أو إنشاء إعدادات افتراضية"""
        settings = OfficeSettings.query.first()
        if not settings:
            settings = OfficeSettings(
                office_name='مكتب المحاماة',
                office_name_en='Law Office',
                country='المملكة العربية السعودية',
                currency='ريال',
                language='ar',
                timezone='Asia/Riyadh'
            )
            db.session.add(settings)
            db.session.commit()
        return settings

# جدول المصروفات
class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)  # عنوان المصروف
    description = db.Column(db.Text)  # وصف المصروف
    amount = db.Column(db.Float, nullable=False)  # المبلغ
    category = db.Column(db.String(100), nullable=False)  # فئة المصروف
    expense_date = db.Column(db.DateTime, nullable=False)  # تاريخ المصروف
    receipt_number = db.Column(db.String(100))  # رقم الإيصال
    vendor = db.Column(db.String(200))  # المورد/الجهة
    payment_method = db.Column(db.String(50), default='نقدي')  # طريقة الدفع
    notes = db.Column(db.Text)  # ملاحظات
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

    creator = db.relationship('User', backref='expenses')

def get_navbar_brand():
    """إنشاء عنصر navbar brand مع الشعار واسم المكتب"""
    settings = OfficeSettings.get_settings()

    if settings.logo_path:
        return f'''
        <a class="navbar-brand d-flex align-items-center" href="/">
            <img src="{url_for('simple_file', filename=settings.logo_path)}"
                 alt="شعار المكتب" style="height: 40px; margin-left: 10px;">
            <span>{settings.office_name}</span>
        </a>
        '''
    else:
        return f'''
        <a class="navbar-brand" href="/">
            <i class="fas fa-balance-scale me-2"></i>
            {settings.office_name}
        </a>
        '''

# تعطيل مؤقتاً
# @login_manager.user_loader
# def load_user(user_id):
#     return User.query.get(int(user_id))

@app.route('/simple_file/<path:filename>')
@app.route('/uploads/<path:filename>')
def simple_file(filename):
    """طريقة بسيطة لعرض الملفات - بدون تسجيل دخول للاختبار"""
    try:
        print(f"🔍 Simple file request: {filename}")

        # التحقق من صحة اسم الملف
        if not filename or filename.strip() == '':
            print("❌ Empty filename provided")
            return "اسم الملف فارغ", 400

        # إصلاح المشكلة: إزالة أي مسارات خاطئة تحتوي على client/
        if 'client/' in filename:
            print(f"⚠️ Detected 'client/' in filename: {filename}")
            # استخراج اسم الملف الصحيح قبل client/
            clean_filename = filename.split('client/')[0].rstrip('_')
            print(f"🧹 Cleaned filename: {clean_filename}")
            filename = clean_filename

        # فك ترميز اسم الملف إذا كان مُرمز
        import urllib.parse
        try:
            decoded_filename = urllib.parse.unquote(filename, encoding='utf-8')
            print(f"📝 Decoded filename: {decoded_filename}")
        except Exception as e:
            print(f"❌ Error decoding filename: {e}")
            decoded_filename = filename
            print(f"📝 Using original filename: {filename}")

        upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
        if not upload_folder:
            upload_folder = 'uploads'
        print(f"📁 Upload folder: {upload_folder}")

        # التأكد من أن المجلد موجود
        if not os.path.exists(upload_folder):
            print(f"❌ Upload folder does not exist: {upload_folder}")
            # محاولة إنشاء المجلد
            try:
                os.makedirs(upload_folder, exist_ok=True)
                print(f"✅ Created upload folder: {upload_folder}")
            except Exception as e:
                print(f"❌ Failed to create upload folder: {e}")
                return f"خطأ: لا يمكن الوصول لمجلد الملفات", 500

        # البحث باستخدام الاسم الأصلي والمُفكك
        search_names = [filename, decoded_filename]

        # إضافة البحث الذكي للملفات المشابهة (نفس النص، timestamps مختلفة)
        if '_' in decoded_filename:
            parts = decoded_filename.split('_', 2)  # تقسيم إلى تاريخ_وقت_اسم
            if len(parts) >= 3:
                name_part = parts[2]  # الجزء بعد التاريخ والوقت
                print(f"🔍 البحث عن ملفات تحتوي على: {name_part}")

                # البحث في جميع الملفات
                if os.path.exists(upload_folder):
                    try:
                        for file in os.listdir(upload_folder):
                            if name_part in file and os.path.isfile(os.path.join(upload_folder, file)):
                                if file not in search_names:
                                    search_names.append(file)
                                    print(f"✅ وجد ملف مشابه: {file}")
                    except Exception as e:
                        print(f"⚠️ خطأ في البحث عن الملفات المشابهة: {e}")

        # إضافة أشكال مختلفة من اسم الملف للبحث
        additional_names = []
        try:
            # محاولة ترميزات مختلفة
            import urllib.parse
            additional_names.append(urllib.parse.quote(filename, safe=''))
            additional_names.append(urllib.parse.quote(decoded_filename, safe=''))
            # إزالة المكررات
            search_names.extend([name for name in additional_names if name not in search_names])
        except Exception as e:
            print(f"⚠️ Error creating additional search names: {e}")

        print(f"🔍 Search names: {search_names}")
        file_path = None

        # قائمة المجلدات للبحث فيها
        search_folders = [
            upload_folder,  # المجلد الرئيسي
            os.path.join(upload_folder, 'documents'),  # مجلد المستندات
            os.path.join(upload_folder, 'logos'),  # مجلد الشعارات
        ]

        print(f"📁 Search folders: {search_folders}")

        for search_name in search_names:
            print(f"🔍 Searching for: {search_name}")

            # البحث في المجلدات المحددة أولاً
            for folder in search_folders:
                if os.path.exists(folder):
                    test_path = os.path.join(folder, search_name)
                    print(f"🔍 Checking: {test_path}")
                    if os.path.exists(test_path):
                        file_path = test_path
                        print(f"✅ Found at: {test_path}")
                        break
                else:
                    print(f"📁 Folder does not exist: {folder}")

            if file_path:
                break

            # إذا لم يوجد، ابحث في جميع المجلدات الفرعية
            print(f"🔍 Searching recursively in: {upload_folder}")
            try:
                for root, dirs, files in os.walk(upload_folder):
                    if search_name in files:
                        file_path = os.path.join(root, search_name)
                        print(f"✅ Found recursively at: {file_path}")
                        break
            except Exception as e:
                print(f"❌ Error during recursive search: {e}")

            if file_path:
                break

        if not file_path:
            print(f"❌ File not found: {filename}")
            print(f"📁 Upload folder contents:")
            try:
                for root, dirs, files in os.walk(upload_folder):
                    print(f"  📁 {root}: {files}")
            except Exception as e:
                print(f"❌ Error listing folder contents: {e}")
            return f"الملف غير موجود: {filename}", 404

        if file_path and os.path.exists(file_path):
            print(f"✅ File found and exists: {file_path}")
            filename_lower = filename.lower()

            # للملفات التي لا يمكن عرضها في المتصفح، أعرض صفحة تحذيرية
            if filename_lower.endswith(('.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx')):
                return f'''
                <!DOCTYPE html>
                <html lang="ar" dir="rtl">
                <head>
                    <meta charset="utf-8">
                    <title>معاينة المستند</title>
                    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
                    <style>
                        .file-icon {{ font-size: 4em; margin-bottom: 20px; }}
                        .download-btn {{ font-size: 1.2em; padding: 15px 30px; }}
                    </style>
                </head>
                <body class="bg-light">
                    <div class="container mt-5">
                        <div class="row justify-content-center">
                            <div class="col-md-6">
                                <div class="card shadow">
                                    <div class="card-body text-center">
                                        <div class="file-icon">
                                            {'📝' if filename_lower.endswith(('.doc', '.docx')) else
                                             '📊' if filename_lower.endswith(('.xls', '.xlsx')) else '📽️'}
                                        </div>
                                        <h4 class="card-title">لا يمكن معاينة هذا الملف</h4>
                                        <p class="card-text text-muted">
                                            هذا النوع من الملفات يحتاج إلى برنامج خاص لفتحه.<br>
                                            يمكنك تحميل الملف وفتحه على جهازك.
                                        </p>
                                        <div class="mb-3">
                                            <strong>اسم الملف:</strong> {filename}<br>
                                            <strong>النوع:</strong> {'مستند Word' if filename_lower.endswith(('.doc', '.docx')) else
                                                                    'جدول Excel' if filename_lower.endswith(('.xls', '.xlsx')) else 'عرض PowerPoint'}
                                        </div>
                                        <a href="/download_file/{filename}" class="btn btn-primary download-btn">
                                            📥 تحميل الملف الآن
                                        </a>
                                        <br><br>
                                        <button onclick="window.close()" class="btn btn-secondary">إغلاق النافذة</button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </body>
                </html>
                '''

            # للملفات القابلة للعرض (صور، PDF)
            from flask import Response
            with open(file_path, 'rb') as f:
                file_data = f.read()

            # تحديد نوع الملف بناءً على اسم الملف أو محتواه

            # التحقق من امتداد الملف أولاً
            if filename_lower.endswith('.pdf') or 'pdf' in filename_lower:
                mimetype = 'application/pdf'
                disposition = 'inline'
            elif filename_lower.endswith(('.jpg', '.jpeg')) or 'jpg' in filename_lower or 'jpeg' in filename_lower:
                mimetype = 'image/jpeg'
                disposition = 'inline'
            elif filename_lower.endswith('.png') or 'png' in filename_lower:
                mimetype = 'image/png'
                disposition = 'inline'
            elif filename_lower.endswith('.gif') or 'gif' in filename_lower:
                mimetype = 'image/gif'
                disposition = 'inline'
            elif filename_lower.endswith('.docx'):
                # ملفات Word الحديثة - محاولة العرض أولاً، ثم التحميل
                mimetype = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                disposition = 'inline'  # محاولة العرض أولاً
            elif filename_lower.endswith('.doc'):
                # ملفات Word القديمة - محاولة العرض أولاً، ثم التحميل
                mimetype = 'application/msword'
                disposition = 'inline'  # محاولة العرض أولاً
            elif filename_lower.endswith('.xlsx'):
                # ملفات Excel الحديثة
                mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                disposition = 'attachment'
            elif filename_lower.endswith('.xls'):
                # ملفات Excel القديمة
                mimetype = 'application/vnd.ms-excel'
                disposition = 'attachment'
            elif filename_lower.endswith('.pptx'):
                # ملفات PowerPoint الحديثة
                mimetype = 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
                disposition = 'attachment'
            elif filename_lower.endswith('.ppt'):
                # ملفات PowerPoint القديمة
                mimetype = 'application/vnd.ms-powerpoint'
                disposition = 'attachment'
            else:
                # محاولة تخمين نوع الملف من المحتوى
                if file_data.startswith(b'%PDF'):
                    mimetype = 'application/pdf'
                    disposition = 'inline'
                elif file_data.startswith(b'\xff\xd8\xff'):  # JPEG
                    mimetype = 'image/jpeg'
                    disposition = 'inline'
                elif file_data.startswith(b'\x89PNG'):  # PNG
                    mimetype = 'image/png'
                    disposition = 'inline'
                else:
                    mimetype = 'application/octet-stream'
                    disposition = 'attachment'

            response = Response(file_data, mimetype=mimetype)

            # إضافة headers لضمان العرض الصحيح
            if disposition == 'inline':
                response.headers['Content-Disposition'] = f'inline; filename="{filename}"'
                response.headers['Cache-Control'] = 'no-cache'
                response.headers['X-Content-Type-Options'] = 'nosniff'
            else:
                response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'

            return response
        else:
            # الملف غير موجود أو file_path هو None
            print(f"❌ File not found or file_path is None")
            print(f"📝 file_path value: {file_path}")
            print(f"📝 filename: {filename}")
            print(f"📝 decoded_filename: {decoded_filename}")

            # إرجاع قائمة بالملفات الموجودة للمساعدة في التشخيص
            available_files = []
            try:
                for root, dirs, files in os.walk(upload_folder):
                    for file in files:
                        rel_path = os.path.relpath(os.path.join(root, file), upload_folder)
                        available_files.append(rel_path)
            except Exception as e:
                print(f"❌ Error listing files: {e}")
                available_files = ["خطأ في قراءة الملفات"]

            print(f"❌ File not found: {filename}")
            print(f"📁 Available files: {available_files[:10]}")  # أول 10 ملفات فقط

            return f"""
            <html dir="rtl">
            <head><title>ملف غير موجود</title></head>
            <body style="font-family: Arial; padding: 20px;">
                <h3>❌ الملف غير موجود: {filename}</h3>
                <p><strong>الاسم المُفكك:</strong> {decoded_filename}</p>
                <p><strong>مجلد البحث:</strong> {upload_folder}</p>
                <h4>الملفات المتاحة (أول 20):</h4>
                <ul>
                {''.join([f'<li>{f}</li>' for f in available_files[:20]])}
                </ul>
                <a href="javascript:history.back()">العودة</a>
            </body>
            </html>
            """, 404

    except Exception as e:
        print(f"❌ Error in simple_file: {str(e)}")
        print(f"📝 Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()

        # محاولة الحصول على معلومات إضافية
        try:
            upload_folder_info = app.config.get('UPLOAD_FOLDER', 'غير محدد')
            upload_exists = os.path.exists(upload_folder_info) if upload_folder_info else False
        except:
            upload_folder_info = "خطأ في القراءة"
            upload_exists = False

        return f"""
        <html dir="rtl">
        <head><title>خطأ في الملف</title></head>
        <body style="font-family: Arial; padding: 20px;">
            <h3>❌ خطأ في عرض الملف</h3>
            <p><strong>اسم الملف:</strong> {filename if 'filename' in locals() else 'غير محدد'}</p>
            <p><strong>مجلد الرفع:</strong> {upload_folder_info}</p>
            <p><strong>المجلد موجود:</strong> {upload_exists}</p>
            <p><strong>نوع الخطأ:</strong> {type(e).__name__}</p>
            <p><strong>تفاصيل الخطأ:</strong> {str(e)}</p>
            <a href="javascript:history.back()">العودة</a>
        </body>
        </html>
        """, 500

@app.route('/documents/<int:document_id>/download')
def documents_download(document_id):
    """تحميل المستند بواسطة ID - نسخة محسنة"""
    try:
        document = ClientDocument.query.get_or_404(document_id)
        upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')

        # البحث عن الملف في عدة مواقع
        possible_paths = [
            os.path.join(upload_folder, document.filename),
            os.path.join(upload_folder, 'documents', document.filename),
        ]

        file_path = None
        for path in possible_paths:
            if os.path.exists(path):
                file_path = path
                break

        if not file_path:
            # إنشاء ملف بديل إذا لم يوجد الملف الأصلي
            error_content = f"""
            <html dir="rtl">
            <head><title>ملف غير موجود</title></head>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h2>⚠️ الملف غير موجود</h2>
                <p>اسم الملف: {document.filename}</p>
                <p>الوصف: {document.description}</p>
                <p>يرجى رفع الملف مرة أخرى</p>
                <a href="/clients/{document.client_id}">العودة لصفحة العميل</a>
            </body>
            </html>
            """
            return error_content, 404

        # استخدام send_file مع mimetype صحيح
        from flask import send_file
        import mimetypes

        # تحديد نوع الملف
        mimetype, _ = mimetypes.guess_type(file_path)
        if mimetype is None:
            mimetype = 'application/octet-stream'

        # استخدام الاسم الأصلي للملف
        download_name = document.original_filename or f"document_{document_id}"

        return send_file(
            file_path,
            as_attachment=True,
            download_name=download_name,
            mimetype=mimetype
        )

    except Exception as e:
        error_content = f"""
        <html dir="rtl">
        <head><title>خطأ في التحميل</title></head>
        <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h2>❌ خطأ في تحميل الملف</h2>
            <p>تفاصيل الخطأ: {str(e)}</p>
            <a href="javascript:history.back()">العودة</a>
        </body>
        </html>
        """
        return error_content, 500

@app.route('/download_file/<filename>')
def download_file(filename):
    """تحميل الملف مع إجبار التحميل - نسخة مبسطة"""
    try:
        upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')

        # البحث عن الملف
        file_path = os.path.join(upload_folder, filename)
        if not os.path.exists(file_path):
            file_path = os.path.join(upload_folder, 'documents', filename)

        if not os.path.exists(file_path):
            return f"<h3>File not found: {filename}</h3>", 404

        # البحث عن المستند في قاعدة البيانات للحصول على الاسم الأصلي
        document = ClientDocument.query.filter_by(filename=filename).first()

        # استخدام send_file مع mimetype صحيح
        from flask import send_file
        import mimetypes

        # تحديد نوع الملف
        mimetype, _ = mimetypes.guess_type(file_path)
        if mimetype is None:
            mimetype = 'application/octet-stream'

        # استخدام الاسم الأصلي إذا كان متوفراً
        if document and document.original_filename:
            download_name = document.original_filename
        else:
            # الحصول على امتداد الملف الأصلي
            original_ext = filename.split('.')[-1] if '.' in filename else 'file'
            download_name = f"document.{original_ext}"

        return send_file(
            file_path,
            as_attachment=True,
            download_name=download_name,
            mimetype=mimetype
        )

    except Exception as e:
        return f"<h3>Error: {str(e)}</h3>", 500



@app.route('/test_file')
def test_file():
    """اختبار سريع لعرض ملف"""
    try:
        upload_folder = app.config['UPLOAD_FOLDER']

        # البحث عن أي ملف في مجلد uploads
        test_files = []
        for root, dirs, files in os.walk(upload_folder):
            for file in files:
                if file.lower().endswith(('.pdf', '.jpg', '.jpeg', '.png')):
                    rel_path = os.path.relpath(os.path.join(root, file), upload_folder)
                    test_files.append({
                        'name': file,
                        'path': rel_path,
                        'full_path': os.path.join(root, file)
                    })

        html = """
        <h2>اختبار الملفات</h2>
        <table border="1" style="border-collapse: collapse; width: 100%;">
            <tr>
                <th>اسم الملف</th>
                <th>المسار النسبي</th>
                <th>رابط الاختبار</th>
            </tr>
        """

        for file_info in test_files:
            html += f"""
            <tr>
                <td>{file_info['name']}</td>
                <td>{file_info['path']}</td>
                <td><a href="/simple_file/{file_info['path']}" target="_blank">عرض</a></td>
            </tr>
            """

        html += "</table>"
        return html

    except Exception as e:
        return f"خطأ: {str(e)}"

@app.route('/debug_documents')
@login_required
def debug_documents():
    """صفحة لفحص المستندات في قاعدة البيانات"""
    documents = ClientDocument.query.all()
    debug_info = []

    for doc in documents:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], doc.filename) if doc.filename else None
        file_exists = os.path.exists(file_path) if file_path else False

        debug_info.append({
            'id': doc.id,
            'filename': doc.filename,
            'original_filename': doc.original_filename,
            'file_path': file_path,
            'file_exists': file_exists,
            'client': doc.client.full_name if doc.client else 'غير محدد'
        })

    return render_template_string('''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>فحص المستندات</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-5">
        <h1>فحص المستندات</h1>
        <table class="table table-striped">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>اسم الملف</th>
                    <th>الاسم الأصلي</th>
                    <th>المسار</th>
                    <th>موجود؟</th>
                    <th>العميل</th>
                    <th>رابط الاختبار</th>
                </tr>
            </thead>
            <tbody>
                {% for doc in debug_info %}
                <tr>
                    <td>{{ doc.id }}</td>
                    <td>{{ doc.filename or 'لا يوجد' }}</td>
                    <td>{{ doc.original_filename or 'لا يوجد' }}</td>
                    <td>{{ doc.file_path or 'لا يوجد' }}</td>
                    <td>
                        {% if doc.file_exists %}
                            <span class="badge bg-success">موجود</span>
                        {% else %}
                            <span class="badge bg-danger">غير موجود</span>
                        {% endif %}
                    </td>
                    <td>{{ doc.client }}</td>
                    <td>
                        {% if doc.filename %}
                            <button onclick="window.open('{{ url_for('simple_file', filename=doc.filename) }}', '_blank')" class="btn btn-sm btn-primary">اختبار</button>
                        {% endif %}
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        <a href="/" class="btn btn-secondary">العودة للرئيسية</a>
    </div>
</body>
</html>
    ''', debug_info=debug_info)

@app.route('/view_document/<int:doc_id>')
@login_required
def view_document(doc_id):
    """عرض مستند محدد"""
    try:
        doc = ClientDocument.query.get_or_404(doc_id)

        if not doc.filename:
            return f'''
            <html dir="rtl">
            <head><title>خطأ</title></head>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h2>❌ لا يوجد ملف مرفق لهذا المستند</h2>
            <a href="javascript:history.back()">العودة</a>
            </body>
            </html>
            '''

        # البحث عن الملف في جميع المجلدات
        upload_folder = app.config['UPLOAD_FOLDER']
        file_path = None

        # البحث في المجلد الرئيسي أولاً
        main_path = os.path.join(upload_folder, doc.filename)
        if os.path.exists(main_path):
            file_path = main_path
        else:
            # البحث في جميع المجلدات الفرعية
            for root, dirs, files in os.walk(upload_folder):
                if doc.filename in files:
                    file_path = os.path.join(root, doc.filename)
                    break

        if not file_path:
            return f'''
            <html dir="rtl">
            <head><title>خطأ</title></head>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h2>❌ الملف غير موجود: {doc.filename}</h2>
            <p>اسم الملف الأصلي: {doc.original_filename}</p>
            <a href="javascript:history.back()">العودة</a>
            </body>
            </html>
            '''

        # قراءة الملف وإرجاعه
        from flask import Response
        with open(file_path, 'rb') as f:
            file_data = f.read()

        # تحديد نوع الملف
        filename_lower = doc.filename.lower()
        if filename_lower.endswith('.pdf'):
            mimetype = 'application/pdf'
        elif filename_lower.endswith(('.jpg', '.jpeg')):
            mimetype = 'image/jpeg'
        elif filename_lower.endswith('.png'):
            mimetype = 'image/png'
        elif filename_lower.endswith('.gif'):
            mimetype = 'image/gif'
        elif filename_lower.endswith(('.doc', '.docx')):
            mimetype = 'application/msword'
        else:
            mimetype = 'application/octet-stream'

        response = Response(file_data, mimetype=mimetype)
        response.headers['Content-Disposition'] = f'inline; filename="{doc.original_filename}"'
        return response

    except Exception as e:
        return f'''
        <html dir="rtl">
        <head><title>خطأ</title></head>
        <body style="font-family: Arial; text-align: center; padding: 50px;">
        <h2>❌ خطأ في عرض المستند</h2>
        <p>{str(e)}</p>
        <a href="javascript:history.back()">العودة</a>
        </body>
        </html>
        '''

@app.route('/debug_document/<int:doc_id>')
@login_required
def debug_document(doc_id):
    """صفحة تشخيص المستند"""
    try:
        doc = ClientDocument.query.get_or_404(doc_id)

        debug_info = {
            'document_id': doc.id,
            'filename': doc.filename,
            'original_filename': doc.original_filename,
            'document_type': doc.document_type,
            'file_size': doc.file_size,
            'client_name': doc.client.full_name if doc.client else 'غير محدد'
        }

        # التحقق من وجود الملف
        if doc.filename:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], doc.filename)
            debug_info['file_path'] = file_path
            debug_info['file_exists'] = os.path.exists(file_path)

            # البحث في مجلدات أخرى
            upload_folder = app.config['UPLOAD_FOLDER']
            found_files = []
            for root, dirs, files in os.walk(upload_folder):
                if doc.filename in files:
                    found_files.append(os.path.join(root, doc.filename))
            debug_info['found_files'] = found_files

        return f'''
        <html dir="rtl">
        <head><title>تشخيص المستند</title></head>
        <body style="font-family: Arial;">
        <h2>تشخيص المستند #{doc_id}</h2>
        <table border="1" style="border-collapse: collapse; width: 100%;">
        <tr><td><b>معرف المستند</b></td><td>{debug_info.get('document_id', 'غير محدد')}</td></tr>
        <tr><td><b>اسم الملف</b></td><td>{debug_info.get('filename', 'غير محدد')}</td></tr>
        <tr><td><b>الاسم الأصلي</b></td><td>{debug_info.get('original_filename', 'غير محدد')}</td></tr>
        <tr><td><b>نوع المستند</b></td><td>{debug_info.get('document_type', 'غير محدد')}</td></tr>
        <tr><td><b>حجم الملف</b></td><td>{debug_info.get('file_size', 'غير محدد')}</td></tr>
        <tr><td><b>العميل</b></td><td>{debug_info.get('client_name', 'غير محدد')}</td></tr>
        <tr><td><b>مسار الملف</b></td><td>{debug_info.get('file_path', 'غير محدد')}</td></tr>
        <tr><td><b>الملف موجود؟</b></td><td>{'نعم' if debug_info.get('file_exists') else 'لا'}</td></tr>
        <tr><td><b>ملفات موجودة</b></td><td>{', '.join(debug_info.get('found_files', []))}</td></tr>
        </table>
        <br>
        <a href="/view_document/{doc_id}">جرب عرض المستند</a> |
        <a href="/simple_file/{doc.filename}">رابط مباشر للملف</a> |
        <a href="javascript:history.back()">العودة</a>
        </body>
        </html>
        '''

    except Exception as e:
        return f'خطأ: {str(e)}'

@app.route('/debug_files')
def debug_files():
    """صفحة تشخيص الملفات"""
    try:
        upload_folder = app.config['UPLOAD_FOLDER']

        # الحصول على الملفات الموجودة فعلياً
        actual_files = []
        if os.path.exists(upload_folder):
            for file in os.listdir(upload_folder):
                file_path = os.path.join(upload_folder, file)
                if os.path.isfile(file_path):
                    size = os.path.getsize(file_path)
                    actual_files.append({
                        'name': file,
                        'size': size,
                        'path': file_path
                    })

        # الحصول على المستندات من قاعدة البيانات
        db_documents = ClientDocument.query.all()

        debug_info = []
        for doc in db_documents:
            if doc.filename:
                file_path = os.path.join(upload_folder, doc.filename)
                exists = os.path.exists(file_path)

                debug_info.append({
                    'id': doc.id,
                    'filename': doc.filename,
                    'original_filename': doc.original_filename,
                    'exists': exists,
                    'path': file_path,
                    'client_name': doc.client.full_name if doc.client else 'غير محدد'
                })

        return f'''
        <!DOCTYPE html>
        <html dir="rtl">
        <head>
            <title>تشخيص الملفات</title>
            <meta charset="utf-8">
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container mt-4">
                <h1>🔍 تشخيص الملفات</h1>

                <div class="row">
                    <div class="col-md-6">
                        <h3>📁 الملفات الموجودة فعلياً ({len(actual_files)})</h3>
                        <div class="table-responsive">
                            <table class="table table-striped">
                                <thead>
                                    <tr>
                                        <th>اسم الملف</th>
                                        <th>الحجم</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {"".join([f"<tr><td>{file['name']}</td><td>{file['size']} bytes</td></tr>" for file in actual_files])}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <div class="col-md-6">
                        <h3>📊 المستندات في قاعدة البيانات ({len(debug_info)})</h3>
                        <div class="table-responsive">
                            <table class="table table-striped">
                                <thead>
                                    <tr>
                                        <th>ID</th>
                                        <th>اسم الملف</th>
                                        <th>الحالة</th>
                                        <th>العميل</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {"".join([f"<tr><td>{doc['id']}</td><td>{doc['filename']}</td><td>{'✅' if doc['exists'] else '❌'}</td><td>{doc['client_name']}</td></tr>" for doc in debug_info])}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                <div class="mt-4">
                    <h3>⚠️ الملفات المفقودة</h3>
                    <ul class="list-group">
                        {"".join([f"<li class='list-group-item list-group-item-danger'>ID: {doc['id']} - {doc['filename']} (العميل: {doc['client_name']})</li>" for doc in debug_info if not doc['exists']])}
                    </ul>
                </div>

                <div class="mt-4">
                    <a href="/" class="btn btn-primary">العودة للرئيسية</a>
                </div>
            </div>
        </body>
        </html>
        '''

    except Exception as e:
        return f"خطأ في التشخيص: {str(e)}"

@app.route('/test_download_direct/<int:doc_id>')
def test_download_direct(doc_id):
    """اختبار تحميل مباشر للمستند"""
    try:
        document = ClientDocument.query.get_or_404(doc_id)
        upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')

        # المسار الكامل للملف
        file_path = os.path.join(upload_folder, document.filename)

        # معلومات تشخيصية
        debug_info = {
            'doc_id': doc_id,
            'filename': document.filename,
            'original_filename': document.original_filename,
            'upload_folder': upload_folder,
            'file_path': file_path,
            'file_exists': os.path.exists(file_path),
            'current_dir': os.getcwd(),
            'absolute_path': os.path.abspath(file_path)
        }

        if os.path.exists(file_path):
            # الملف موجود - اختبارات إضافية
            try:
                # اختبار قراءة الملف
                with open(file_path, 'rb') as f:
                    file_size = len(f.read())

                # اختبار الأذونات
                readable = os.access(file_path, os.R_OK)

                # معلومات إضافية
                import stat
                file_stat = os.stat(file_path)

                additional_info = {
                    'file_size_actual': file_size,
                    'file_size_stat': file_stat.st_size,
                    'readable': readable,
                    'file_mode': oct(file_stat.st_mode),
                    'is_file': os.path.isfile(file_path),
                    'is_link': os.path.islink(file_path)
                }

                debug_info.update(additional_info)

                # محاولة التحميل
                from flask import send_file
                return send_file(file_path, as_attachment=True,
                               download_name=f"test_{document.original_filename}")

            except Exception as download_error:
                return f'''
                <h3>خطأ في التحميل</h3>
                <p>خطأ التحميل: {str(download_error)}</p>
                <h4>معلومات تشخيصية مفصلة:</h4>
                <pre>{debug_info}</pre>

                <h4>اختبار بديل - قراءة مباشرة:</h4>
                <p>محاولة قراءة الملف مباشرة...</p>
                '''
        else:
            # الملف غير موجود - عرض معلومات تشخيصية
            return f'''
            <h3>الملف غير موجود</h3>
            <h4>معلومات تشخيصية:</h4>
            <ul>
                <li><strong>معرف المستند:</strong> {debug_info['doc_id']}</li>
                <li><strong>اسم الملف:</strong> {debug_info['filename']}</li>
                <li><strong>الاسم الأصلي:</strong> {debug_info['original_filename']}</li>
                <li><strong>مجلد الرفع:</strong> {debug_info['upload_folder']}</li>
                <li><strong>المسار النسبي:</strong> {debug_info['file_path']}</li>
                <li><strong>المسار المطلق:</strong> {debug_info['absolute_path']}</li>
                <li><strong>المجلد الحالي:</strong> {debug_info['current_dir']}</li>
                <li><strong>الملف موجود:</strong> {debug_info['file_exists']}</li>
            </ul>

            <h4>الملفات الموجودة في مجلد uploads:</h4>
            <ul>
                {"".join([f"<li>{f}</li>" for f in os.listdir(upload_folder) if os.path.isfile(os.path.join(upload_folder, f))])}
            </ul>

            <a href="/debug_files">العودة لصفحة التشخيص</a>
            '''

    except Exception as e:
        return f"خطأ عام: {str(e)}"

@app.route('/download_alternative/<int:doc_id>')
def download_alternative(doc_id):
    """طريقة بديلة للتحميل"""
    try:
        document = ClientDocument.query.get_or_404(doc_id)
        upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
        file_path = os.path.join(upload_folder, document.filename)

        if not os.path.exists(file_path):
            return f"الملف غير موجود: {file_path}"

        # قراءة الملف مباشرة
        with open(file_path, 'rb') as f:
            file_data = f.read()

        # تحديد نوع الملف
        import mimetypes
        mimetype, _ = mimetypes.guess_type(file_path)
        if mimetype is None:
            mimetype = 'application/octet-stream'

        # إنشاء response مخصص
        from flask import Response
        response = Response(file_data, mimetype=mimetype)
        response.headers['Content-Disposition'] = f'attachment; filename="{document.original_filename}"'
        response.headers['Content-Length'] = len(file_data)

        return response

    except Exception as e:
        return f"خطأ في التحميل البديل: {str(e)}"

@app.route('/check_latest_files')
def check_latest_files():
    """فحص آخر الملفات المرفوعة"""
    try:
        # الحصول على آخر 5 مستندات
        latest_docs = ClientDocument.query.order_by(ClientDocument.id.desc()).limit(5).all()

        upload_folder = app.config['UPLOAD_FOLDER']

        results = []
        for doc in latest_docs:
            if doc.filename:
                file_path = os.path.join(upload_folder, doc.filename)

                file_info = {
                    'id': doc.id,
                    'filename': doc.filename,
                    'original_filename': doc.original_filename,
                    'client_name': doc.client.full_name if doc.client else 'غير محدد',
                    'file_exists': os.path.exists(file_path),
                    'file_path': file_path
                }

                if os.path.exists(file_path):
                    file_info['file_size'] = os.path.getsize(file_path)

                    # قراءة أول 100 بايت للتحقق من محتوى الملف
                    try:
                        with open(file_path, 'rb') as f:
                            first_bytes = f.read(100)
                            file_info['first_bytes_hex'] = first_bytes.hex()[:50]  # أول 25 بايت بصيغة hex
                            file_info['is_empty'] = len(first_bytes) == 0
                    except Exception as e:
                        file_info['read_error'] = str(e)
                else:
                    file_info['file_size'] = 0

                results.append(file_info)

        html = '''
        <!DOCTYPE html>
        <html dir="rtl">
        <head>
            <title>فحص آخر الملفات</title>
            <meta charset="utf-8">
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container mt-4">
                <h1>🔍 فحص آخر الملفات المرفوعة</h1>

                <div class="table-responsive">
                    <table class="table table-striped">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>اسم الملف</th>
                                <th>العميل</th>
                                <th>الحجم</th>
                                <th>موجود</th>
                                <th>أول البيانات</th>
                                <th>اختبار</th>
                            </tr>
                        </thead>
                        <tbody>
        '''

        for file_info in results:
            status_color = 'success' if file_info['file_exists'] else 'danger'
            size_text = f"{file_info.get('file_size', 0)} bytes"
            first_bytes = file_info.get('first_bytes_hex', 'N/A')

            html += f'''
            <tr class="table-{status_color}">
                <td>{file_info['id']}</td>
                <td>{file_info['filename']}</td>
                <td>{file_info['client_name']}</td>
                <td>{size_text}</td>
                <td>{'✅' if file_info['file_exists'] else '❌'}</td>
                <td><code>{first_bytes}</code></td>
                <td>
                    <a href="/test_download_direct/{file_info['id']}" class="btn btn-sm btn-primary">اختبار</a>
                    <a href="/download_alternative/{file_info['id']}" class="btn btn-sm btn-success">تحميل</a>
                </td>
            </tr>
            '''

        html += '''
                        </tbody>
                    </table>
                </div>

                <div class="mt-4">
                    <a href="/" class="btn btn-primary">العودة للرئيسية</a>
                    <a href="/debug_files" class="btn btn-secondary">صفحة التشخيص</a>
                </div>
            </div>
        </body>
        </html>
        '''

        return html

    except Exception as e:
        return f"خطأ في فحص الملفات: {str(e)}"

@app.route('/test_files')
@login_required
def test_files():
    """صفحة اختبار الملفات"""
    upload_folder = app.config['UPLOAD_FOLDER']

    # البحث عن جميع الملفات
    all_files = []
    for root, dirs, files in os.walk(upload_folder):
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, upload_folder)
            all_files.append({
                'name': file,
                'path': rel_path,
                'full_path': file_path,
                'size': os.path.getsize(file_path) if os.path.exists(file_path) else 0
            })

    html = '''
    <html dir="rtl">
    <head>
        <title>اختبار الملفات</title>
        <style>
            body { font-family: Arial; margin: 20px; }
            table { border-collapse: collapse; width: 100%; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: right; }
            th { background-color: #f2f2f2; }
            .btn { padding: 5px 10px; margin: 2px; text-decoration: none; border-radius: 3px; }
            .btn-primary { background: #007bff; color: white; }
            .btn-success { background: #28a745; color: white; }
        </style>
    </head>
    <body>
        <h2>🔍 اختبار الملفات المرفوعة</h2>
        <p>مجلد الرفع: ''' + upload_folder + '''</p>
        <table>
            <tr>
                <th>اسم الملف</th>
                <th>المسار النسبي</th>
                <th>الحجم</th>
                <th>اختبار العرض</th>
            </tr>
    '''

    for file_info in all_files:
        html += f'''
        <tr>
            <td>{file_info['name']}</td>
            <td>{file_info['path']}</td>
            <td>{file_info['size']} بايت</td>
            <td>
                <a href="/simple_file/{file_info['path']}" target="_blank" class="btn btn-primary">عرض</a>
                <a href="/simple_file/{file_info['path']}" download class="btn btn-success">تحميل</a>
            </td>
        </tr>
        '''

    html += '''
        </table>
        <br>
        <a href="/">العودة للرئيسية</a>
    </body>
    </html>
    '''

    return html

@app.route('/debug_view')
def debug_view():
    """صفحة تشخيص مشاكل العرض"""
    return '''
    <html dir="rtl">
    <head>
        <title>تشخيص مشاكل العرض</title>
        <style>
            body { font-family: Arial; margin: 20px; }
            .test-btn { padding: 10px; margin: 10px; display: block; width: 300px; }
        </style>
    </head>
    <body>
        <h2>🔍 تشخيص مشاكل عرض الملفات</h2>

        <h3>اختبار 1: رابط مباشر (صورة)</h3>
        <a href="/simple_file/20250715_214725_Scan.jpg" target="_blank" class="test-btn" style="background: #007bff; color: white; text-decoration: none;">
            رابط مباشر - نافذة جديدة
        </a>

        <h3>اختبار 2: JavaScript (صورة)</h3>
        <button onclick="window.open('/simple_file/20250715_214725_Scan.jpg', '_blank')" class="test-btn" style="background: #28a745; color: white;">
            JavaScript - نافذة جديدة
        </button>

        <h3>اختبار 3: نفس النافذة (صورة)</h3>
        <a href="/simple_file/20250715_214725_Scan.jpg" class="test-btn" style="background: #ffc107; color: black; text-decoration: none;">
            نفس النافذة
        </a>

        <h3>اختبار 4: تحميل فعلي (صورة)</h3>
        <a href="/download_file/20250715_214725_Scan.jpg" class="test-btn" style="background: #dc3545; color: white; text-decoration: none;">
            تحميل الملف
        </a>

        <h3>اختبار 5: ملف PDF</h3>
        <button onclick="window.open('/simple_file/20250715_214725_lphlhi2.pdf', '_blank')" class="test-btn" style="background: #6f42c1; color: white;">
            فتح PDF
        </button>

        <hr>
        <h3>معلومات المتصفح:</h3>
        <script>
            document.write('<p>User Agent: ' + navigator.userAgent + '</p>');
            document.write('<p>Platform: ' + navigator.platform + '</p>');
        </script>

        <br>
        <a href="/">العودة للرئيسية</a>
    </body>
    </html>
    '''

@app.route('/test_file_issue')
def test_file_issue():
    """اختبار مشكلة الملفات"""
    try:
        # البحث عن أول مستند
        document = ClientDocument.query.first()
        if not document:
            return "لا توجد مستندات للاختبار"

        # إنشاء رابط الاختبار
        test_url = url_for('simple_file', filename=document.filename)

        return f"""
        <html dir="rtl">
        <head><title>اختبار الملفات</title></head>
        <body style="font-family: Arial; padding: 20px;">
            <h2>اختبار مشكلة الملفات</h2>
            <p><strong>اسم الملف:</strong> {document.filename}</p>
            <p><strong>الرابط المُنشأ:</strong> {test_url}</p>
            <p><strong>اختبار الرابط:</strong> <a href="{test_url}" target="_blank">انقر هنا</a></p>
            <hr>
            <h3>معلومات إضافية:</h3>
            <p><strong>ID المستند:</strong> {document.id}</p>
            <p><strong>ID العميل:</strong> {document.client_id}</p>
            <p><strong>الاسم الأصلي:</strong> {document.original_filename}</p>
        </body>
        </html>
        """
    except Exception as e:
        return f"خطأ: {str(e)}"

@app.route('/login', methods=['GET', 'POST'])
def login():
    """صفحة تسجيل الدخول"""
    if current_user.is_authenticated:
        return redirect('/')

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash('يرجى إدخال اسم المستخدم وكلمة المرور', 'danger')
        else:
            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                login_user(user, remember=request.form.get('remember_me'))
                next_page = request.args.get('next')
                if not next_page or not next_page.startswith('/'):
                    next_page = '/'
                return redirect(next_page)
            else:
                flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'danger')

    return render_template_string('''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="utf-8">
    <title>تسجيل الدخول - {{ office_settings.office_name }}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
        }
        .login-card {
            background: white;
            border-radius: 15px;
            box-shadow: 0 15px 35px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .login-header {
            background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .login-body {
            padding: 40px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="row justify-content-center">
            <div class="col-md-6 col-lg-4">
                <div class="login-card">
                    <div class="login-header">
                        {% if office_settings.logo_path %}
                            <img src="/uploads/{{ office_settings.logo_path }}" alt="شعار المكتب" style="height: 60px; margin-bottom: 15px;">
                        {% else %}
                            <i class="fas fa-balance-scale fa-3x mb-3"></i>
                        {% endif %}
                        <h4>{{ office_settings.office_name }}</h4>
                        <p class="mb-0">تسجيل الدخول</p>
                    </div>
                    <div class="login-body">
                        {% with messages = get_flashed_messages(with_categories=true) %}
                            {% if messages %}
                                {% for category, message in messages %}
                                    <div class="alert alert-{{ 'danger' if category == 'error' else category }} alert-dismissible fade show">
                                        {{ message }}
                                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                                    </div>
                                {% endfor %}
                            {% endif %}
                        {% endwith %}

                        <form method="POST">
                            <div class="mb-3">
                                <label class="form-label">
                                    <i class="fas fa-user me-2"></i>اسم المستخدم
                                </label>
                                <input type="text" class="form-control" name="username" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">
                                    <i class="fas fa-lock me-2"></i>كلمة المرور
                                </label>
                                <input type="password" class="form-control" name="password" required>
                            </div>
                            <div class="mb-3 form-check">
                                <input type="checkbox" class="form-check-input" name="remember_me" id="remember_me">
                                <label class="form-check-label" for="remember_me">تذكرني</label>
                            </div>
                            <button type="submit" class="btn btn-primary w-100">
                                <i class="fas fa-sign-in-alt me-2"></i>تسجيل الدخول
                            </button>
                        </form>

                        <div class="text-center mt-4">
                            <small class="text-muted">
                                البيانات الافتراضية: admin / admin123
                            </small>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
    ''', office_settings=OfficeSettings.get_settings())

@app.route('/logout')
@login_required
def logout():
    """تسجيل الخروج"""
    logout_user()
    flash('تم تسجيل الخروج بنجاح', 'info')
    return redirect('/login')

@app.route('/')
@login_required
def index():
    try:
        # إزالة متطلب تسجيل الدخول مؤقتاً
        if True:  # current_user.is_authenticated:
            # الحصول على إعدادات المكتب
            office_settings = OfficeSettings.get_settings()

            clients_count = Client.query.count()
            documents_count = ClientDocument.query.count()
            cases_count = Case.query.count()
            appointments_count = Appointment.query.count()
            invoices_count = Invoice.query.count()
            pending_invoices = Invoice.query.filter_by(status='pending').count()
            today_appointments = Appointment.query.filter(
                db.func.date(Appointment.appointment_date) == datetime.now().date()
            ).count()

            # إحصائيات المصروفات
            expenses_count = Expense.query.count()
            total_expenses = db.session.query(db.func.sum(Expense.amount)).scalar() or 0
            monthly_expenses = db.session.query(db.func.sum(Expense.amount)).filter(
                db.func.extract('month', Expense.expense_date) == datetime.now().month,
                db.func.extract('year', Expense.expense_date) == datetime.now().year
            ).scalar() or 0

            return render_template_string('''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ office_settings.office_name }} - نظام إدارة المكتب القانوني</title>
    <!-- Bootstrap CSS with fallback -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet"
          onerror="this.onerror=null;this.href='https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.0/css/bootstrap.rtl.min.css';">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet"
          onerror="this.onerror=null;this.href='https://maxcdn.bootstrapcdn.com/font-awesome/6.4.0/css/all.min.css';">
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700&display=swap" rel="stylesheet"
          onerror="this.onerror=null;this.href='https://fonts.cdnfonts.com/css/cairo';">

    <!-- Inline Bootstrap CSS as ultimate fallback -->
    <style id="bootstrap-fallback" style="display: none;">
        /* Bootstrap RTL Fallback CSS */
        .container { max-width: 1200px; margin: 0 auto; padding: 0 15px; }
        .row { display: flex; flex-wrap: wrap; margin: 0 -15px; }
        .col, .col-md-6, .col-md-4, .col-md-3 { padding: 0 15px; flex: 1; }
        .col-md-6 { flex: 0 0 50%; max-width: 50%; }
        .col-md-4 { flex: 0 0 33.333333%; max-width: 33.333333%; }
        .col-md-3 { flex: 0 0 25%; max-width: 25%; }
        .btn { display: inline-block; padding: 0.375rem 0.75rem; margin-bottom: 0; font-size: 1rem;
               font-weight: 400; line-height: 1.5; text-align: center; text-decoration: none;
               vertical-align: middle; cursor: pointer; border: 1px solid transparent;
               border-radius: 0.25rem; transition: all 0.15s ease-in-out; }
        .btn-primary { color: #fff; background-color: #007bff; border-color: #007bff; }
        .btn-success { color: #fff; background-color: #28a745; border-color: #28a745; }
        .btn-danger { color: #fff; background-color: #dc3545; border-color: #dc3545; }
        .btn-warning { color: #212529; background-color: #ffc107; border-color: #ffc107; }
        .btn-info { color: #fff; background-color: #17a2b8; border-color: #17a2b8; }
        .btn-secondary { color: #fff; background-color: #6c757d; border-color: #6c757d; }
        .card { position: relative; display: flex; flex-direction: column; min-width: 0;
                word-wrap: break-word; background-color: #fff; background-clip: border-box;
                border: 1px solid rgba(0,0,0,.125); border-radius: 0.25rem; }
        .card-body { flex: 1 1 auto; padding: 1.25rem; }
        .card-header { padding: 0.75rem 1.25rem; margin-bottom: 0; background-color: rgba(0,0,0,.03);
                       border-bottom: 1px solid rgba(0,0,0,.125); }
        .form-control { display: block; width: 100%; padding: 0.375rem 0.75rem; font-size: 1rem;
                        font-weight: 400; line-height: 1.5; color: #495057; background-color: #fff;
                        background-clip: padding-box; border: 1px solid #ced4da; border-radius: 0.25rem; }
        .table { width: 100%; margin-bottom: 1rem; color: #212529; border-collapse: collapse; }
        .table th, .table td { padding: 0.75rem; vertical-align: top; border-top: 1px solid #dee2e6; }
        .table thead th { vertical-align: bottom; border-bottom: 2px solid #dee2e6; }
        .navbar { position: relative; display: flex; flex-wrap: wrap; align-items: center;
                  justify-content: space-between; padding: 0.5rem 1rem; }
        .navbar-brand { display: inline-block; padding-top: 0.3125rem; padding-bottom: 0.3125rem;
                        margin-left: 1rem; font-size: 1.25rem; line-height: inherit; white-space: nowrap; }
        .alert { position: relative; padding: 0.75rem 1.25rem; margin-bottom: 1rem; border: 1px solid transparent;
                 border-radius: 0.25rem; }
        .alert-success { color: #155724; background-color: #d4edda; border-color: #c3e6cb; }
        .alert-danger { color: #721c24; background-color: #f8d7da; border-color: #f5c6cb; }
        .alert-warning { color: #856404; background-color: #fff3cd; border-color: #ffeaa7; }
        .alert-info { color: #0c5460; background-color: #d1ecf1; border-color: #bee5eb; }
        .modal { position: fixed; top: 0; left: 0; z-index: 1050; display: none; width: 100%; height: 100%;
                 overflow: hidden; outline: 0; }
        .modal-dialog { position: relative; width: auto; margin: 0.5rem; pointer-events: none; }
        .modal-content { position: relative; display: flex; flex-direction: column; width: 100%;
                         pointer-events: auto; background-color: #fff; background-clip: padding-box;
                         border: 1px solid rgba(0,0,0,.2); border-radius: 0.3rem; outline: 0; }
        .modal-header { display: flex; align-items: flex-start; justify-content: space-between;
                        padding: 1rem 1rem; border-bottom: 1px solid #dee2e6; border-top-left-radius: calc(0.3rem - 1px);
                        border-top-right-radius: calc(0.3rem - 1px); }
        .modal-body { position: relative; flex: 1 1 auto; padding: 1rem; }
        .modal-footer { display: flex; flex-wrap: wrap; align-items: center; justify-content: flex-end;
                        padding: 0.75rem; border-top: 1px solid #dee2e6; border-bottom-right-radius: calc(0.3rem - 1px);
                        border-bottom-left-radius: calc(0.3rem - 1px); }
        .text-center { text-align: center !important; }
        .text-right { text-align: right !important; }
        .text-left { text-align: left !important; }
        .d-flex { display: flex !important; }
        .justify-content-between { justify-content: space-between !important; }
        .align-items-center { align-items: center !important; }
        .mb-3 { margin-bottom: 1rem !important; }
        .mt-3 { margin-top: 1rem !important; }
        .p-3 { padding: 1rem !important; }
        .bg-light { background-color: #f8f9fa !important; }
        .bg-primary { background-color: #007bff !important; }
        .text-white { color: #fff !important; }
        .border { border: 1px solid #dee2e6 !important; }
        .rounded { border-radius: 0.25rem !important; }
        .shadow { box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15) !important; }
        .img-fluid { max-width: 100%; height: auto; }
        .img-thumbnail { padding: 0.25rem; background-color: #fff; border: 1px solid #dee2e6;
                         border-radius: 0.25rem; max-width: 100%; height: auto; }
        /* RTL Support */
        [dir="rtl"] { direction: rtl; text-align: right; }
        [dir="rtl"] .navbar-brand { margin-right: 1rem; margin-left: 0; }
        [dir="rtl"] .modal-footer { justify-content: flex-start; }
    </style>

    <script>
        // Check if Bootstrap CSS loaded, if not show fallback
        document.addEventListener('DOMContentLoaded', function() {
            var testEl = document.createElement('div');
            testEl.className = 'container';
            testEl.style.position = 'absolute';
            testEl.style.visibility = 'hidden';
            document.body.appendChild(testEl);

            var computedStyle = window.getComputedStyle(testEl);
            if (computedStyle.maxWidth === 'none' || computedStyle.maxWidth === '') {
                console.warn('Bootstrap CSS failed to load, using fallback');
                document.getElementById('bootstrap-fallback').style.display = 'block';
                // Show a notification
                var notification = document.createElement('div');
                notification.innerHTML = '⚠️ تم تحميل التصميم الاحتياطي - قد يبدو الموقع مختلفاً قليلاً';
                notification.style.cssText = 'position: fixed; top: 10px; right: 10px; background: #ffc107; color: #000; padding: 10px; border-radius: 5px; z-index: 9999; font-size: 12px;';
                document.body.appendChild(notification);
                setTimeout(function() { notification.remove(); }, 5000);
            }
            document.body.removeChild(testEl);
        });
    </script>
    <link href="/static/css/custom.css" rel="stylesheet">
    <style>
        .riyal-symbol {
            display: inline-block;
            width: 18px;
            height: 18px;
            margin: 0 2px;
            vertical-align: middle;
        }

        /* إصلاح التخطيط - إزالة المساحات الجانبية */
        body {
            margin: 0;
            padding: 0;
            width: 100%;
            overflow-x: hidden;
        }

        .container-fluid {
            width: 100%;
            padding-right: 10px;
            padding-left: 10px;
            margin-right: auto;
            margin-left: auto;
            max-width: none;
        }

        .navbar .container {
            max-width: none;
            width: 100%;
            padding-right: 15px;
            padding-left: 15px;
        }

        /* تحسين المسافات بين البطاقات */
        .row {
            margin-right: -10px;
            margin-left: -10px;
        }

        .row > * {
            padding-right: 10px;
            padding-left: 10px;
        }

        /* تحسين بطاقات الإحصائيات */
        .stats-card {
            margin-bottom: 15px;
        }

        @media (max-width: 768px) {
            .container-fluid {
                padding-right: 5px;
                padding-left: 5px;
            }

            .row {
                margin-right: -5px;
                margin-left: -5px;
            }

            .row > * {
                padding-right: 5px;
                padding-left: 5px;
            }
        }
    </style>
</head>
<body>
    <!-- الشريط العلوي المحسن -->
    <nav class="navbar navbar-expand-lg navbar-dark">
        <div class="container-fluid">
            {{ navbar_brand | safe }}

            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>

            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav me-auto">
                    <li class="nav-item">
                        <a class="nav-link active" href="/">
                            <i class="fas fa-home me-1"></i>الرئيسية
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/clients">
                            <i class="fas fa-users me-1"></i>العملاء
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/cases">
                            <i class="fas fa-folder-open me-1"></i>القضايا
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/appointments">
                            <i class="fas fa-calendar-alt me-1"></i>المواعيد
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/invoices">
                            <i class="fas fa-file-invoice-dollar me-1"></i>الفواتير
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/documents">
                            <i class="fas fa-folder-open me-1"></i>المستندات
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/expenses">
                            <i class="fas fa-money-bill-wave me-1"></i>المصروفات
                        </a>
                    </li>
                    {% if user_has_permission('manage_users') %}
                    <li class="nav-item">
                        <a class="nav-link" href="/users">
                            <i class="fas fa-user-cog me-1"></i>المستخدمين
                        </a>
                    </li>
                    {% endif %}
                </ul>

                <div class="navbar-nav">
                    <div class="nav-item dropdown">
                        <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown">
                            <i class="fas fa-user-circle me-1"></i>
                            {{ current_user.full_name }}
                            <span class="badge bg-light text-dark ms-2">{{ current_user.role_name }}</span>
                        </a>
                        <ul class="dropdown-menu">
                            <li><a class="dropdown-item" href="/profile">
                                <i class="fas fa-user me-2"></i>الملف الشخصي
                            </a></li>
                            <li><a class="dropdown-item" href="/edit_profile">
                                <i class="fas fa-edit me-2"></i>تعديل الملف الشخصي
                            </a></li>
                            <li><hr class="dropdown-divider"></li>
                            <li><a class="dropdown-item" href="/logout">
                                <i class="fas fa-sign-out-alt me-2"></i>تسجيل الخروج
                            </a></li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    </nav>
    
    <div class="container-fluid px-4 mt-custom">
        <!-- رسائل التنبيه -->
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }} fade-in-up">
                        <i class="fas fa-info-circle me-2"></i>{{ message }}
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        <!-- عنوان الصفحة -->
        <div class="text-center mb-4">
            <h1 class="page-title fade-in-up">
                <i class="fas fa-tachometer-alt me-3"></i>
                لوحة التحكم الرئيسية
            </h1>
            <p class="lead text-muted">نظام إدارة المكتب القانوني المتكامل</p>
        </div>

        <!-- بطاقات الإحصائيات المحسنة -->
        <div class="row mb-5">
            <div class="col-lg-2 col-md-4 col-sm-6 mb-4">
                <div class="stats-card clients fade-in-up">
                    <div class="icon">
                        <i class="fas fa-users icon-hover" style="color: #17a2b8;"></i>
                    </div>
                    <div class="number">{{ clients_count }}</div>
                    <div class="label">العملاء</div>
                    <a href="/clients" class="btn btn-info btn-sm">
                        <i class="fas fa-eye me-1"></i>عرض التفاصيل
                    </a>
                </div>
            </div>

            <div class="col-lg-2 col-md-4 col-sm-6 mb-4">
                <div class="stats-card cases fade-in-up">
                    <div class="icon">
                        <i class="fas fa-folder-open icon-hover" style="color: #27ae60;"></i>
                    </div>
                    <div class="number">{{ cases_count }}</div>
                    <div class="label">القضايا</div>
                    <a href="/cases" class="btn btn-success btn-sm">
                        <i class="fas fa-eye me-1"></i>عرض التفاصيل
                    </a>
                </div>
            </div>

            <div class="col-lg-2 col-md-4 col-sm-6 mb-4">
                <div class="stats-card appointments fade-in-up">
                    <div class="icon">
                        <i class="fas fa-calendar-alt icon-hover" style="color: #f39c12;"></i>
                    </div>
                    <div class="number">{{ appointments_count }}</div>
                    <div class="label">المواعيد</div>
                    <a href="/appointments" class="btn btn-warning btn-sm">
                        <i class="fas fa-eye me-1"></i>عرض التفاصيل
                    </a>
                </div>
            </div>

            <div class="col-lg-2 col-md-4 col-sm-6 mb-4">
                <div class="stats-card invoices fade-in-up">
                    <div class="icon">
                        <i class="fas fa-file-invoice-dollar icon-hover" style="color: #e74c3c;"></i>
                    </div>
                    <div class="number">{{ invoices_count }}</div>
                    <div class="label">الفواتير</div>
                    <a href="/invoices" class="btn btn-danger btn-sm">
                        <i class="fas fa-eye me-1"></i>عرض التفاصيل
                    </a>
                </div>
            </div>

            <div class="col-lg-2 col-md-4 col-sm-6 mb-4">
                <div class="stats-card fade-in-up">
                    <div class="icon">
                        <i class="fas fa-file-alt icon-hover" style="color: #6c757d;"></i>
                    </div>
                    <div class="number">{{ documents_count }}</div>
                    <div class="label">المستندات</div>
                    <a href="/documents" class="btn btn-secondary btn-sm">
                        <i class="fas fa-eye me-1"></i>عرض التفاصيل
                    </a>
                </div>
            </div>

            <div class="col-lg-2 col-md-4 col-sm-6 mb-4">
                <div class="stats-card fade-in-up">
                    <div class="icon">
                        <i class="fas fa-exclamation-triangle icon-hover" style="color: #dc3545;"></i>
                    </div>
                    <div class="number">{{ pending_invoices }}</div>
                    <div class="label">فواتير معلقة</div>
                    <a href="/invoices?filter=pending" class="btn btn-outline-danger btn-sm">
                        <i class="fas fa-eye me-1"></i>عرض التفاصيل
                    </a>
                </div>
            </div>

            <div class="col-lg-2 col-md-4 col-sm-6 mb-4">
                <div class="stats-card fade-in-up">
                    <div class="icon">
                        <i class="fas fa-money-bill-wave icon-hover" style="color: #f39c12;"></i>
                    </div>
                    <div class="number">{{ expenses_count }}</div>
                    <div class="label">المصروفات</div>
                    <a href="/expenses" class="btn btn-warning btn-sm">
                        <i class="fas fa-eye me-1"></i>عرض التفاصيل
                    </a>
                </div>
            </div>
        </div>

        <!-- مواعيد اليوم -->
        {% if today_appointments > 0 %}
        <div class="alert alert-warning fade-in-up">
            <div class="d-flex align-items-center">
                <i class="fas fa-clock fa-2x me-3"></i>
                <div>
                    <h5 class="mb-1">⏰ تذكير مهم!</h5>
                    <p class="mb-2">لديك {{ today_appointments }} موعد اليوم</p>
                    <a href="/appointments?filter=today" class="btn btn-warning btn-sm">
                        <i class="fas fa-calendar-check me-1"></i>عرض مواعيد اليوم
                    </a>
                </div>
            </div>
        </div>
        {% endif %}

        <!-- البحث السريع المحسن -->
        <div class="search-container fade-in-up">
            <div class="card-header">
                <h5 class="mb-0">
                    <i class="fas fa-search me-2"></i>البحث السريع
                </h5>
            </div>
            <div class="row">
                <div class="col-md-6 mb-3">
                    <form method="GET" action="/cases">
                        <div class="input-group">
                            <span class="input-group-text">
                                <i class="fas fa-folder-open"></i>
                            </span>
                            <input type="text" class="form-control" name="search"
                                   placeholder="البحث في القضايا (اسم العميل، رقم الهاتف، رقم الهوية...)">
                            <input type="hidden" name="search_type" value="all">
                            <button class="btn btn-primary" type="submit">
                                <i class="fas fa-search me-1"></i>بحث في القضايا
                            </button>
                        </div>
                    </form>
                </div>
                <div class="col-md-6 mb-3">
                    <form method="GET" action="/clients">
                        <div class="input-group">
                            <span class="input-group-text">
                                <i class="fas fa-users"></i>
                            </span>
                            <input type="text" class="form-control" name="search"
                                   placeholder="البحث في العملاء (الاسم، رقم الهاتف، رقم الهوية...)">
                            <input type="hidden" name="search_type" value="all">
                            <button class="btn btn-success" type="submit">
                                <i class="fas fa-search me-1"></i>بحث في العملاء
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>

        <div class="section-divider"></div>

        <!-- الإجراءات السريعة المحسنة -->
        <div class="card fade-in-up">
            <div class="card-header">
                <h5 class="mb-0">
                    <i class="fas fa-bolt me-2"></i>الإجراءات السريعة
                </h5>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-lg-3 col-md-6 mb-3">
                        <a href="/add_client" class="btn btn-success btn-lg w-100">
                            <i class="fas fa-user-plus me-2"></i>
                            <div>
                                <strong>إضافة عميل جديد</strong>
                                <small class="d-block">تسجيل عميل جديد</small>
                            </div>
                        </a>
                    </div>
                    <div class="col-lg-3 col-md-6 mb-3">
                        <a href="/add_case" class="btn btn-primary btn-lg w-100">
                            <i class="fas fa-folder-plus me-2"></i>
                            <div>
                                <strong>إضافة قضية جديدة</strong>
                                <small class="d-block">فتح ملف قضية</small>
                            </div>
                        </a>
                    </div>
                    <div class="col-lg-3 col-md-6 mb-3">
                        <a href="/add_appointment" class="btn btn-warning btn-lg w-100">
                            <i class="fas fa-calendar-plus me-2"></i>
                            <div>
                                <strong>إضافة موعد جديد</strong>
                                <small class="d-block">جدولة موعد</small>
                            </div>
                        </a>
                    </div>
                    <div class="col-lg-3 col-md-6 mb-3">
                        <a href="/add_invoice" class="btn btn-danger btn-lg w-100">
                            <i class="fas fa-file-invoice-dollar me-2"></i>
                            <div>
                                <strong>إضافة فاتورة جديدة</strong>
                                <small class="d-block">إنشاء فاتورة</small>
                            </div>
                        </a>
                    </div>
                    <div class="col-lg-3 col-md-6 mb-3">
                        <a href="/reports" class="btn btn-info btn-lg w-100">
                            <i class="fas fa-chart-bar me-2"></i>
                            <div>
                                <strong>التقارير</strong>
                                <small class="d-block">عرض الإحصائيات</small>
                            </div>
                        </a>
                    </div>
                    <div class="col-lg-3 col-md-6 mb-3">
                        <a href="/invoices" class="btn btn-secondary btn-lg w-100">
                            <i class="fas fa-money-check-alt me-2"></i>
                            <div>
                                <strong>إدارة الفواتير</strong>
                                <small class="d-block">متابعة المدفوعات</small>
                            </div>
                        </a>
                    </div>
                    {% if current_user.role == 'admin' %}
                    <div class="col-lg-3 col-md-6 mb-3">
                        <a href="/users" class="btn btn-dark btn-lg w-100">
                            <i class="fas fa-users-cog me-2"></i>
                            <div>
                                <strong>إدارة المستخدمين</strong>
                                <small class="d-block">للمدير فقط</small>
                            </div>
                        </a>
                    </div>
                    {% endif %}

                    {% if current_user.role == 'admin' %}
                    <div class="col-lg-3 col-md-6 mb-3">
                        <a href="/office_settings" class="btn btn-info btn-lg w-100">
                            <i class="fas fa-cogs me-2"></i>
                            <div>
                                <strong>إعدادات المكتب</strong>
                                <small class="d-block">بيانات المكتب</small>
                            </div>
                        </a>
                    </div>
                    {% endif %}
                    <div class="col-lg-3 col-md-6 mb-3">
                        <a href="/expenses" class="btn btn-warning btn-lg w-100">
                            <i class="fas fa-money-bill-wave me-2"></i>
                            <div>
                                <strong>المصروفات</strong>
                                <small class="d-block">متابعة المصروفات</small>
                            </div>
                        </a>
                    </div>
                    <div class="col-lg-3 col-md-6 mb-3">
                        <a href="/all_documents" class="btn btn-outline-primary btn-lg w-100">
                            <i class="fas fa-file-alt me-2"></i>
                            <div>
                                <strong>المستندات</strong>
                                <small class="d-block">إدارة الملفات</small>
                            </div>
                        </a>
                    </div>
                </div>
            </div>
        </div>

        <!-- تذييل الصفحة -->
        <footer class="text-center mt-5 py-4">
            <div class="section-divider mb-4"></div>
            <p class="text-muted">
                <i class="fas fa-balance-scale me-2"></i>
                نظام إدارة المكتب القانوني - المحامي فالح بن عقاب آل عيسى
            </p>
            <p class="text-muted small">
                جميع الحقوق محفوظة © {{ current_year }}
            </p>
        </footer>
    </div>

    <!-- JavaScript للتفاعل -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"
            onerror="this.onerror=null;this.src='https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.0/js/bootstrap.bundle.min.js';"></script>

    <!-- Bootstrap JS Fallback -->
    <script>
        // Check if Bootstrap JS loaded
        document.addEventListener('DOMContentLoaded', function() {
            if (typeof bootstrap === 'undefined') {
                console.warn('Bootstrap JS failed to load, adding basic functionality');

                // Basic modal functionality
                window.showModal = function(modalId) {
                    var modal = document.getElementById(modalId);
                    if (modal) {
                        modal.style.display = 'block';
                        modal.style.position = 'fixed';
                        modal.style.top = '0';
                        modal.style.left = '0';
                        modal.style.width = '100%';
                        modal.style.height = '100%';
                        modal.style.backgroundColor = 'rgba(0,0,0,0.5)';
                        modal.style.zIndex = '1050';
                    }
                };

                window.hideModal = function(modalId) {
                    var modal = document.getElementById(modalId);
                    if (modal) {
                        modal.style.display = 'none';
                    }
                };

                // Basic dropdown functionality
                document.addEventListener('click', function(e) {
                    if (e.target.matches('.dropdown-toggle')) {
                        e.preventDefault();
                        var dropdown = e.target.nextElementSibling;
                        if (dropdown && dropdown.classList.contains('dropdown-menu')) {
                            dropdown.style.display = dropdown.style.display === 'block' ? 'none' : 'block';
                        }
                    }
                });

                // Close dropdowns when clicking outside
                document.addEventListener('click', function(e) {
                    if (!e.target.matches('.dropdown-toggle')) {
                        var dropdowns = document.querySelectorAll('.dropdown-menu');
                        dropdowns.forEach(function(dropdown) {
                            dropdown.style.display = 'none';
                        });
                    }
                });
            }
        });
    </script>
    <script>
        // تأثيرات الرسوم المتحركة
        document.addEventListener('DOMContentLoaded', function() {
            // إضافة تأثير fade-in للعناصر
            const elements = document.querySelectorAll('.fade-in-up');
            elements.forEach((element, index) => {
                element.style.animationDelay = (index * 0.1) + 's';
            });

            // تحسين تفاعل البطاقات
            const statsCards = document.querySelectorAll('.stats-card');
            statsCards.forEach(card => {
                card.addEventListener('mouseenter', function() {
                    this.style.transform = 'translateY(-10px) scale(1.02)';
                });

                card.addEventListener('mouseleave', function() {
                    this.style.transform = 'translateY(0) scale(1)';
                });
            });

            // تحسين الأزرار
            const buttons = document.querySelectorAll('.btn');
            buttons.forEach(button => {
                button.addEventListener('mouseenter', function() {
                    this.style.transform = 'translateY(-2px)';
                });

                button.addEventListener('mouseleave', function() {
                    this.style.transform = 'translateY(0)';
                });
            });
        });

        // إضافة تأثير loading للنماذج
        document.querySelectorAll('form').forEach(form => {
            form.addEventListener('submit', function() {
                const submitBtn = this.querySelector('button[type="submit"]');
                if (submitBtn) {
                    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>جاري البحث...';
                    submitBtn.disabled = true;
                }
            });
        });
    </script>
</body>
</html>
        ''', clients_count=clients_count, documents_count=documents_count, current_year=datetime.now().year,
             cases_count=cases_count, appointments_count=appointments_count,
             invoices_count=invoices_count, pending_invoices=pending_invoices,
             today_appointments=today_appointments, office_settings=office_settings,
             expenses_count=expenses_count, total_expenses=total_expenses, monthly_expenses=monthly_expenses,
             navbar_brand=get_navbar_brand())
        else:
            return redirect(url_for('login'))
    except Exception as e:
        print(f"❌ خطأ في الصفحة الرئيسية: {e}")
        return f'''
        <html dir="rtl">
        <head><title>خطأ في النظام</title></head>
        <body style="font-family: Arial; padding: 20px; text-align: center;">
            <h1>🚨 خطأ في النظام</h1>
            <p>عذراً، حدث خطأ في تشغيل النظام</p>
            <p><strong>تفاصيل الخطأ:</strong> {str(e)}</p>
            <p><a href="/login" style="color: blue;">العودة لتسجيل الدخول</a></p>
            <hr>
            <p><small>إذا استمر الخطأ، تواصل مع المطور</small></p>
        </body>
        </html>
        '''

# تم نقل route تسجيل الدخول إلى الأعلى

# تم نقل route تسجيل الخروج إلى الأعلى

@app.route('/clients')
@login_required
def clients():
    # الحصول على معايير البحث من الرابط
    search_query = request.args.get('search', '').strip()
    search_type = request.args.get('search_type', 'all')

    # بناء الاستعلام الأساسي
    query = Client.query

    # تطبيق البحث إذا كان موجوداً
    if search_query:
        if search_type == 'name':
            # البحث بالاسم (الاسم الأول أو الأخير)
            query = query.filter(
                db.or_(
                    Client.first_name.contains(search_query),
                    Client.last_name.contains(search_query),
                    db.func.concat(Client.first_name, ' ', Client.last_name).contains(search_query)
                )
            )
        elif search_type == 'phone':
            # البحث برقم الهاتف
            query = query.filter(Client.phone.contains(search_query))
        elif search_type == 'national_id':
            # البحث برقم الهوية
            query = query.filter(Client.national_id.contains(search_query))
        elif search_type == 'email':
            # البحث بالبريد الإلكتروني
            query = query.filter(Client.email.contains(search_query))
        else:  # search_type == 'all'
            # البحث في جميع الحقول
            query = query.filter(
                db.or_(
                    Client.first_name.contains(search_query),
                    Client.last_name.contains(search_query),
                    Client.phone.contains(search_query),
                    Client.national_id.contains(search_query),
                    Client.email.contains(search_query),
                    db.func.concat(Client.first_name, ' ', Client.last_name).contains(search_query)
                )
            )

    clients_list = query.order_by(Client.created_at.desc()).all()

    return render_template_string('''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>إدارة العملاء - نظام إدارة المكتب القانوني</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700&display=swap" rel="stylesheet">
    <link href="/static/css/custom.css" rel="stylesheet">
</head>
<body>
    <!-- الشريط العلوي المحسن -->
    <nav class="navbar navbar-expand-lg navbar-dark">
        <div class="container">
            <a class="navbar-brand" href="/">
                <i class="fas fa-balance-scale me-2"></i>
                المحامي فالح بن عقاب آل عيسى
            </a>

            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/">
                    <i class="fas fa-home me-1"></i>الرئيسية
                </a>
                <a class="nav-link active" href="/clients">
                    <i class="fas fa-users me-1"></i>العملاء
                </a>
                <a class="nav-link" href="/cases">
                    <i class="fas fa-folder-open me-1"></i>القضايا
                </a>
                <a class="nav-link" href="/appointments">
                    <i class="fas fa-calendar-alt me-1"></i>المواعيد
                </a>
                <a class="nav-link" href="/invoices">
                    <i class="fas fa-file-invoice-dollar me-1"></i>الفواتير
                </a>
            </div>
        </div>
    </nav>
    
    <div class="container mt-custom">
        <!-- عنوان الصفحة -->
        <div class="text-center mb-4">
            <h1 class="page-title fade-in-up">
                <i class="fas fa-users me-3"></i>
                إدارة العملاء
            </h1>
            <p class="lead text-muted">إدارة وتتبع معلومات العملاء</p>
        </div>

        <!-- رسائل التنبيه -->
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }} fade-in-up">
                        <i class="fas fa-info-circle me-2"></i>{{ message }}
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        <!-- شريط الإجراءات -->
        <div class="d-flex justify-content-between align-items-center mb-4">
            <div>
                <h4 class="mb-0">قائمة العملاء</h4>
                <small class="text-muted">إجمالي العملاء: {{ clients_list|length }}</small>
            </div>
            <a href="/add_client" class="btn btn-success btn-lg">
                <i class="fas fa-user-plus me-2"></i>إضافة عميل جديد
            </a>
        </div>

        <!-- نموذج البحث المحسن -->
        <div class="search-container fade-in-up">
            <div class="card-header">
                <h5 class="mb-0">
                    <i class="fas fa-search me-2"></i>البحث في العملاء
                </h5>
            </div>
            <form method="GET" action="/clients">
                <div class="row">
                    <div class="col-md-3">
                        <div class="mb-3">
                            <label class="form-label">
                                <i class="fas fa-filter me-1"></i>نوع البحث
                            </label>
                            <select class="form-control" name="search_type">
                                <option value="all" {{ 'selected' if request.args.get('search_type') == 'all' else '' }}>
                                    <i class="fas fa-globe"></i> البحث في جميع الحقول
                                </option>
                                <option value="name" {{ 'selected' if request.args.get('search_type') == 'name' else '' }}>
                                    👤 الاسم
                                </option>
                                <option value="phone" {{ 'selected' if request.args.get('search_type') == 'phone' else '' }}>
                                    📱 رقم الهاتف
                                </option>
                                <option value="national_id" {{ 'selected' if request.args.get('search_type') == 'national_id' else '' }}>
                                    🆔 رقم الهوية
                                </option>
                                <option value="email" {{ 'selected' if request.args.get('search_type') == 'email' else '' }}>
                                    📧 البريد الإلكتروني
                                </option>
                            </select>
                        </div>
                    </div>
                    <div class="col-md-7">
                        <div class="mb-3">
                            <label class="form-label">
                                <i class="fas fa-keyboard me-1"></i>كلمة البحث
                            </label>
                            <div class="input-group">
                                <span class="input-group-text">
                                    <i class="fas fa-search"></i>
                                </span>
                                <input type="text" class="form-control" name="search"
                                       value="{{ request.args.get('search', '') }}"
                                       placeholder="أدخل كلمة البحث...">
                            </div>
                        </div>
                    </div>
                                <div class="col-md-2">
                                    <div class="mb-3">
                                        <label class="form-label">&nbsp;</label>
                                        <div class="d-grid">
                                            <button type="submit" class="btn btn-primary">
                                                <i class="fas fa-search"></i> بحث
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            {% if request.args.get('search') %}
                            <div class="row">
                                <div class="col-12">
                                    <div class="alert alert-info d-flex justify-content-between align-items-center">
                                        <span>
                                            <i class="fas fa-info-circle"></i>
                                            نتائج البحث عن: "<strong>{{ request.args.get('search') }}</strong>"
                                            - تم العثور على {{ clients_list|length }} نتيجة
                                        </span>
                                        <a href="/clients" class="btn btn-sm btn-outline-secondary">
                                            <i class="fas fa-times"></i> مسح البحث
                                        </a>
                                    </div>
                                </div>
                            </div>
                            {% endif %}
                        </form>
                    </div>
                </div>

                {% if clients_list %}
                <table class="table">
                    <thead>
                        <tr>
                            <th>الاسم</th>
                            <th>رقم الهوية</th>
                            <th>الهاتف</th>
                            <th>البريد</th>
                            <th>المستندات</th>
                            <th>الإجراءات</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for client in clients_list %}
                        <tr>
                            <td><strong>{{ client.full_name }}</strong></td>
                            <td>{{ client.national_id or '-' }}</td>
                            <td>{{ client.phone or '-' }}</td>
                            <td>{{ client.email or '-' }}</td>
                            <td>
                                <span class="badge bg-info">{{ client.client_documents|length }}</span>
                                <a href="/client_documents/{{ client.id }}" class="btn btn-sm btn-outline-info">📄 عرض</a>
                            </td>
                            <td>
                                <div class="btn-group" role="group">
                                    <a href="/edit_client/{{ client.id }}" class="btn btn-sm btn-warning">✏️ تعديل</a>
                                    <a href="/delete_client/{{ client.id }}" class="btn btn-sm btn-danger"
                                       onclick="return confirm('حذف {{ client.full_name }}؟\\n\\nملاحظة: سيتم رفض الحذف إذا كان العميل مرتبط بقضايا أو مواعيد أو فواتير.')">🗑️ حذف</a>
                                    {% if user_has_permission('manage_users') %}
                                    <a href="/force_delete_client/{{ client.id }}" class="btn btn-sm btn-outline-danger"
                                       onclick="return confirm('⚠️ تحذير: حذف قسري!\\n\\nسيتم حذف {{ client.full_name }} مع جميع بياناته المرتبطة:\\n- جميع القضايا\\n- جميع المواعيد\\n- جميع الفواتير\\n- جميع المستندات\\n\\nهذا الإجراء لا يمكن التراجع عنه!\\n\\nهل أنت متأكد؟')"
                                       title="حذف قسري مع جميع البيانات المرتبطة (للمدير فقط)">🗑️💥 حذف قسري</a>
                                    {% endif %}
                                </div>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
                {% else %}
                <div class="text-center py-5">
                    {% if request.args.get('search') %}
                    <i class="fas fa-search fa-3x text-muted mb-3"></i>
                    <h5 class="text-muted">لم يتم العثور على نتائج</h5>
                    <p class="text-muted">لا يوجد عملاء يطابقون معايير البحث المحددة</p>
                    <a href="/clients" class="btn btn-secondary me-2">مسح البحث</a>
                    <a href="/add_client" class="btn btn-primary">إضافة عميل جديد</a>
                    {% else %}
                    <i class="fas fa-users fa-3x text-muted mb-3"></i>
                    <h5 class="text-muted">لا توجد عملاء</h5>
                    <p class="text-muted">ابدأ بإضافة عميل جديد</p>
                    <a href="/add_client" class="btn btn-primary">إضافة عميل جديد</a>
                    {% endif %}
                </div>
                {% endif %}
            </div>
        </div>
    </div>
</body>
</html>
    ''', clients_list=clients_list, search_query=search_query, search_type=search_type)

@app.route('/cases')
@login_required
def cases():
    # الحصول على معايير البحث من الرابط
    search_query = request.args.get('search', '').strip()
    search_type = request.args.get('search_type', 'all')

    # بناء الاستعلام الأساسي
    query = Case.query.join(Client)

    # تطبيق البحث إذا كان موجوداً
    if search_query:
        if search_type == 'client_name':
            # البحث بالاسم (الاسم الأول أو الأخير)
            query = query.filter(
                db.or_(
                    Client.first_name.contains(search_query),
                    Client.last_name.contains(search_query),
                    db.func.concat(Client.first_name, ' ', Client.last_name).contains(search_query)
                )
            )
        elif search_type == 'phone':
            # البحث برقم الهاتف
            query = query.filter(Client.phone.contains(search_query))
        elif search_type == 'national_id':
            # البحث برقم الهوية
            query = query.filter(Client.national_id.contains(search_query))
        elif search_type == 'case_number':
            # البحث برقم القضية
            query = query.filter(Case.case_number.contains(search_query))
        elif search_type == 'case_title':
            # البحث بعنوان القضية
            query = query.filter(Case.title.contains(search_query))
        else:  # search_type == 'all'
            # البحث في جميع الحقول
            query = query.filter(
                db.or_(
                    Client.first_name.contains(search_query),
                    Client.last_name.contains(search_query),
                    Client.phone.contains(search_query),
                    Client.national_id.contains(search_query),
                    Case.case_number.contains(search_query),
                    Case.title.contains(search_query),
                    db.func.concat(Client.first_name, ' ', Client.last_name).contains(search_query)
                )
            )

    cases_list = query.order_by(Case.created_at.desc()).all()

    return render_template_string('''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="utf-8">
    <title>إدارة القضايا</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/">🏛️ المحامي فالح بن عقاب آل عيسى</a>
            <div>
                <a class="btn btn-outline-light btn-sm" href="/">الرئيسية</a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="card">
            <div class="card-header d-flex justify-content-between">
                <h3>📁 إدارة القضايا</h3>
                <a href="/add_case" class="btn btn-primary">➕ إضافة قضية</a>
            </div>
            <div class="card-body">
                {% with messages = get_flashed_messages(with_categories=true) %}
                    {% if messages %}
                        {% for category, message in messages %}
                            <div class="alert alert-{{ category }}">{{ message }}</div>
                        {% endfor %}
                    {% endif %}
                {% endwith %}

                <!-- نموذج البحث -->
                <div class="card mb-4">
                    <div class="card-header">
                        <h5 class="mb-0">🔍 البحث في القضايا</h5>
                    </div>
                    <div class="card-body">
                        <form method="GET" action="/cases">
                            <div class="row">
                                <div class="col-md-4">
                                    <div class="mb-3">
                                        <label class="form-label">نوع البحث</label>
                                        <select class="form-control" name="search_type">
                                            <option value="all" {{ 'selected' if request.args.get('search_type') == 'all' else '' }}>البحث في جميع الحقول</option>
                                            <option value="client_name" {{ 'selected' if request.args.get('search_type') == 'client_name' else '' }}>اسم العميل</option>
                                            <option value="phone" {{ 'selected' if request.args.get('search_type') == 'phone' else '' }}>رقم الهاتف</option>
                                            <option value="national_id" {{ 'selected' if request.args.get('search_type') == 'national_id' else '' }}>رقم الهوية</option>
                                            <option value="case_number" {{ 'selected' if request.args.get('search_type') == 'case_number' else '' }}>رقم القضية</option>
                                            <option value="case_title" {{ 'selected' if request.args.get('search_type') == 'case_title' else '' }}>عنوان القضية</option>
                                        </select>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">كلمة البحث</label>
                                        <input type="text" class="form-control" name="search"
                                               value="{{ request.args.get('search', '') }}"
                                               placeholder="أدخل كلمة البحث...">
                                    </div>
                                </div>
                                <div class="col-md-2">
                                    <div class="mb-3">
                                        <label class="form-label">&nbsp;</label>
                                        <div class="d-grid">
                                            <button type="submit" class="btn btn-primary">
                                                <i class="fas fa-search"></i> بحث
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            {% if request.args.get('search') %}
                            <div class="row">
                                <div class="col-12">
                                    <div class="alert alert-info d-flex justify-content-between align-items-center">
                                        <span>
                                            <i class="fas fa-info-circle"></i>
                                            نتائج البحث عن: "<strong>{{ request.args.get('search') }}</strong>"
                                            {% if request.args.get('search_type') != 'all' %}
                                            في: <strong>
                                                {% if request.args.get('search_type') == 'client_name' %}اسم العميل
                                                {% elif request.args.get('search_type') == 'phone' %}رقم الهاتف
                                                {% elif request.args.get('search_type') == 'national_id' %}رقم الهوية
                                                {% elif request.args.get('search_type') == 'case_number' %}رقم القضية
                                                {% elif request.args.get('search_type') == 'case_title' %}عنوان القضية
                                                {% endif %}
                                            </strong>
                                            {% endif %}
                                            - تم العثور على {{ cases_list|length }} نتيجة
                                        </span>
                                        <a href="/cases" class="btn btn-sm btn-outline-secondary">
                                            <i class="fas fa-times"></i> مسح البحث
                                        </a>
                                    </div>
                                </div>
                            </div>
                            {% endif %}
                        </form>
                    </div>
                </div>

                {% if cases_list %}
                <div class="table-responsive">
                    <table class="table table-striped">
                        <thead>
                            <tr>
                                <th>رقم القضية</th>
                                <th>العنوان</th>
                                <th>العميل</th>
                                <th>النوع</th>
                                <th>الحالة</th>
                                <th>الجلسة القادمة</th>
                                <th>الإجراءات</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for case in cases_list %}
                            <tr>
                                <td><strong>{{ case.case_number }}</strong></td>
                                <td>{{ case.title }}</td>
                                <td>{{ case.client.full_name }}</td>
                                <td>{{ case.case_type }}</td>
                                <td>
                                    <span class="badge bg-{{ case.status_badge }}">
                                        {% if case.status == 'active' %}نشطة
                                        {% elif case.status == 'closed' %}مغلقة
                                        {% elif case.status == 'pending' %}معلقة
                                        {% else %}ملغية{% endif %}
                                    </span>
                                </td>
                                <td>
                                    {% if case.next_hearing_date %}
                                        {{ case.next_hearing_date.strftime('%Y-%m-%d') }}
                                    {% else %}
                                        -
                                    {% endif %}
                                </td>
                                <td>
                                    <div class="btn-group btn-group-sm" role="group">
                                        <a href="/view_case/{{ case.id }}" class="btn btn-outline-info">👁️ عرض</a>
                                        <a href="/add_invoice?case_id={{ case.id }}" class="btn btn-outline-success">💰 فاتورة</a>
                                        <a href="/edit_case/{{ case.id }}" class="btn btn-outline-warning">✏️ تعديل</a>
                                        <a href="/delete_case/{{ case.id }}" class="btn btn-outline-danger"
                                           onclick="return confirm('حذف القضية {{ case.case_number }}؟')">🗑️ حذف</a>
                                    </div>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                {% else %}
                <div class="text-center py-5">
                    {% if request.args.get('search') %}
                    <i class="fas fa-search fa-3x text-muted mb-3"></i>
                    <h5 class="text-muted">لم يتم العثور على نتائج</h5>
                    <p class="text-muted">لا توجد قضايا تطابق معايير البحث المحددة</p>
                    <a href="/cases" class="btn btn-secondary me-2">مسح البحث</a>
                    <a href="/add_case" class="btn btn-primary">إضافة قضية جديدة</a>
                    {% else %}
                    <i class="fas fa-folder-open fa-3x text-muted mb-3"></i>
                    <h5 class="text-muted">لا توجد قضايا</h5>
                    <p class="text-muted">ابدأ بإضافة قضية جديدة</p>
                    <a href="/add_case" class="btn btn-primary">إضافة قضية جديدة</a>
                    {% endif %}
                </div>
                {% endif %}
            </div>
        </div>
    </div>
</body>
</html>
    ''', cases_list=cases_list, search_query=search_query, search_type=search_type)

@app.route('/add_case', methods=['GET', 'POST'])
@login_required
def add_case():
    if request.method == 'POST':
        case = Case(
            case_number=request.form['case_number'],
            title=request.form['title'],
            case_type=request.form['case_type'],
            description=request.form.get('description'),
            court_name=request.form.get('court_name'),
            judge_name=request.form.get('judge_name'),
            client_id=request.form['client_id']
        )

        # معالجة تاريخ الجلسة القادمة
        if request.form.get('next_hearing_date'):
            case.next_hearing_date = datetime.strptime(
                request.form['next_hearing_date'], '%Y-%m-%dT%H:%M'
            )

        db.session.add(case)
        db.session.commit()
        flash(f'تم إضافة القضية {case.case_number} بنجاح', 'success')
        return redirect(url_for('cases'))

    clients = Client.query.all()
    return render_template_string('''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="utf-8">
    <title>إضافة قضية جديدة</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/">🏛️ المحامي فالح بن عقاب آل عيسى</a>
            <div>
                <a class="btn btn-outline-light btn-sm" href="/cases">القضايا</a>
                <a class="btn btn-outline-light btn-sm ms-2" href="/">الرئيسية</a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="card">
            <div class="card-header bg-primary text-white">
                <h3>➕ إضافة قضية جديدة</h3>
            </div>
            <div class="card-body">
                <form method="POST">
                    <div class="row">
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label class="form-label">رقم القضية *</label>
                                <input type="text" class="form-control" name="case_number" required placeholder="مثال: 2025/123">
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label class="form-label">العميل *</label>
                                <select class="form-control" name="client_id" required>
                                    <option value="">اختر العميل</option>
                                    {% for client in clients %}
                                    <option value="{{ client.id }}">{{ client.full_name }}</option>
                                    {% endfor %}
                                </select>
                            </div>
                        </div>
                    </div>

                    <div class="mb-3">
                        <label class="form-label">عنوان القضية *</label>
                        <input type="text" class="form-control" name="title" required placeholder="مثال: دعوى مطالبة مالية">
                    </div>

                    <div class="row">
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label class="form-label">نوع القضية *</label>
                                <select class="form-control" name="case_type" required>
                                    <option value="">اختر النوع</option>
                                    <option value="مدنية">مدنية</option>
                                    <option value="تجارية">تجارية</option>
                                    <option value="جنائية">جنائية</option>
                                    <option value="عمالية">عمالية</option>
                                    <option value="أحوال شخصية">أحوال شخصية</option>
                                    <option value="إدارية">إدارية</option>
                                    <option value="أخرى">أخرى</option>
                                </select>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label class="form-label">الجلسة القادمة</label>
                                <input type="datetime-local" class="form-control" name="next_hearing_date">
                            </div>
                        </div>
                    </div>

                    <div class="row">
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label class="form-label">اسم المحكمة</label>
                                <input type="text" class="form-control" name="court_name" placeholder="مثال: المحكمة العامة بالرياض">
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label class="form-label">اسم القاضي</label>
                                <input type="text" class="form-control" name="judge_name" placeholder="مثال: القاضي أحمد محمد">
                            </div>
                        </div>
                    </div>

                    <div class="mb-3">
                        <label class="form-label">وصف القضية</label>
                        <textarea class="form-control" name="description" rows="4" placeholder="تفاصيل القضية والملاحظات..."></textarea>
                    </div>

                    <div class="text-center">
                        <button type="submit" class="btn btn-primary btn-lg">💾 حفظ القضية</button>
                        <a href="/cases" class="btn btn-secondary btn-lg ms-2">❌ إلغاء</a>
                    </div>
                </form>
            </div>
        </div>
    </div>
</body>
</html>
    ''', clients=clients)

@app.route('/view_case/<int:case_id>')
@login_required
def view_case(case_id):
    case = Case.query.get_or_404(case_id)
    case_appointments = Appointment.query.filter_by(case_id=case_id).order_by(Appointment.appointment_date.desc()).all()
    case_invoices = Invoice.query.filter_by(case_id=case_id).order_by(Invoice.created_at.desc()).all()
    case_documents = ClientDocument.query.filter_by(case_id=case_id).order_by(ClientDocument.created_at.desc()).all()
    client_documents = ClientDocument.query.filter_by(client_id=case.client_id, case_id=None).all()

    # حساب إجمالي الفواتير
    total_invoices_amount = sum(invoice.total_amount for invoice in case_invoices)
    total_paid_amount = sum(invoice.paid_amount for invoice in case_invoices)
    total_remaining_amount = total_invoices_amount - total_paid_amount

    return render_template_string('''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="utf-8">
    <title>عرض القضية</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/">🏛️ المحامي فالح بن عقاب آل عيسى</a>
            <div>
                <a class="btn btn-outline-light btn-sm" href="/cases">القضايا</a>
                <a class="btn btn-outline-light btn-sm ms-2" href="/">الرئيسية</a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="card">
            <div class="card-header bg-info text-white d-flex justify-content-between align-items-center">
                <h3>👁️ عرض القضية: {{ case.case_number }}</h3>
                <div>
                    <a href="/edit_case/{{ case.id }}" class="btn btn-warning btn-sm">✏️ تعديل</a>
                    <a href="/delete_case/{{ case.id }}" class="btn btn-danger btn-sm"
                       onclick="return confirm('حذف القضية {{ case.case_number }}؟')">🗑️ حذف</a>
                </div>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-8">
                        <h4>{{ case.title }}</h4>
                        <div class="row mb-3">
                            <div class="col-md-6">
                                <strong>رقم القضية:</strong> {{ case.case_number }}
                            </div>
                            <div class="col-md-6">
                                <strong>العميل:</strong> {{ case.client.full_name }}
                            </div>
                        </div>
                        <div class="row mb-3">
                            <div class="col-md-6">
                                <strong>نوع القضية:</strong> {{ case.case_type }}
                            </div>
                            <div class="col-md-6">
                                <strong>الحالة:</strong>
                                <span class="badge bg-{{ case.status_badge }}">
                                    {% if case.status == 'active' %}نشطة
                                    {% elif case.status == 'closed' %}مغلقة
                                    {% elif case.status == 'pending' %}معلقة
                                    {% else %}ملغية{% endif %}
                                </span>
                            </div>
                        </div>
                        <div class="row mb-3">
                            <div class="col-md-6">
                                <strong>المحكمة:</strong> {{ case.court_name or '-' }}
                            </div>
                            <div class="col-md-6">
                                <strong>القاضي:</strong> {{ case.judge_name or '-' }}
                            </div>
                        </div>
                        {% if case.next_hearing_date %}
                        <div class="row mb-3">
                            <div class="col-md-12">
                                <strong>الجلسة القادمة:</strong>
                                <span class="badge bg-warning">{{ case.next_hearing_date.strftime('%Y-%m-%d %H:%M') }}</span>
                            </div>
                        </div>
                        {% endif %}
                        {% if case.description %}
                        <div class="mb-3">
                            <strong>وصف القضية:</strong>
                            <p class="mt-2">{{ case.description }}</p>
                        </div>
                        {% endif %}
                    </div>
                    <div class="col-md-4">
                        <div class="card">
                            <div class="card-header">
                                <h6>معلومات إضافية</h6>
                            </div>
                            <div class="card-body">
                                <p><strong>تاريخ الإنشاء:</strong><br>{{ case.created_at.strftime('%Y-%m-%d') }}</p>
                                <p><strong>عدد المواعيد:</strong><br>{{ case_appointments|length }}</p>
                                <div class="d-grid gap-2">
                                    <a href="/add_appointment?case_id={{ case.id }}" class="btn btn-primary btn-sm">📅 إضافة موعد</a>
                                    <a href="/client_documents/{{ case.client_id }}" class="btn btn-info btn-sm">📄 مستندات العميل</a>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- المواعيد المرتبطة -->
        {% if case_appointments %}
        <div class="card mt-4">
            <div class="card-header">
                <h5>📅 المواعيد المرتبطة بالقضية</h5>
            </div>
            <div class="card-body">
                <div class="table-responsive">
                    <table class="table table-sm">
                        <thead>
                            <tr>
                                <th>العنوان</th>
                                <th>التاريخ</th>
                                <th>المكان</th>
                                <th>الحالة</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for appointment in case_appointments %}
                            <tr>
                                <td>{{ appointment.title }}</td>
                                <td>{{ appointment.appointment_date.strftime('%Y-%m-%d %H:%M') }}</td>
                                <td>{{ appointment.location or '-' }}</td>
                                <td>
                                    <span class="badge bg-{{ appointment.status_badge }}">
                                        {% if appointment.status == 'scheduled' %}مجدول
                                        {% elif appointment.status == 'completed' %}مكتمل
                                        {% elif appointment.status == 'cancelled' %}ملغي
                                        {% else %}معاد جدولته{% endif %}
                                    </span>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        {% endif %}

        <!-- قسم الفواتير المرتبطة بالقضية -->
        <div class="card mt-4">
            <div class="card-header d-flex justify-content-between align-items-center">
                <h5>💰 الفواتير المرتبطة بالقضية</h5>
                <div>
                    <span class="badge bg-primary me-2">{{ case_invoices|length }} فاتورة</span>
                    <a href="/add_invoice?case_id={{ case.id }}" class="btn btn-success btn-sm">➕ إضافة فاتورة</a>
                </div>
            </div>
            <div class="card-body">
                {% if case_invoices %}
                    <!-- ملخص مالي -->
                    <div class="row mb-3">
                        <div class="col-md-4">
                            <div class="card bg-primary text-white">
                                <div class="card-body text-center">
                                    <h6>إجمالي الفواتير</h6>
                                    <h4>{{ "{:,.2f}".format(total_invoices_amount) }} {{ riyal_svg()|safe }}</h4>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="card bg-success text-white">
                                <div class="card-body text-center">
                                    <h6>المبلغ المدفوع</h6>
                                    <h4>{{ "{:,.2f}".format(total_paid_amount) }} {{ riyal_svg()|safe }}</h4>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="card bg-danger text-white">
                                <div class="card-body text-center">
                                    <h6>المبلغ المتبقي</h6>
                                    <h4>{{ "{:,.2f}".format(total_remaining_amount) }} {{ riyal_svg()|safe }}</h4>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- شريط التقدم الإجمالي -->
                    {% if total_invoices_amount > 0 %}
                    <div class="mb-3">
                        <div class="d-flex justify-content-between">
                            <span>نسبة الدفع الإجمالية</span>
                            <span>{{ "{:.1f}".format((total_paid_amount / total_invoices_amount) * 100) }}%</span>
                        </div>
                        <div class="progress">
                            <div class="progress-bar bg-success" style="width: {{ (total_paid_amount / total_invoices_amount) * 100 }}%"></div>
                        </div>
                    </div>
                    {% endif %}

                    <!-- جدول الفواتير -->
                    <div class="table-responsive">
                        <table class="table table-striped">
                            <thead>
                                <tr>
                                    <th>رقم الفاتورة</th>
                                    <th>التاريخ</th>
                                    <th>المبلغ</th>
                                    <th>المدفوع</th>
                                    <th>المتبقي</th>
                                    <th>الحالة</th>
                                    <th>الإجراءات</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for invoice in case_invoices %}
                                <tr>
                                    <td><strong>{{ invoice.invoice_number }}</strong></td>
                                    <td>{{ invoice.issue_date.strftime('%Y-%m-%d') }}</td>
                                    <td>{{ "{:,.2f}".format(invoice.total_amount) }} {{ riyal_svg()|safe }}</td>
                                    <td class="text-success">{{ "{:,.2f}".format(invoice.paid_amount) }} {{ riyal_svg()|safe }}</td>
                                    <td class="text-danger">{{ "{:,.2f}".format(invoice.remaining_amount) }} {{ riyal_svg()|safe }}</td>
                                    <td>
                                        <span class="badge bg-{{ invoice.status_badge }}">
                                            {% if invoice.status == 'pending' %}معلقة
                                            {% elif invoice.status == 'paid' %}مكتملة
                                            {% elif invoice.status == 'partial' %}جزئية
                                            {% else %}ملغية{% endif %}
                                        </span>
                                        {% if invoice.payments %}
                                            <br><small class="text-muted">{{ invoice.payments|length }} دفعة</small>
                                        {% endif %}
                                    </td>
                                    <td>
                                        <div class="btn-group btn-group-sm">
                                            <a href="/view_invoice/{{ invoice.id }}" class="btn btn-outline-info">👁️</a>
                                            {% if invoice.remaining_amount > 0 %}
                                                <a href="/add_payment/{{ invoice.id }}" class="btn btn-outline-success">💰</a>
                                            {% endif %}
                                            <a href="/edit_invoice/{{ invoice.id }}" class="btn btn-outline-warning">✏️</a>
                                        </div>
                                    </td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                {% else %}
                    <div class="text-center py-4">
                        <h6 class="text-muted">لا توجد فواتير مرتبطة بهذه القضية</h6>
                        <a href="/add_invoice?case_id={{ case.id }}" class="btn btn-success">إضافة فاتورة جديدة</a>
                    </div>
                {% endif %}
            </div>
        </div>

        <!-- قسم المستندات المرتبطة بالقضية -->
        <div class="card mt-4">
            <div class="card-header d-flex justify-content-between align-items-center">
                <h5>📄 مستندات القضية</h5>
                <div>
                    <span class="badge bg-info me-2">{{ case_documents|length }} مستند مرتبط</span>
                    <span class="badge bg-secondary me-2">{{ client_documents|length }} مستند عام</span>
                    <a href="/client_documents/{{ case.client_id }}?case_id={{ case.id }}" class="btn btn-success btn-sm">➕ إضافة مستند</a>
                </div>
            </div>
            <div class="card-body">
                <!-- المستندات المرتبطة بالقضية -->
                {% if case_documents %}
                <div class="mb-4">
                    <h6 class="text-primary">📋 المستندات المرتبطة بهذه القضية</h6>
                    <div class="row">
                        {% for document in case_documents %}
                        <div class="col-md-4 mb-3">
                            <div class="card border-primary">
                                <div class="card-body">
                                    <div class="d-flex justify-content-between align-items-start">
                                        <div>
                                            <h6 class="card-title">
                                                {% if document.document_type == 'national_id' %}🆔 الهوية الوطنية
                                                {% elif document.document_type == 'power_of_attorney' %}📜 توكيل
                                                {% elif document.document_type == 'contract' %}📋 عقد
                                                {% elif document.document_type == 'court_document' %}⚖️ مستند محكمة
                                                {% elif document.document_type == 'evidence' %}🔍 دليل
                                                {% else %}📄 مستند أخر{% endif %}
                                            </h6>
                                            <p class="card-text small">{{ document.description or 'بدون وصف' }}</p>
                                            <small class="text-muted">{{ document.created_at.strftime('%Y-%m-%d') }}</small>
                                        </div>
                                        <div class="dropdown">
                                            <button class="btn btn-sm btn-outline-secondary dropdown-toggle" data-bs-toggle="dropdown">⚙️</button>
                                            <ul class="dropdown-menu">
                                                {% if document.filename %}
                                                    <li><a class="dropdown-item" href="{{ url_for('simple_file', filename=document.filename) }}" target="_blank">👁️ معاينة</a></li>
                                                    <li><a class="dropdown-item" href="{{ url_for('download_file', filename=document.filename) }}">📥 تحميل</a></li>
                                                {% endif %}
                                                <li><a class="dropdown-item" href="/unlink_document/{{ document.id }}" onclick="return confirm('إلغاء ربط المستند بالقضية؟')">🔗 إلغاء الربط</a></li>
                                                <li><a class="dropdown-item text-danger" href="/delete_document/{{ document.id }}" onclick="return confirm('حذف المستند نهائياً؟')">🗑️ حذف</a></li>
                                            </ul>
                                        </div>
                                    </div>
                                    {% if document.filename %}
                                        <div class="mt-2">
                                            {% if document.is_image %}
                                                <img src="{{ url_for('simple_file', filename=document.filename) }}" class="img-thumbnail" style="max-height: 100px;">
                                            {% elif document.is_pdf %}
                                                <span class="badge bg-danger">PDF</span>
                                            {% else %}
                                                <span class="badge bg-info">{{ document.file_extension | safe_upper }}</span>
                                            {% endif %}
                                            <small class="text-muted d-block">{{ document.file_size_mb }} MB</small>
                                        </div>
                                    {% endif %}
                                </div>
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                </div>
                {% endif %}

                <!-- المستندات العامة للعميل -->
                {% if client_documents %}
                <div class="mb-4">
                    <h6 class="text-secondary">📂 مستندات العميل العامة (يمكن ربطها بالقضية)</h6>
                    <div class="row">
                        {% for document in client_documents %}
                        <div class="col-md-4 mb-3">
                            <div class="card border-secondary">
                                <div class="card-body">
                                    <div class="d-flex justify-content-between align-items-start">
                                        <div>
                                            <h6 class="card-title">
                                                {% if document.document_type == 'national_id' %}🆔 الهوية الوطنية
                                                {% elif document.document_type == 'power_of_attorney' %}📜 توكيل
                                                {% elif document.document_type == 'contract' %}📋 عقد
                                                {% else %}📄 مستند أخر{% endif %}
                                            </h6>
                                            <p class="card-text small">{{ document.description or 'بدون وصف' }}</p>
                                            <small class="text-muted">{{ document.created_at.strftime('%Y-%m-%d') }}</small>
                                        </div>
                                        <div class="dropdown">
                                            <button class="btn btn-sm btn-outline-secondary dropdown-toggle" data-bs-toggle="dropdown">⚙️</button>
                                            <ul class="dropdown-menu">
                                                <li><a class="dropdown-item text-primary" href="/link_document/{{ document.id }}/{{ case.id }}" onclick="return confirm('ربط المستند بهذه القضية؟')">🔗 ربط بالقضية</a></li>
                                                {% if document.filename %}
                                                    <li><a class="dropdown-item" href="/documents/{{ document.id }}/view" target="_blank">👁️ معاينة</a></li>
                                                    <li><a class="dropdown-item" href="/documents/{{ document.id }}/download">📥 تحميل</a></li>
                                                {% endif %}
                                            </ul>
                                        </div>
                                    </div>
                                    {% if document.filename %}
                                        <div class="mt-2">
                                            {% if document.is_image %}
                                                <img src="{{ url_for('simple_file', filename=document.filename) }}" class="img-thumbnail" style="max-height: 100px;">
                                            {% elif document.is_pdf %}
                                                <span class="badge bg-danger">PDF</span>
                                            {% else %}
                                                <span class="badge bg-info">{{ document.file_extension | safe_upper }}</span>
                                            {% endif %}
                                            <small class="text-muted d-block">{{ document.file_size_mb }} MB</small>
                                        </div>
                                    {% endif %}
                                </div>
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                </div>
                {% endif %}

                {% if not case_documents and not client_documents %}
                <div class="text-center py-4">
                    <h6 class="text-muted">لا توجد مستندات مرتبطة بهذه القضية</h6>
                    <p class="text-muted">يمكنك إضافة مستندات جديدة أو ربط مستندات العميل الموجودة</p>
                    <a href="/client_documents/{{ case.client_id }}?case_id={{ case.id }}" class="btn btn-success">إضافة مستند جديد</a>
                </div>
                {% endif %}
            </div>
        </div>
    </div>

    <!-- Bootstrap JS for dropdown -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
    ''', case=case, case_appointments=case_appointments, case_invoices=case_invoices,
         case_documents=case_documents, client_documents=client_documents,
         total_invoices_amount=total_invoices_amount, total_paid_amount=total_paid_amount,
         total_remaining_amount=total_remaining_amount)

@app.route('/edit_case/<int:case_id>', methods=['GET', 'POST'])
@login_required
def edit_case(case_id):
    case = Case.query.get_or_404(case_id)

    if request.method == 'POST':
        case.case_number = request.form['case_number']
        case.title = request.form['title']
        case.case_type = request.form['case_type']
        case.status = request.form['status']
        case.description = request.form.get('description')
        case.court_name = request.form.get('court_name')
        case.judge_name = request.form.get('judge_name')
        case.client_id = request.form['client_id']

        # معالجة تاريخ الجلسة القادمة
        if request.form.get('next_hearing_date'):
            case.next_hearing_date = datetime.strptime(
                request.form['next_hearing_date'], '%Y-%m-%dT%H:%M'
            )
        else:
            case.next_hearing_date = None

        db.session.commit()
        flash(f'تم تحديث القضية {case.case_number} بنجاح', 'success')
        return redirect(url_for('view_case', case_id=case_id))

    clients = Client.query.all()
    return render_template_string('''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="utf-8">
    <title>تعديل القضية</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/">🏛️ المحامي فالح بن عقاب آل عيسى</a>
            <div>
                <a class="btn btn-outline-light btn-sm" href="/view_case/{{ case.id }}">عرض القضية</a>
                <a class="btn btn-outline-light btn-sm ms-2" href="/cases">القضايا</a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="card">
            <div class="card-header bg-warning text-dark">
                <h3>✏️ تعديل القضية: {{ case.case_number }}</h3>
            </div>
            <div class="card-body">
                <form method="POST">
                    <div class="row">
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label class="form-label">رقم القضية *</label>
                                <input type="text" class="form-control" name="case_number" value="{{ case.case_number }}" required>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label class="form-label">العميل *</label>
                                <select class="form-control" name="client_id" required>
                                    {% for client in clients %}
                                    <option value="{{ client.id }}" {{ 'selected' if client.id == case.client_id else '' }}>{{ client.full_name }}</option>
                                    {% endfor %}
                                </select>
                            </div>
                        </div>
                    </div>

                    <div class="mb-3">
                        <label class="form-label">عنوان القضية *</label>
                        <input type="text" class="form-control" name="title" value="{{ case.title }}" required>
                    </div>

                    <div class="row">
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label class="form-label">نوع القضية *</label>
                                <select class="form-control" name="case_type" required>
                                    <option value="مدنية" {{ 'selected' if case.case_type == 'مدنية' else '' }}>مدنية</option>
                                    <option value="تجارية" {{ 'selected' if case.case_type == 'تجارية' else '' }}>تجارية</option>
                                    <option value="جنائية" {{ 'selected' if case.case_type == 'جنائية' else '' }}>جنائية</option>
                                    <option value="عمالية" {{ 'selected' if case.case_type == 'عمالية' else '' }}>عمالية</option>
                                    <option value="أحوال شخصية" {{ 'selected' if case.case_type == 'أحوال شخصية' else '' }}>أحوال شخصية</option>
                                    <option value="إدارية" {{ 'selected' if case.case_type == 'إدارية' else '' }}>إدارية</option>
                                    <option value="أخرى" {{ 'selected' if case.case_type == 'أخرى' else '' }}>أخرى</option>
                                </select>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label class="form-label">حالة القضية *</label>
                                <select class="form-control" name="status" required>
                                    <option value="active" {{ 'selected' if case.status == 'active' else '' }}>نشطة</option>
                                    <option value="pending" {{ 'selected' if case.status == 'pending' else '' }}>معلقة</option>
                                    <option value="closed" {{ 'selected' if case.status == 'closed' else '' }}>مغلقة</option>
                                    <option value="cancelled" {{ 'selected' if case.status == 'cancelled' else '' }}>ملغية</option>
                                </select>
                            </div>
                        </div>
                    </div>

                    <div class="mb-3">
                        <label class="form-label">الجلسة القادمة</label>
                        <input type="datetime-local" class="form-control" name="next_hearing_date"
                               value="{{ case.next_hearing_date.strftime('%Y-%m-%dT%H:%M') if case.next_hearing_date else '' }}">
                    </div>

                    <div class="row">
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label class="form-label">اسم المحكمة</label>
                                <input type="text" class="form-control" name="court_name" value="{{ case.court_name or '' }}">
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label class="form-label">اسم القاضي</label>
                                <input type="text" class="form-control" name="judge_name" value="{{ case.judge_name or '' }}">
                            </div>
                        </div>
                    </div>

                    <div class="mb-3">
                        <label class="form-label">وصف القضية</label>
                        <textarea class="form-control" name="description" rows="4">{{ case.description or '' }}</textarea>
                    </div>

                    <div class="text-center">
                        <button type="submit" class="btn btn-warning btn-lg">💾 حفظ التعديلات</button>
                        <a href="/view_case/{{ case.id }}" class="btn btn-secondary btn-lg ms-2">❌ إلغاء</a>
                    </div>
                </form>
            </div>
        </div>
    </div>
</body>
</html>
    ''', case=case, clients=clients)

@app.route('/delete_case/<int:case_id>')
@login_required
def delete_case(case_id):
    case = Case.query.get_or_404(case_id)
    case_number = case.case_number

    try:
        # حذف جميع البيانات المرتبطة بالقضية بالترتيب الصحيح

        # 1. حذف ملفات المستندات من النظام
        documents = ClientDocument.query.filter_by(case_id=case_id).all()
        for doc in documents:
            if doc.filename:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], doc.filename)
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except OSError:
                        pass

        # 2. حذف المستندات من قاعدة البيانات
        ClientDocument.query.filter_by(case_id=case_id).delete()

        # 3. حذف الفواتير والدفعات المرتبطة بالقضية
        invoices = Invoice.query.filter_by(case_id=case_id).all()
        for invoice in invoices:
            InvoicePayment.query.filter_by(invoice_id=invoice.id).delete()
        Invoice.query.filter_by(case_id=case_id).delete()

        # 4. حذف المواعيد المرتبطة بالقضية
        Appointment.query.filter_by(case_id=case_id).delete()

        # 5. حذف القضية
        db.session.delete(case)
        db.session.commit()

        flash(f'تم حذف القضية {case_number} وجميع بياناتها المرتبطة بنجاح', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء حذف القضية: {str(e)}', 'error')

    return redirect(url_for('cases'))

@app.route('/add_client', methods=['GET', 'POST'])
@login_required
def add_client():
    if request.method == 'POST':
        client = Client(
            first_name=request.form['first_name'],
            last_name=request.form['last_name'],
            national_id=request.form.get('national_id'),
            phone=request.form.get('phone'),
            email=request.form.get('email'),
            address=request.form.get('address')
        )
        db.session.add(client)
        db.session.flush()

        documents_added = 0
        document_types = [
            ('identity', 'الهوية الشخصية'),
            ('power_of_attorney', 'الوكالة'),
            ('contract', 'العقد'),
            ('other', 'مستندات أخرى')
        ]

        for doc_type, doc_name in document_types:
            desc_field = f'{doc_type}_desc'
            file_field = f'{doc_type}_file'

            # التحقق من وجود وصف أو ملف
            has_description = desc_field in request.form and request.form[desc_field].strip()
            has_file = file_field in request.files and request.files[file_field].filename != ''

            if has_description or has_file:
                doc = ClientDocument(
                    document_type=doc_type,
                    description=request.form.get(desc_field, ''),
                    client_id=client.id,
                    case_id=request.form.get('case_id') if request.form.get('case_id') else None
                )

                # معالجة الملف المرفوع
                if has_file:
                    file = request.files[file_field]
                    if file and allowed_file(file.filename):
                        # إنشاء اسم ملف آمن مع timestamp
                        filename = safe_filename_with_timestamp(file.filename)

                        # حفظ الملف
                        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        file.save(file_path)

                        # حفظ معلومات الملف في قاعدة البيانات
                        doc.filename = filename
                        doc.original_filename = file.filename
                        doc.file_size = os.path.getsize(file_path)

                db.session.add(doc)
                documents_added += 1

        db.session.commit()
        flash(f'تم إضافة العميل {client.full_name} بنجاح مع {documents_added} مستندات', 'success')
        return redirect(url_for('clients'))

    return render_template_string('''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="utf-8">
    <title>إضافة عميل جديد</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/">🏛️ المحامي فالح بن عقاب آل عيسى</a>
            <div>
                <a class="btn btn-outline-light btn-sm" href="/clients">العملاء</a>
                <a class="btn btn-outline-light btn-sm ms-2" href="/">الرئيسية</a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="card">
            <div class="card-header bg-success text-white">
                <h3>➕ إضافة عميل جديد مع المستندات</h3>
            </div>
            <div class="card-body">
                <form method="POST" enctype="multipart/form-data">
                    <div class="card mb-3">
                        <div class="card-header bg-primary text-white">
                            <h5>👤 البيانات الأساسية</h5>
                        </div>
                        <div class="card-body">
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">الاسم الأول *</label>
                                        <input type="text" class="form-control" name="first_name" required>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">اسم العائلة *</label>
                                        <input type="text" class="form-control" name="last_name" required>
                                    </div>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">🆔 رقم الهوية الوطنية</label>
                                        <input type="text" class="form-control" name="national_id" placeholder="مثال: 1234567890">
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">📱 رقم الهاتف</label>
                                        <input type="text" class="form-control" name="phone" placeholder="مثال: 0501234567">
                                    </div>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">📧 البريد الإلكتروني</label>
                                        <input type="email" class="form-control" name="email" placeholder="مثال: client@email.com">
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">🏠 العنوان</label>
                                        <input type="text" class="form-control" name="address" placeholder="العنوان الكامل">
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="card mb-3">
                        <div class="card-header bg-success text-white">
                            <h5>📄 المستندات والوثائق (اختياري)</h5>
                        </div>
                        <div class="card-body">
                            <div class="alert alert-info">
                                <strong>💡 ملاحظة:</strong> يمكنك إضافة وصف و/أو رفع ملف لكل مستند
                                <br><small>الملفات المدعومة: PDF, صور (PNG, JPG, JPEG, GIF), Word (DOC, DOCX)</small>
                            </div>

                            <!-- الهوية الشخصية -->
                            <div class="card mb-3 border-info">
                                <div class="card-header bg-info text-white">
                                    <h6 class="mb-0">🆔 الهوية الشخصية</h6>
                                </div>
                                <div class="card-body">
                                    <div class="mb-3">
                                        <label class="form-label">وصف المستند</label>
                                        <input type="text" class="form-control" name="identity_desc" placeholder="مثال: هوية وطنية رقم 1234567890">
                                    </div>
                                    <div class="mb-3">
                                        <label class="form-label">رفع ملف الهوية</label>
                                        <input type="file" class="form-control" name="identity_file" accept=".pdf,.png,.jpg,.jpeg,.gif,.doc,.docx">
                                        <small class="text-muted">اختر صورة أو ملف PDF للهوية الشخصية</small>
                                    </div>
                                </div>
                            </div>

                            <!-- الوكالة -->
                            <div class="card mb-3 border-warning">
                                <div class="card-header bg-warning text-dark">
                                    <h6 class="mb-0">📋 الوكالة</h6>
                                </div>
                                <div class="card-body">
                                    <div class="mb-3">
                                        <label class="form-label">وصف المستند</label>
                                        <input type="text" class="form-control" name="power_of_attorney_desc" placeholder="مثال: وكالة عامة مؤرخة 2025/01/15">
                                    </div>
                                    <div class="mb-3">
                                        <label class="form-label">رفع ملف الوكالة</label>
                                        <input type="file" class="form-control" name="power_of_attorney_file" accept=".pdf,.png,.jpg,.jpeg,.gif,.doc,.docx">
                                        <small class="text-muted">اختر صورة أو ملف PDF للوكالة</small>
                                    </div>
                                </div>
                            </div>

                            <!-- العقد -->
                            <div class="card mb-3 border-success">
                                <div class="card-header bg-success text-white">
                                    <h6 class="mb-0">📄 العقد</h6>
                                </div>
                                <div class="card-body">
                                    <div class="mb-3">
                                        <label class="form-label">وصف المستند</label>
                                        <input type="text" class="form-control" name="contract_desc" placeholder="مثال: عقد استشارة قانونية">
                                    </div>
                                    <div class="mb-3">
                                        <label class="form-label">رفع ملف العقد</label>
                                        <input type="file" class="form-control" name="contract_file" accept=".pdf,.png,.jpg,.jpeg,.gif,.doc,.docx">
                                        <small class="text-muted">اختر صورة أو ملف PDF للعقد</small>
                                    </div>
                                </div>
                            </div>

                            <!-- مستندات أخرى -->
                            <div class="card mb-3 border-secondary">
                                <div class="card-header bg-secondary text-white">
                                    <h6 class="mb-0">📎 مستندات أخرى</h6>
                                </div>
                                <div class="card-body">
                                    <div class="mb-3">
                                        <label class="form-label">وصف المستند</label>
                                        <input type="text" class="form-control" name="other_desc" placeholder="مثال: شهادات، تقارير، مراسلات">
                                    </div>
                                    <div class="mb-3">
                                        <label class="form-label">رفع الملف</label>
                                        <input type="file" class="form-control" name="other_file" accept=".pdf,.png,.jpg,.jpeg,.gif,.doc,.docx">
                                        <small class="text-muted">اختر أي ملف مدعوم</small>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="text-center">
                        <button type="submit" class="btn btn-success btn-lg">💾 حفظ العميل والمستندات</button>
                        <a href="/clients" class="btn btn-secondary btn-lg ms-2">❌ إلغاء</a>
                    </div>
                </form>
            </div>
        </div>
    </div>
</body>
</html>
    ''')

@app.route('/client_documents/<int:client_id>')
def client_documents(client_id):
    client = Client.query.get_or_404(client_id)
    documents = ClientDocument.query.filter_by(client_id=client_id).all()

    # التحقق من وجود case_id في الرابط
    preselected_case_id = request.args.get('case_id', type=int)
    case = None
    if preselected_case_id:
        case = Case.query.get(preselected_case_id)
        if case and case.client_id != client_id:
            case = None  # إذا كانت القضية لا تخص هذا العميل

    return render_template_string('''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="utf-8">
    <title>مستندات العميل</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/">🏛️ المحامي فالح بن عقاب آل عيسى</a>
            <div>
                <a class="btn btn-outline-light btn-sm" href="/clients">العملاء</a>
                <a class="btn btn-outline-light btn-sm ms-2" href="/">الرئيسية</a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="card">
            <div class="card-header d-flex justify-content-between align-items-center">
                <h3>📄 مستندات العميل: {{ client.full_name }}</h3>
                {% if case %}
                    <div class="alert alert-info mb-0 py-2">
                        <small>📁 سيتم ربط المستندات الجديدة بالقضية: <strong>{{ case.case_number }}</strong></small>
                    </div>
                {% endif %}
            </div>
            <div class="card-body">
                {% if documents %}
                <div class="row">
                    {% for doc in documents %}
                    <div class="col-md-6 mb-3">
                        <div class="card border-primary">
                            <div class="card-body">
                                <h6>
                                    {% if doc.document_type == 'identity' %}
                                        🆔 الهوية الشخصية
                                    {% elif doc.document_type == 'power_of_attorney' %}
                                        📋 الوكالة
                                    {% elif doc.document_type == 'contract' %}
                                        📄 العقد
                                    {% else %}
                                        📎 مستند آخر
                                    {% endif %}
                                </h6>

                                {% if doc.description %}
                                    <p><strong>الوصف:</strong> {{ doc.description }}</p>
                                {% endif %}

                                {% if doc.case %}
                                    <div class="alert alert-info py-2">
                                        <small><strong>📁 مرتبط بالقضية:</strong>
                                            <a href="/view_case/{{ doc.case.id }}" class="text-decoration-none">{{ doc.case.case_number }}</a>
                                        </small>
                                    </div>
                                {% endif %}

                                {% if doc.filename %}
                                    <div class="mb-2">
                                        <strong>الملف المرفق:</strong>
                                        <br>
                                        <span class="badge bg-info">{{ doc.original_filename }}</span>
                                        <span class="badge bg-secondary">{{ doc.file_size_mb }} MB</span>
                                    </div>

                                    {% if doc.is_image %}
                                        <div class="mb-2 text-center">
                                            <img src="/documents/{{ doc.id }}/view"
                                                 class="img-thumbnail"
                                                 style="max-width: 200px; max-height: 150px; cursor: pointer; border: 2px solid #007bff;"
                                                 alt="معاينة {{ doc.original_filename }}"
                                                 onclick="showQuickPreview({{ doc.id }}, '{{ (doc.original_filename or doc.filename)|replace("'", "\\'") }}')"
                                                 onerror="this.style.display='none'; this.nextElementSibling.style.display='block';"
                                                 title="انقر للمعاينة الكاملة">
                                            <div style="display: none; padding: 10px; background: #f8f9fa; border-radius: 4px; border: 1px dashed #ccc;">
                                                <i class="fas fa-image text-muted" style="font-size: 2em;"></i>
                                                <br><small class="text-muted">لا يمكن عرض الصورة</small>
                                            </div>
                                        </div>
                                    {% elif doc.is_pdf %}
                                        <div class="mb-2 text-center">
                                            <div style="position: relative; display: inline-block; cursor: pointer; border: 2px solid #dc3545; border-radius: 8px; padding: 10px; background: #fff;"
                                                 onclick="showQuickPreview({{ doc.id }}, '{{ (doc.original_filename or doc.filename)|replace("'", "\\'") }}')"
                                                 title="انقر للمعاينة الكاملة">
                                                <i class="fas fa-file-pdf text-danger" style="font-size: 3em;"></i>
                                                <div style="position: absolute; top: 5px; right: 5px; background: rgba(220, 53, 69, 0.8); color: white; border-radius: 50%; width: 20px; height: 20px; display: flex; align-items: center; justify-content: center; font-size: 10px;">
                                                    👁️
                                                </div>
                                                <br><small class="text-muted">ملف PDF</small>
                                            </div>
                                        </div>
                                    {% elif doc.is_word %}
                                        <div class="mb-2">
                                            <i class="fas fa-file-word text-primary" style="font-size: 2em;"></i>
                                            <span class="ms-2">مستند Word</span>
                                            <small class="text-muted d-block">سيتم تحميل الملف عند الضغط على "عرض"</small>
                                        </div>
                                    {% elif doc.is_excel %}
                                        <div class="mb-2">
                                            <i class="fas fa-file-excel text-success" style="font-size: 2em;"></i>
                                            <span class="ms-2">جدول Excel</span>
                                            <small class="text-muted d-block">سيتم تحميل الملف عند الضغط على "عرض"</small>
                                        </div>
                                    {% elif doc.is_powerpoint %}
                                        <div class="mb-2">
                                            <i class="fas fa-file-powerpoint text-warning" style="font-size: 2em;"></i>
                                            <span class="ms-2">عرض PowerPoint</span>
                                            <small class="text-muted d-block">سيتم تحميل الملف عند الضغط على "عرض"</small>
                                        </div>
                                    {% else %}
                                        <div class="mb-2">
                                            <i class="fas fa-file text-secondary" style="font-size: 2em;"></i>
                                            <span class="ms-2">ملف مستند</span>
                                            <small class="text-muted d-block">سيتم تحميل الملف عند الضغط على "عرض"</small>
                                        </div>
                                    {% endif %}

                                    <div class="btn-group" role="group">
                                        {% if doc.filename %}
                                            <button onclick="showQuickPreview({{ doc.id }}, '{{ (doc.original_filename or doc.filename)|replace("'", "\\'") }}')" class="btn btn-sm btn-primary" title="معاينة سريعة">
                                                👁️ معاينة
                                            </button>
                                            <button onclick="window.open('/documents/{{ doc.id }}/view', '_blank')" class="btn btn-sm btn-outline-primary" title="معاينة في نافذة جديدة" style="display: none;" id="fallback-{{ doc.id }}">
                                                🔗 معاينة
                                            </button>
                                            <a href="/documents/{{ doc.id }}/download" class="btn btn-sm btn-success">
                                                📥 تحميل
                                            </a>
                                        {% else %}
                                            <span class="btn btn-sm btn-secondary disabled">لا يوجد ملف</span>
                                        {% endif %}
                                    </div>
                                {% else %}
                                    <p class="text-muted">لا يوجد ملف مرفق</p>
                                {% endif %}

                                <hr>
                                <small class="text-muted">تاريخ الإضافة: {{ doc.created_at.strftime('%Y-%m-%d %H:%M') }}</small>
                            </div>
                        </div>
                    </div>
                    {% endfor %}
                </div>
                {% else %}
                <div class="text-center py-5">
                    <h5>📄 لا توجد مستندات لهذا العميل</h5>
                </div>
                {% endif %}

                <a href="/clients" class="btn btn-secondary">← العودة للعملاء</a>
            </div>
        </div>
    </div>

    <!-- Modal للمعاينة السريعة -->
    <div class="modal fade" id="quickPreviewModal" tabindex="-1" aria-labelledby="quickPreviewModalLabel" aria-hidden="true">
        <div class="modal-dialog modal-lg modal-dialog-centered">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="quickPreviewModalLabel">معاينة سريعة</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body text-center" id="previewContent">
                    <div class="spinner-border" role="status">
                        <span class="visually-hidden">جاري التحميل...</span>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">إغلاق</button>
                    <a href="#" id="downloadBtn" class="btn btn-success">📥 تحميل</a>
                </div>
            </div>
        </div>
    </div>

    <script>
    function showQuickPreview(docId, filename) {
        try {
            console.log('showQuickPreview called with:', docId, filename);

            // التحقق من وجود Bootstrap - إذا لم يكن متاحاً، استخدم modal بسيط
            if (typeof bootstrap === 'undefined') {
                console.log('Bootstrap غير متاح، استخدام modal بسيط');
                showSimplePreview(docId, filename);
                return;
            }

            // التحقق من وجود المودال
            const modalElement = document.getElementById('quickPreviewModal');
            if (!modalElement) {
                alert('خطأ: المودال غير موجود');
                return;
            }

            // إظهار المودال
            const modal = new bootstrap.Modal(modalElement);
            const previewContent = document.getElementById('previewContent');
            const downloadBtn = document.getElementById('downloadBtn');
            const modalTitle = document.getElementById('quickPreviewModalLabel');

            // تحديث العنوان
            modalTitle.textContent = 'معاينة: ' + filename;

            // تحديث رابط التحميل
            downloadBtn.href = '/documents/' + docId + '/download';

            // إظهار loading
            previewContent.innerHTML = `
                <div class="spinner-border" role="status">
                    <span class="visually-hidden">جاري التحميل...</span>
                </div>
            `;

            modal.show();

            // تحديد نوع الملف من الامتداد
            const extension = filename.split('.').pop().toLowerCase();

        if (['jpg', 'jpeg', 'png', 'gif'].includes(extension)) {
            // للصور - استخدام route التحميل مباشرة (حل مؤقت)
            setTimeout(() => {
                previewContent.innerHTML = `
                    <div class="text-center">
                        <div class="alert alert-info mb-3">
                            <i class="fas fa-info-circle"></i> جاري تحميل الصورة...
                        </div>
                        <img src="/documents/${docId}/download"
                             class="img-fluid"
                             style="max-height: 400px; max-width: 100%; border: 1px solid #ddd; border-radius: 5px;"
                             alt="${filename}"
                             onload="console.log('Image loaded successfully'); this.previousElementSibling.style.display='none';"
                             onerror="console.error('Image failed to load'); this.style.display='none'; this.nextElementSibling.style.display='block';">
                        <div class="alert alert-warning" style="display: none;">
                            <i class="fas fa-exclamation-triangle"></i>
                            لا يمكن عرض الصورة.
                            <a href="/documents/${docId}/download" class="btn btn-sm btn-primary ms-2">
                                <i class="fas fa-download"></i> تحميل الملف
                            </a>
                        </div>
                        <div class="mt-2">
                            <small class="text-muted">اسم الملف: ${filename}</small>
                        </div>
                    </div>
                `;
            }, 500);
        } else if (extension === 'pdf') {
            // لملفات PDF
            setTimeout(() => {
                previewContent.innerHTML = `
                    <div class="text-center">
                        <iframe src="/documents/${docId}/download"
                                width="100%"
                                height="400px"
                                style="border: 1px solid #ddd; border-radius: 5px;"
                                onload="console.log('PDF loaded successfully')"
                                onerror="console.error('PDF failed to load')">
                            <p>متصفحك لا يدعم عرض ملفات PDF.
                               <a href="/documents/${docId}/download">انقر هنا لتحميل الملف</a>
                            </p>
                        </iframe>
                        <div class="mt-2">
                            <a href="/documents/${docId}/download" class="btn btn-primary btn-sm" target="_blank">
                                <i class="fas fa-external-link-alt"></i> فتح في نافذة جديدة
                            </a>
                        </div>
                        <div class="mt-2">
                            <small class="text-muted">اسم الملف: ${filename}</small>
                        </div>
                    </div>
                `;
            }, 500);
        } else {
            // للملفات الأخرى
            setTimeout(() => {
                previewContent.innerHTML = `
                    <div class="alert alert-info text-center">
                        <i class="fas fa-file-alt fa-3x mb-3"></i>
                        <h5>معاينة غير متاحة</h5>
                        <p>لا يمكن معاينة هذا النوع من الملفات في المتصفح</p>
                        <p><strong>اسم الملف:</strong> ${filename}</p>
                        <p><strong>نوع الملف:</strong> ${extension.toUpperCase()}</p>
                        <a href="/documents/${docId}/download" class="btn btn-primary mt-2">
                            <i class="fas fa-download me-2"></i>تحميل الملف
                        </a>
                    </div>
                `;
            }, 300);
        }
        } catch (error) {
            console.error('خطأ في showQuickPreview:', error);
            alert('حدث خطأ في عرض المعاينة: ' + error.message);
        }
    }

    // دالة معاينة بسيطة بدون Bootstrap
    function showSimplePreview(docId, filename) {
        try {
            // إنشاء overlay
            const overlay = document.createElement('div');
            overlay.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.8);
                z-index: 9999;
                display: flex;
                justify-content: center;
                align-items: center;
                cursor: pointer;
            `;

            // إنشاء محتوى المعاينة
            const content = document.createElement('div');
            content.style.cssText = `
                background: white;
                border-radius: 8px;
                padding: 20px;
                max-width: 90%;
                max-height: 90%;
                overflow: auto;
                position: relative;
                cursor: default;
                direction: rtl;
                text-align: center;
            `;

            // زر الإغلاق
            const closeBtn = document.createElement('button');
            closeBtn.innerHTML = '×';
            closeBtn.style.cssText = `
                position: absolute;
                top: 10px;
                left: 15px;
                background: none;
                border: none;
                font-size: 24px;
                cursor: pointer;
                color: #666;
                width: 30px;
                height: 30px;
                display: flex;
                align-items: center;
                justify-content: center;
            `;

            // محتوى الملف
            const fileContent = document.createElement('div');
            fileContent.style.cssText = `
                text-align: center;
                padding: 20px;
                min-height: 200px;
            `;

            // عرض loading أولاً
            fileContent.innerHTML = '<div style="padding: 40px;"><p>جاري التحميل...</p></div>';

            // تحديد نوع الملف وعرضه
            const fileExt = filename.split('.').pop().toLowerCase();

            setTimeout(() => {
                if (['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'].includes(fileExt)) {
                    const img = document.createElement('img');
                    // استخدام رابط المستند بدلاً من اسم الملف مباشرة
                    img.src = '/documents/' + docId + '/view';
                    img.style.cssText = 'max-width: 100%; max-height: 70vh; border-radius: 4px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);';
                    img.onload = function() {
                        fileContent.innerHTML = '';
                        fileContent.appendChild(img);
                    };
                    img.onerror = function() {
                        // إذا فشل الرابط الأول، جرب الرابط البديل
                        img.src = '/simple_file/' + filename;
                        img.onerror = function() {
                            fileContent.innerHTML = `
                                <div style="padding: 40px; color: #dc3545;">
                                    <h4>⚠️ خطأ في تحميل الصورة</h4>
                                    <p>اسم الملف: ${filename}</p>
                                    <div style="margin-top: 20px;">
                                        <a href="/documents/${docId}/download" target="_blank"
                                           style="display: inline-block; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 4px; margin: 10px;">
                                            فتح في نافذة جديدة
                                        </a>
                                        <a href="/documents/${docId}/download" download
                                           style="display: inline-block; padding: 10px 20px; background: #28a745; color: white; text-decoration: none; border-radius: 4px; margin: 10px;">
                                            تحميل الملف
                                        </a>
                                    </div>
                                </div>
                            `;
                        };
                    };
                } else if (fileExt === 'pdf') {
                    fileContent.innerHTML = `
                        <div style="padding: 20px;">
                            <iframe src="/documents/${docId}/view"
                                    style="width: 80vw; height: 70vh; border: 1px solid #ddd; border-radius: 4px;"
                                    onload="console.log('PDF loaded')"
                                    onerror="this.style.display='none'; this.nextElementSibling.style.display='block';">
                            </iframe>
                            <div style="display: none; padding: 40px; color: #dc3545;">
                                <h4>⚠️ لا يمكن عرض ملف PDF</h4>
                                <p>اسم الملف: ${filename}</p>
                                <div style="margin-top: 20px;">
                                    <a href="/documents/${docId}/download" target="_blank"
                                       style="display: inline-block; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 4px; margin: 10px;">
                                        فتح في نافذة جديدة
                                    </a>
                                    <a href="/documents/${docId}/download" download
                                       style="display: inline-block; padding: 10px 20px; background: #28a745; color: white; text-decoration: none; border-radius: 4px; margin: 10px;">
                                        تحميل الملف
                                    </a>
                                </div>
                            </div>
                        </div>
                    `;
                } else {
                    fileContent.innerHTML = `
                        <div style="padding: 40px;">
                            <h4>📄 معاينة الملف</h4>
                            <p><strong>اسم الملف:</strong> ${filename}</p>
                            <p><strong>نوع الملف:</strong> ${fileExt.toUpperCase()}</p>
                            <div style="margin-top: 20px;">
                                <a href="/documents/${docId}/download" target="_blank"
                                   style="display: inline-block; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 4px; margin: 10px;">
                                    فتح الملف
                                </a>
                                <a href="/documents/${docId}/download" download
                                   style="display: inline-block; padding: 10px 20px; background: #28a745; color: white; text-decoration: none; border-radius: 4px; margin: 10px;">
                                    تحميل الملف
                                </a>
                            </div>
                        </div>
                    `;
                }
            }, 300);

            // تجميع العناصر
            content.appendChild(closeBtn);
            content.appendChild(fileContent);
            overlay.appendChild(content);
            document.body.appendChild(overlay);

            // إغلاق عند النقر على الخلفية
            overlay.addEventListener('click', function(e) {
                if (e.target === overlay) {
                    document.body.removeChild(overlay);
                }
            });

            // إغلاق عند النقر على زر الإغلاق
            closeBtn.addEventListener('click', function() {
                document.body.removeChild(overlay);
            });

            // إغلاق بمفتاح Escape
            const escapeHandler = function(e) {
                if (e.key === 'Escape') {
                    if (document.body.contains(overlay)) {
                        document.body.removeChild(overlay);
                        document.removeEventListener('keydown', escapeHandler);
                    }
                }
            };
            document.addEventListener('keydown', escapeHandler);

        } catch (error) {
            console.error('خطأ في showSimplePreview:', error);
            // fallback: فتح في نافذة جديدة
            window.open('/simple_file/' + filename, '_blank');
        }
    }
    </script>
</body>
</html>
    ''', client=client, documents=documents, case=case)

@app.route('/documents/<int:document_id>')
@login_required
def documents_view(document_id):
    """عرض تفاصيل المستند"""
    document = ClientDocument.query.get_or_404(document_id)

    # تحديد نوع الملف
    if document.filename:
        file_extension = document.filename.split('.')[-1].lower()
    else:
        file_extension = 'unknown'

    return render_template_string('''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ document.original_filename or document.filename }}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        .document-header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
        .file-icon { font-size: 3rem; margin-bottom: 1rem; }
        .preview-container { max-height: 600px; overflow: auto; }
    </style>
</head>
<body>
    <div class="document-header py-4">
        <div class="container">
            <div class="row align-items-center">
                <div class="col-md-8">
                    <h1 class="mb-0">
                        <i class="fas fa-file-{{ 'pdf' if file_extension == 'pdf' else 'image' if file_extension in ['jpg', 'jpeg', 'png', 'gif'] else 'word' if file_extension in ['doc', 'docx'] else 'alt' }} me-2"></i>
                        {{ document.original_filename or document.filename }}
                    </h1>
                    <p class="mb-0 opacity-75">العميل: {{ document.client.full_name }}</p>
                </div>
                <div class="col-md-4 text-end">
                    <a href="{{ url_for('documents_download', document_id=document.id) }}" class="btn btn-light btn-lg">
                        <i class="fas fa-download me-2"></i>تحميل الملف
                    </a>
                </div>
            </div>
        </div>
    </div>

    <div class="container mt-4">
        <div class="row">
            <div class="col-md-8">
                <div class="card">
                    <div class="card-header">
                        <h5 class="mb-0">معاينة المستند</h5>
                    </div>
                    <div class="card-body preview-container">
                        {% if file_extension == 'pdf' %}
                            <div class="text-center">
                                <iframe src="/documents/{{ document.id }}/view"
                                        width="100%" height="500px"
                                        style="border: 1px solid #ddd;">
                                    <p>متصفحك لا يدعم عرض ملفات PDF.
                                       <a href="/documents/{{ document.id }}/download">انقر هنا لتحميل الملف</a>
                                    </p>
                                </iframe>
                            </div>
                        {% elif file_extension in ['jpg', 'jpeg', 'png', 'gif'] %}
                            <div class="text-center">
                                <img src="/documents/{{ document.id }}/view"
                                     class="img-fluid"
                                     alt="{{ document.original_filename or document.filename }}"
                                     style="max-height: 500px;">
                            </div>
                        {% else %}
                            <div class="text-center py-5">
                                <div class="file-icon text-muted">
                                    <i class="fas fa-file-{{ 'word' if file_extension in ['doc', 'docx'] else 'excel' if file_extension in ['xls', 'xlsx'] else 'alt' }}"></i>
                                </div>
                                <h5 class="text-muted">معاينة غير متاحة</h5>
                                <p class="text-muted">لا يمكن معاينة هذا النوع من الملفات في المتصفح</p>
                                <a href="/documents/{{ document.id }}/download" class="btn btn-primary">
                                    <i class="fas fa-download me-2"></i>تحميل الملف
                                </a>
                            </div>
                        {% endif %}
                    </div>
                </div>
            </div>

            <div class="col-md-4">
                <div class="card">
                    <div class="card-header">
                        <h6 class="mb-0">معلومات المستند</h6>
                    </div>
                    <div class="card-body">
                        <table class="table table-sm">
                            <tr>
                                <td><strong>اسم الملف:</strong></td>
                                <td>{{ document.original_filename or document.filename }}</td>
                            </tr>
                            <tr>
                                <td><strong>النوع:</strong></td>
                                <td>
                                    {% if document.document_type == 'identity' %}
                                        🆔 الهوية الشخصية
                                    {% elif document.document_type == 'power_of_attorney' %}
                                        📋 الوكالة
                                    {% elif document.document_type == 'contract' %}
                                        📄 العقد
                                    {% else %}
                                        📎 مستند آخر
                                    {% endif %}
                                </td>
                            </tr>
                            <tr>
                                <td><strong>العميل:</strong></td>
                                <td>{{ document.client.full_name }}</td>
                            </tr>
                            <tr>
                                <td><strong>تاريخ الرفع:</strong></td>
                                <td>{{ document.created_at.strftime('%Y-%m-%d %H:%M') }}</td>
                            </tr>
                            {% if document.description %}
                            <tr>
                                <td><strong>الوصف:</strong></td>
                                <td>{{ document.description }}</td>
                            </tr>
                            {% endif %}
                        </table>
                    </div>
                </div>

                <div class="card mt-3">
                    <div class="card-header">
                        <h6 class="mb-0">إجراءات</h6>
                    </div>
                    <div class="card-body">
                        <div class="d-grid gap-2">
                            <a href="{{ url_for('documents_download', document_id=document.id) }}" class="btn btn-success">
                                <i class="fas fa-download me-2"></i>تحميل الملف
                            </a>
                            <a href="{{ url_for('client_details', client_id=document.client_id) }}" class="btn btn-outline-primary">
                                <i class="fas fa-user me-2"></i>عرض العميل
                            </a>
                            <a href="javascript:history.back()" class="btn btn-outline-secondary">
                                <i class="fas fa-arrow-right me-2"></i>العودة
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
    ''', document=document, file_extension=file_extension)

@app.route('/documents')
def documents_index():
    """قائمة جميع المستندات"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    document_type = request.args.get('document_type', '', type=str)

    query = ClientDocument.query.join(Client)

    # تطبيق البحث
    if search:
        query = query.filter(
            db.or_(
                ClientDocument.original_filename.contains(search),
                ClientDocument.description.contains(search),
                Client.first_name.contains(search),
                Client.last_name.contains(search)
            )
        )

    # تطبيق فلتر نوع المستند
    if document_type:
        query = query.filter(ClientDocument.document_type == document_type)

    documents = query.order_by(ClientDocument.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False)

    # إرجاع صفحة بسيطة للاختبار
    return f"""
    <html dir="rtl">
    <head>
        <title>المستندات</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-4">
            <h1>إدارة المستندات</h1>
            <p>إجمالي المستندات: {documents.total}</p>
            <a href="/" class="btn btn-primary">العودة للرئيسية</a>

            <div class="row mt-4">
                {' '.join([f'''
                <div class="col-md-4 mb-3">
                    <div class="card">
                        <div class="card-body">
                            <h6>{doc.original_filename or doc.filename}</h6>
                            <p>العميل: {doc.client.full_name}</p>
                            <a href="/download/{doc.id}" class="btn btn-sm btn-success">تحميل</a>
                        </div>
                    </div>
                </div>
                ''' for doc in documents.items])}
            </div>
        </div>
    </body>
    </html>
    """



@app.route('/download/<int:doc_id>')
def download_document(doc_id):
    """تحميل مباشر للمستند"""
    try:
        document = ClientDocument.query.get_or_404(doc_id)
        upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')

        # البحث عن الملف
        file_path = os.path.join(upload_folder, document.filename)
        if not os.path.exists(file_path):
            file_path = os.path.join(upload_folder, 'documents', document.filename)

        if not os.path.exists(file_path):
            return f"<h3>File not found: {document.filename}</h3>", 404

        # استخدام send_file مع mimetype صحيح
        from flask import send_file
        import mimetypes

        # تحديد نوع الملف
        mimetype, _ = mimetypes.guess_type(file_path)
        if mimetype is None:
            mimetype = 'application/octet-stream'

        # استخدام الاسم الأصلي للملف
        download_name = document.original_filename or f"document_{doc_id}"

        return send_file(
            file_path,
            as_attachment=True,
            download_name=download_name,
            mimetype=mimetype
        )

    except Exception as e:
        return f"<h3>Error: {str(e)}</h3>", 500

@app.route('/test_download/<filename>')
def test_download(filename):
    """تحميل اختبار مباشر"""
    try:
        upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
        file_path = os.path.join(upload_folder, filename)

        if not os.path.exists(file_path):
            return f"File not found: {filename}", 404

        from flask import send_file
        return send_file(file_path, as_attachment=True, download_name=f"test_{filename}")

    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/create_test_file')
def create_test_file():
    """إنشاء ملف تجريبي للاختبار"""
    try:
        upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
        test_file_path = os.path.join(upload_folder, 'test_file.txt')

        # إنشاء ملف تجريبي
        with open(test_file_path, 'w', encoding='utf-8') as f:
            f.write('هذا ملف تجريبي لاختبار رفع الملفات\n')
            f.write('تم إنشاؤه على الخادم السحابي\n')
            f.write(f'التاريخ: {datetime.now()}\n')

        return f"تم إنشاء ملف تجريبي في: {test_file_path}"
    except Exception as e:
        return f"خطأ في إنشاء الملف: {str(e)}"

@app.route('/test_preview_route')
def test_preview_route():
    """اختبار route المعاينة"""
    try:
        # البحث عن أول مستند في قاعدة البيانات
        document = ClientDocument.query.first()
        if not document:
            return "لا توجد مستندات للاختبار"

        upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
        file_path = os.path.join(upload_folder, document.filename)
        file_exists = os.path.exists(file_path)

        return f"""
        <html dir="rtl">
        <head><title>اختبار المعاينة</title></head>
        <body style="font-family: Arial; padding: 20px;">
            <h2>اختبار route المعاينة</h2>
            <p><strong>المستند:</strong> {document.original_filename or document.filename}</p>
            <p><strong>ID:</strong> {document.id}</p>
            <p><strong>مجلد الرفع:</strong> {upload_folder}</p>
            <p><strong>مسار الملف:</strong> {file_path}</p>
            <p><strong>الملف موجود:</strong> {'نعم' if file_exists else 'لا'}</p>
            <hr>
            <p><strong>رابط المعاينة:</strong> <a href="/documents/{document.id}/view" target="_blank">/documents/{document.id}/view</a></p>
            <p><strong>رابط التحميل:</strong> <a href="/documents/{document.id}/download" target="_blank">/documents/{document.id}/download</a></p>
            <hr>
            <h3>اختبار المعاينة:</h3>
            <img src="/documents/{document.id}/view" style="max-width: 300px; border: 1px solid #ccc;"
                 onerror="this.style.display='none'; this.nextElementSibling.style.display='block';">
            <div style="display: none; padding: 20px; background: #f8f9fa; border: 1px solid #ccc;">
                لا يمكن عرض الصورة - قد يكون ملف PDF أو نوع آخر
            </div>
            <hr>
            <h3>اختبار المودال:</h3>
            <button onclick="testModal()" class="btn btn-primary">اختبار المودال</button>

            <script>
            function testModal() {{
                alert('سيتم اختبار المودال');
                // محاكاة نفس الكود
                console.log('Testing modal with ID: {document.id}');
            }}
            </script>
        </body>
        </html>
        """
    except Exception as e:
        return f"خطأ في الاختبار: {str(e)}"

@app.route('/simple_preview/<int:doc_id>')
def simple_preview(doc_id):
    """معاينة بسيطة بدون مودال"""
    try:
        print(f"🔍 Simple preview request for doc ID: {doc_id}")

        document = ClientDocument.query.get(doc_id)
        if not document:
            print(f"❌ Document not found: {doc_id}")
            return "المستند غير موجود", 404

        print(f"📄 Document found: {document.filename}")

        upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')

        # البحث في عدة مواقع
        possible_paths = [
            os.path.join(upload_folder, document.filename),
            os.path.join(upload_folder, 'documents', document.filename),
            os.path.join('uploads', document.filename),
            os.path.join('uploads', 'documents', document.filename),
        ]

        file_path = None
        for path in possible_paths:
            print(f"🔍 Checking: {path}")
            if os.path.exists(path):
                file_path = path
                print(f"✅ File found at: {path}")
                break

        if not file_path:
            print(f"❌ File not found in any location")
            # إنشاء صورة placeholder
            return f"""
            <svg width="300" height="200" xmlns="http://www.w3.org/2000/svg">
                <rect width="100%" height="100%" fill="#f8f9fa" stroke="#dee2e6"/>
                <text x="50%" y="50%" text-anchor="middle" dy=".3em" font-family="Arial" font-size="14" fill="#6c757d">
                    الملف غير موجود
                    <tspan x="50%" dy="1.2em">{document.filename}</tspan>
                </text>
            </svg>
            """, 404, {'Content-Type': 'image/svg+xml'}

        # إرسال الملف
        from flask import send_file
        import mimetypes

        mimetype, _ = mimetypes.guess_type(file_path)
        if mimetype is None:
            mimetype = 'application/octet-stream'

        print(f"📋 Sending file with mimetype: {mimetype}")

        return send_file(
            file_path,
            as_attachment=False,
            mimetype=mimetype
        )

    except Exception as e:
        print(f"❌ Error in simple preview: {str(e)}")
        import traceback
        traceback.print_exc()

        # إرجاع صورة خطأ
        return f"""
        <svg width="300" height="200" xmlns="http://www.w3.org/2000/svg">
            <rect width="100%" height="100%" fill="#f8d7da" stroke="#f5c6cb"/>
            <text x="50%" y="50%" text-anchor="middle" dy=".3em" font-family="Arial" font-size="14" fill="#721c24">
                خطأ في المعاينة
                <tspan x="50%" dy="1.2em">{str(e)[:50]}</tspan>
            </text>
        </svg>
        """, 500, {'Content-Type': 'image/svg+xml'}

@app.route('/check_files')
def check_files():
    """فحص جميع الملفات المرفوعة"""
    try:
        documents = ClientDocument.query.all()
        upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')

        results = []
        for doc in documents:
            possible_paths = [
                os.path.join(upload_folder, doc.filename),
                os.path.join(upload_folder, 'documents', doc.filename),
                os.path.join('uploads', doc.filename),
                os.path.join('uploads', 'documents', doc.filename),
            ]

            found_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    found_path = path
                    break

            results.append({
                'id': doc.id,
                'filename': doc.filename,
                'original_filename': doc.original_filename,
                'found': found_path is not None,
                'path': found_path,
                'client_id': doc.client_id
            })

        html = """
        <html dir="rtl">
        <head>
            <title>فحص الملفات</title>
            <style>
                body { font-family: Arial; padding: 20px; }
                table { border-collapse: collapse; width: 100%; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: right; }
                th { background-color: #f2f2f2; }
                .found { color: green; }
                .not-found { color: red; }
            </style>
        </head>
        <body>
            <h2>فحص الملفات المرفوعة</h2>
            <p><strong>مجلد الرفع:</strong> """ + upload_folder + """</p>
            <table>
                <tr>
                    <th>ID</th>
                    <th>اسم الملف</th>
                    <th>الاسم الأصلي</th>
                    <th>موجود؟</th>
                    <th>المسار</th>
                    <th>العميل</th>
                    <th>معاينة</th>
                </tr>
        """

        for result in results:
            status_class = "found" if result['found'] else "not-found"
            status_text = "نعم" if result['found'] else "لا"
            path_text = result['path'] if result['path'] else "غير موجود"

            html += f"""
                <tr>
                    <td>{result['id']}</td>
                    <td>{result['filename']}</td>
                    <td>{result['original_filename'] or 'غير محدد'}</td>
                    <td class="{status_class}">{status_text}</td>
                    <td>{path_text}</td>
                    <td>{result['client_id']}</td>
                    <td>
                        <a href="/simple_preview/{result['id']}" target="_blank">معاينة</a>
                    </td>
                </tr>
            """

        html += """
            </table>
        </body>
        </html>
        """

        return html

    except Exception as e:
        return f"خطأ في فحص الملفات: {str(e)}"

@app.route('/documents/<int:document_id>/view')
def documents_view_file(document_id):
    """عرض المستند في المتصفح (للمعاينة)"""
    try:
        print(f"🔍 طلب معاينة للمستند ID: {document_id}")

        document = ClientDocument.query.get(document_id)
        if not document:
            print(f"❌ المستند غير موجود: {document_id}")
            return "المستند غير موجود", 404

        print(f"📄 المستند موجود: {document.filename}")

        upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
        print(f"📁 مجلد الرفع: {upload_folder}")

        # البحث عن الملف في عدة مواقع
        possible_paths = [
            os.path.join(upload_folder, document.filename),
            os.path.join(upload_folder, 'documents', document.filename),
        ]

        file_path = None
        for path in possible_paths:
            print(f"🔍 البحث في: {path}")
            if os.path.exists(path):
                file_path = path
                print(f"✅ الملف موجود في: {path}")
                break
            else:
                print(f"❌ الملف غير موجود في: {path}")

        if not file_path:
            print(f"❌ الملف غير موجود في جميع المسارات")
            return f"""
            <html dir="rtl">
            <head><title>ملف غير موجود</title></head>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h2>⚠️ الملف غير موجود</h2>
                <p>اسم الملف: {document.filename}</p>
                <p>المسارات المفحوصة:</p>
                <ul>
                    {''.join([f'<li>{path}</li>' for path in possible_paths])}
                </ul>
                <a href="/clients/{document.client_id}">العودة لصفحة العميل</a>
            </body>
            </html>
            """, 404

        # استخدام send_file للعرض في المتصفح (بدون تحميل)
        from flask import send_file
        import mimetypes

        # تحديد نوع الملف
        mimetype, _ = mimetypes.guess_type(file_path)
        if mimetype is None:
            mimetype = 'application/octet-stream'

        print(f"📋 نوع الملف: {mimetype}")

        # عرض الملف في المتصفح (inline) بدلاً من التحميل
        return send_file(
            file_path,
            as_attachment=False,  # هذا مهم للمعاينة
            mimetype=mimetype
        )

    except Exception as e:
        print(f"❌ خطأ في المعاينة: {str(e)}")
        import traceback
        traceback.print_exc()

        return f"""
        <html dir="rtl">
        <head><title>خطأ في العرض</title></head>
        <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h2>❌ خطأ في عرض الملف</h2>
            <p>تفاصيل الخطأ: {str(e)}</p>
            <a href="javascript:history.back()">العودة</a>
        </body>
        </html>
        """, 500

@app.route('/simple_download/<int:doc_id>')
def simple_download(doc_id):
    """تحميل مبسط للاختبار"""
    try:
        document = ClientDocument.query.get_or_404(doc_id)
        upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')

        # البحث عن الملف
        file_path = os.path.join(upload_folder, document.filename)
        if not os.path.exists(file_path):
            file_path = os.path.join(upload_folder, 'documents', document.filename)

        if not os.path.exists(file_path):
            return f"<h3>File not found: {document.filename}</h3>", 404

        # استخدام send_file بدلاً من Response
        from flask import send_file
        return send_file(file_path, as_attachment=True, download_name=document.original_filename or f"document_{doc_id}")

    except Exception as e:
        return f"<h3>Error: {str(e)}</h3>", 500

@app.route('/test_documents')
def test_documents():
    """صفحة اختبار لعرض روابط المستندات"""
    documents = ClientDocument.query.all()

    html = """
    <html dir="rtl">
    <head>
        <title>اختبار المستندات</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-4">
            <h1>اختبار روابط المستندات</h1>
            <table class="table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>اسم الملف</th>
                        <th>العميل</th>
                        <th>رابط التحميل</th>
                        <th>اختبار</th>
                    </tr>
                </thead>
                <tbody>
    """

    for doc in documents:
        html += f"""
                    <tr>
                        <td>{doc.id}</td>
                        <td>{doc.original_filename or doc.filename}</td>
                        <td>{doc.client.full_name}</td>
                        <td>/documents/{doc.id}/download</td>
                        <td>
                            <a href="/documents/{doc.id}/download" class="btn btn-sm btn-primary">تحميل عادي</a>
                            <a href="/download/{doc.id}" class="btn btn-sm btn-success">تحميل مبسط</a>
                        </td>
                    </tr>
        """

    html += """
                </tbody>
            </table>
            <a href="/documents" class="btn btn-primary">صفحة المستندات الرئيسية</a>
            <a href="/" class="btn btn-secondary">الرئيسية</a>
        </div>
    </body>
    </html>
    """

    return html

@app.route('/all_documents')
@login_required
def all_documents():
    documents = ClientDocument.query.join(Client).all()

    return render_template_string('''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="utf-8">
    <title>جميع المستندات</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/">🏛️ المحامي فالح بن عقاب آل عيسى</a>
            <div>
                <a class="btn btn-outline-light btn-sm" href="/">الرئيسية</a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="card">
            <div class="card-header">
                <h3>📄 جميع المستندات</h3>
            </div>
            <div class="card-body">
                {% if documents %}
                <table class="table">
                    <thead>
                        <tr>
                            <th>العميل</th>
                            <th>نوع المستند</th>
                            <th>الوصف</th>
                            <th>التاريخ</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for doc in documents %}
                        <tr>
                            <td>{{ doc.client.full_name }}</td>
                            <td>
                                {% if doc.document_type == 'identity' %}
                                    🆔 الهوية الشخصية
                                {% elif doc.document_type == 'power_of_attorney' %}
                                    📋 الوكالة
                                {% elif doc.document_type == 'contract' %}
                                    📄 العقد
                                {% else %}
                                    📎 مستند آخر
                                {% endif %}
                            </td>
                            <td>{{ doc.description or '-' }}</td>
                            <td>{{ doc.created_at.strftime('%Y-%m-%d') }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
                {% else %}
                <div class="text-center py-5">
                    <h5>لا توجد مستندات</h5>
                </div>
                {% endif %}
            </div>
        </div>
    </div>
</body>
</html>
    ''', documents=documents)

@app.route('/edit_client/<int:client_id>', methods=['GET', 'POST'])
@login_required
def edit_client(client_id):
    client = Client.query.get_or_404(client_id)

    if request.method == 'POST':
        # تحديث بيانات العميل
        client.first_name = request.form['first_name']
        client.last_name = request.form['last_name']
        client.national_id = request.form.get('national_id')
        client.phone = request.form.get('phone')
        client.email = request.form.get('email')
        client.address = request.form.get('address')

        db.session.commit()
        flash(f'تم تحديث بيانات العميل {client.full_name} بنجاح', 'success')
        return redirect(url_for('clients'))

    return render_template_string('''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="utf-8">
    <title>تعديل العميل</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/">🏛️ المحامي فالح بن عقاب آل عيسى</a>
            <div>
                <a class="btn btn-outline-light btn-sm" href="/clients">العملاء</a>
                <a class="btn btn-outline-light btn-sm ms-2" href="/">الرئيسية</a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="card">
            <div class="card-header bg-warning text-dark">
                <h3>✏️ تعديل بيانات العميل: {{ client.full_name }}</h3>
            </div>
            <div class="card-body">
                <form method="POST">
                    <div class="card mb-3">
                        <div class="card-header bg-primary text-white">
                            <h5>👤 البيانات الأساسية</h5>
                        </div>
                        <div class="card-body">
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">الاسم الأول *</label>
                                        <input type="text" class="form-control" name="first_name" value="{{ client.first_name }}" required>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">اسم العائلة *</label>
                                        <input type="text" class="form-control" name="last_name" value="{{ client.last_name }}" required>
                                    </div>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">🆔 رقم الهوية الوطنية</label>
                                        <input type="text" class="form-control" name="national_id" value="{{ client.national_id or '' }}">
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">📱 رقم الهاتف</label>
                                        <input type="text" class="form-control" name="phone" value="{{ client.phone or '' }}">
                                    </div>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">📧 البريد الإلكتروني</label>
                                        <input type="email" class="form-control" name="email" value="{{ client.email or '' }}">
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">🏠 العنوان</label>
                                        <input type="text" class="form-control" name="address" value="{{ client.address or '' }}">
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="text-center">
                        <button type="submit" class="btn btn-warning btn-lg">💾 حفظ التعديلات</button>
                        <a href="/clients" class="btn btn-secondary btn-lg ms-2">❌ إلغاء</a>
                        <a href="/client_documents/{{ client.id }}" class="btn btn-info btn-lg ms-2">📄 إدارة المستندات</a>
                    </div>
                </form>
            </div>
        </div>

        <!-- عرض المستندات الحالية -->
        <div class="card mt-4">
            <div class="card-header bg-info text-white d-flex justify-content-between align-items-center">
                <h5 class="mb-0">📄 المستندات الحالية</h5>
                <a href="/add_document/{{ client.id }}" class="btn btn-light btn-sm">➕ إضافة مستند جديد</a>
            </div>
            <div class="card-body">
                {% if client.client_documents %}
                <div class="row">
                    {% for doc in client.client_documents %}
                    <div class="col-md-4 mb-3">
                        <div class="card border-secondary">
                            <div class="card-body">
                                <h6 class="card-title">
                                    {% if doc.document_type == 'identity' %}
                                        🆔 الهوية الشخصية
                                    {% elif doc.document_type == 'power_of_attorney' %}
                                        📋 الوكالة
                                    {% elif doc.document_type == 'contract' %}
                                        📄 العقد
                                    {% else %}
                                        📎 مستند آخر
                                    {% endif %}
                                </h6>

                                {% if doc.description %}
                                    <p class="card-text"><small>{{ doc.description }}</small></p>
                                {% endif %}

                                {% if doc.filename %}
                                    <div class="mb-2">
                                        <span class="badge bg-info">{{ doc.original_filename }}</span>
                                        {% if doc.is_image %}
                                            <div class="mt-1 text-center">
                                                <img src="/documents/{{ doc.id }}/view"
                                                     class="img-thumbnail"
                                                     style="max-width: 120px; max-height: 90px; cursor: pointer; border: 2px solid #007bff;"
                                                     alt="معاينة {{ doc.original_filename }}"
                                                     onclick="showQuickPreview({{ doc.id }}, '{{ (doc.original_filename or doc.filename)|replace("'", "\\'") }}')"
                                                     onerror="this.style.display='none'; this.nextElementSibling.style.display='block';"
                                                     title="انقر للمعاينة الكاملة">
                                                <div style="display: none; padding: 5px; background: #f8f9fa; border-radius: 4px; border: 1px dashed #ccc;">
                                                    <i class="fas fa-image text-muted"></i>
                                                    <br><small class="text-muted">لا يمكن عرض الصورة</small>
                                                </div>
                                            </div>
                                        {% endif %}
                                    </div>
                                {% endif %}

                                <div class="btn-group btn-group-sm" role="group">
                                    {% if doc.filename %}
                                        <button onclick="showQuickPreview({{ doc.id }}, '{{ (doc.original_filename or doc.filename)|replace("'", "\\'") }}')" class="btn btn-outline-primary" title="معاينة سريعة">👁️</button>
                                        <a href="/documents/{{ doc.id }}/download" class="btn btn-outline-success" title="تحميل">📥</a>
                                    {% endif %}
                                    <a href="/edit_document/{{ doc.id }}" class="btn btn-outline-warning" title="تعديل">✏️</a>
                                    <a href="/delete_document/{{ doc.id }}" class="btn btn-outline-danger" title="حذف"
                                       onclick="return confirm('حذف هذا المستند؟')">🗑️</a>
                                </div>
                            </div>
                        </div>
                    </div>
                    {% endfor %}
                </div>
                {% else %}
                <div class="text-center py-3">
                    <p class="text-muted">لا توجد مستندات لهذا العميل</p>
                    <a href="/add_document/{{ client.id }}" class="btn btn-primary">➕ إضافة مستند جديد</a>
                </div>
                {% endif %}
            </div>
        </div>
    </div>

    <!-- Modal للمعاينة السريعة -->
    <div class="modal fade" id="quickPreviewModal" tabindex="-1" aria-labelledby="quickPreviewModalLabel" aria-hidden="true">
        <div class="modal-dialog modal-lg modal-dialog-centered">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="quickPreviewModalLabel">معاينة سريعة</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body text-center" id="previewContent">
                    <div class="spinner-border" role="status">
                        <span class="visually-hidden">جاري التحميل...</span>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">إغلاق</button>
                    <a href="#" id="downloadBtn" class="btn btn-success">📥 تحميل</a>
                </div>
            </div>
        </div>
    </div>

    <script>
    function showQuickPreview(docId, filename) {
        try {
            console.log('showQuickPreview called with:', docId, filename);

            // التحقق من وجود Bootstrap - إذا لم يكن متاحاً، استخدم modal بسيط
            if (typeof bootstrap === 'undefined') {
                console.log('Bootstrap غير متاح، استخدام modal بسيط');
                showSimplePreview(docId, filename);
                return;
            }

            // التحقق من وجود المودال
            const modalElement = document.getElementById('quickPreviewModal');
            if (!modalElement) {
                alert('خطأ: المودال غير موجود');
                return;
            }

            // إظهار المودال
            const modal = new bootstrap.Modal(modalElement);
            const previewContent = document.getElementById('previewContent');
            const downloadBtn = document.getElementById('downloadBtn');
            const modalTitle = document.getElementById('quickPreviewModalLabel');

            // تحديث العنوان
            modalTitle.textContent = 'معاينة: ' + filename;

            // تحديث رابط التحميل
            downloadBtn.href = '/documents/' + docId + '/download';

            // إظهار loading
            previewContent.innerHTML = `
                <div class="spinner-border" role="status">
                    <span class="visually-hidden">جاري التحميل...</span>
                </div>
            `;

            modal.show();

            // تحديد نوع الملف من الامتداد
            const extension = filename.split('.').pop().toLowerCase();

        if (['jpg', 'jpeg', 'png', 'gif'].includes(extension)) {
            // للصور
            setTimeout(() => {
                previewContent.innerHTML = `
                    <div class="text-center">
                        <img src="/documents/${docId}/view"
                             class="img-fluid"
                             style="max-height: 400px; max-width: 100%; border: 1px solid #ddd; border-radius: 5px;"
                             alt="${filename}"
                             onload="console.log('Image loaded successfully')"
                             onerror="console.error('Image failed to load'); this.parentElement.innerHTML='<div class=\\"alert alert-danger\\">خطأ في تحميل الصورة<br>المسار: /documents/${docId}/view</div>'">
                        <div class="mt-2">
                            <small class="text-muted">اسم الملف: ${filename}</small>
                        </div>
                    </div>
                `;
            }, 500);
        } else if (extension === 'pdf') {
            // لملفات PDF
            previewContent.innerHTML = `
                <iframe src="/documents/${docId}/view"
                        width="100%"
                        height="400px"
                        style="border: 1px solid #ddd;">
                    <p>متصفحك لا يدعم عرض ملفات PDF.
                       <a href="/documents/${docId}/download">انقر هنا لتحميل الملف</a>
                    </p>
                </iframe>
            `;
        } else {
            // للملفات الأخرى
            previewContent.innerHTML = `
                <div class="alert alert-info">
                    <i class="fas fa-file-alt fa-3x mb-3"></i>
                    <h5>معاينة غير متاحة</h5>
                    <p>لا يمكن معاينة هذا النوع من الملفات في المتصفح</p>
                    <p><strong>نوع الملف:</strong> ${extension.toUpperCase()}</p>
                </div>
            `;
        }
        } catch (error) {
            console.error('خطأ في showQuickPreview:', error);
            alert('حدث خطأ في عرض المعاينة: ' + error.message);
        }
    }

    // دالة معاينة بسيطة بدون Bootstrap (نسخة للحالات)
    function showSimplePreview(docId, filename) {
        try {
            // إنشاء overlay
            const overlay = document.createElement('div');
            overlay.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.8);
                z-index: 9999;
                display: flex;
                justify-content: center;
                align-items: center;
                cursor: pointer;
            `;

            // إنشاء محتوى المعاينة
            const content = document.createElement('div');
            content.style.cssText = `
                background: white;
                border-radius: 8px;
                padding: 20px;
                max-width: 90%;
                max-height: 90%;
                overflow: auto;
                position: relative;
                cursor: default;
                direction: rtl;
                text-align: center;
            `;

            // زر الإغلاق
            const closeBtn = document.createElement('button');
            closeBtn.innerHTML = '×';
            closeBtn.style.cssText = `
                position: absolute;
                top: 10px;
                left: 15px;
                background: none;
                border: none;
                font-size: 24px;
                cursor: pointer;
                color: #666;
                width: 30px;
                height: 30px;
                display: flex;
                align-items: center;
                justify-content: center;
            `;

            // محتوى الملف
            const fileContent = document.createElement('div');
            fileContent.style.cssText = `
                text-align: center;
                padding: 20px;
                min-height: 200px;
            `;

            // عرض loading أولاً
            fileContent.innerHTML = '<div style="padding: 40px;"><p>جاري التحميل...</p></div>';

            // تحديد نوع الملف وعرضه
            const fileExt = filename.split('.').pop().toLowerCase();

            setTimeout(() => {
                if (['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'].includes(fileExt)) {
                    const img = document.createElement('img');
                    // استخدام رابط المستند بدلاً من اسم الملف مباشرة
                    img.src = '/documents/' + docId + '/view';
                    img.style.cssText = 'max-width: 100%; max-height: 70vh; border-radius: 4px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);';
                    img.onload = function() {
                        fileContent.innerHTML = '';
                        fileContent.appendChild(img);
                    };
                    img.onerror = function() {
                        // إذا فشل الرابط الأول، جرب الرابط البديل
                        img.src = '/simple_file/' + filename;
                        img.onerror = function() {
                            fileContent.innerHTML = `
                                <div style="padding: 40px; color: #dc3545;">
                                    <h4>⚠️ خطأ في تحميل الصورة</h4>
                                    <p>اسم الملف: ${filename}</p>
                                    <div style="margin-top: 20px;">
                                        <a href="/documents/${docId}/download" target="_blank"
                                           style="display: inline-block; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 4px; margin: 10px;">
                                            فتح في نافذة جديدة
                                        </a>
                                        <a href="/documents/${docId}/download" download
                                           style="display: inline-block; padding: 10px 20px; background: #28a745; color: white; text-decoration: none; border-radius: 4px; margin: 10px;">
                                            تحميل الملف
                                        </a>
                                    </div>
                                </div>
                            `;
                        };
                    };
                } else if (fileExt === 'pdf') {
                    fileContent.innerHTML = `
                        <div style="padding: 20px;">
                            <iframe src="/simple_file/${filename}"
                                    style="width: 80vw; height: 70vh; border: 1px solid #ddd; border-radius: 4px;"
                                    onload="console.log('PDF loaded')"
                                    onerror="this.style.display='none'; this.nextElementSibling.style.display='block';">
                            </iframe>
                            <div style="display: none; padding: 40px; color: #dc3545;">
                                <h4>⚠️ لا يمكن عرض ملف PDF</h4>
                                <p>اسم الملف: ${filename}</p>
                                <a href="/simple_file/${filename}" target="_blank"
                                   style="display: inline-block; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 4px; margin: 10px;">
                                    فتح في نافذة جديدة
                                </a>
                            </div>
                        </div>
                    `;
                } else {
                    fileContent.innerHTML = `
                        <div style="padding: 40px;">
                            <h4>📄 معاينة الملف</h4>
                            <p><strong>اسم الملف:</strong> ${filename}</p>
                            <p><strong>نوع الملف:</strong> ${fileExt.toUpperCase()}</p>
                            <div style="margin-top: 20px;">
                                <a href="/simple_file/${filename}" target="_blank"
                                   style="display: inline-block; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 4px; margin: 10px;">
                                    فتح الملف
                                </a>
                                <a href="/simple_file/${filename}" download
                                   style="display: inline-block; padding: 10px 20px; background: #28a745; color: white; text-decoration: none; border-radius: 4px; margin: 10px;">
                                    تحميل الملف
                                </a>
                            </div>
                        </div>
                    `;
                }
            }, 300);

            // تجميع العناصر
            content.appendChild(closeBtn);
            content.appendChild(fileContent);
            overlay.appendChild(content);
            document.body.appendChild(overlay);

            // إغلاق عند النقر على الخلفية
            overlay.addEventListener('click', function(e) {
                if (e.target === overlay) {
                    document.body.removeChild(overlay);
                }
            });

            // إغلاق عند النقر على زر الإغلاق
            closeBtn.addEventListener('click', function() {
                document.body.removeChild(overlay);
            });

            // إغلاق بمفتاح Escape
            const escapeHandler = function(e) {
                if (e.key === 'Escape') {
                    if (document.body.contains(overlay)) {
                        document.body.removeChild(overlay);
                        document.removeEventListener('keydown', escapeHandler);
                    }
                }
            };
            document.addEventListener('keydown', escapeHandler);

        } catch (error) {
            console.error('خطأ في showSimplePreview:', error);
            // fallback: فتح في نافذة جديدة
            window.open('/simple_file/' + filename, '_blank');
        }
    }
    </script>
</body>
</html>
    ''', client=client)

@app.route('/delete_client/<int:client_id>')
@login_required
def delete_client(client_id):
    client = Client.query.get_or_404(client_id)

    # التحقق من وجود قضايا مرتبطة
    cases_count = Case.query.filter_by(client_id=client_id).count()
    appointments_count = Appointment.query.filter_by(client_id=client_id).count()
    invoices_count = Invoice.query.filter_by(client_id=client_id).count()

    if cases_count > 0 or appointments_count > 0 or invoices_count > 0:
        flash(f'لا يمكن حذف العميل {client.full_name} لأنه مرتبط بـ {cases_count} قضية و {appointments_count} موعد و {invoices_count} فاتورة. يجب حذف هذه البيانات أولاً.', 'error')
        return redirect(url_for('clients'))

    try:
        # حذف ملفات المستندات من النظام
        documents = ClientDocument.query.filter_by(client_id=client_id).all()
        for doc in documents:
            if doc.filename:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], doc.filename)
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except OSError:
                        pass  # تجاهل أخطاء حذف الملفات

        # حذف المستندات من قاعدة البيانات
        ClientDocument.query.filter_by(client_id=client_id).delete()

        # حذف العميل
        db.session.delete(client)
        db.session.commit()

        flash(f'تم حذف العميل {client.full_name} ومستنداته بنجاح', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء حذف العميل: {str(e)}', 'error')

    return redirect(url_for('clients'))

@app.route('/force_delete_client/<int:client_id>')
@login_required
@admin_required
def force_delete_client(client_id):
    """حذف العميل مع جميع بياناته المرتبطة (للمدير فقط)"""
    client = Client.query.get_or_404(client_id)

    try:
        # حذف ملفات المستندات من النظام
        documents = ClientDocument.query.filter_by(client_id=client_id).all()
        for doc in documents:
            if doc.filename:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], doc.filename)
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except OSError:
                        pass

        # حذف جميع البيانات المرتبطة بالعميل
        # 1. حذف المستندات
        ClientDocument.query.filter_by(client_id=client_id).delete()

        # 2. حذف الفواتير والدفعات
        invoices = Invoice.query.filter_by(client_id=client_id).all()
        for invoice in invoices:
            InvoicePayment.query.filter_by(invoice_id=invoice.id).delete()
        Invoice.query.filter_by(client_id=client_id).delete()

        # 3. حذف المواعيد
        Appointment.query.filter_by(client_id=client_id).delete()

        # 4. حذف القضايا (سيحذف المواعيد والفواتير المرتبطة بالقضايا تلقائياً)
        cases = Case.query.filter_by(client_id=client_id).all()
        for case in cases:
            # حذف مستندات القضية
            ClientDocument.query.filter_by(case_id=case.id).delete()
            # حذف مواعيد القضية
            Appointment.query.filter_by(case_id=case.id).delete()
            # حذف فواتير القضية
            case_invoices = Invoice.query.filter_by(case_id=case.id).all()
            for invoice in case_invoices:
                InvoicePayment.query.filter_by(invoice_id=invoice.id).delete()
            Invoice.query.filter_by(case_id=case.id).delete()

        Case.query.filter_by(client_id=client_id).delete()

        # 5. حذف العميل
        db.session.delete(client)
        db.session.commit()

        flash(f'تم حذف العميل {client.full_name} وجميع بياناته المرتبطة بنجاح', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء حذف العميل: {str(e)}', 'error')

    return redirect(url_for('clients'))

@app.route('/add_document/<int:client_id>', methods=['GET', 'POST'])
@login_required
def add_document(client_id):
    client = Client.query.get_or_404(client_id)

    # التحقق من وجود case_id في الرابط
    preselected_case_id = request.args.get('case_id', type=int)

    if request.method == 'POST':
        doc = ClientDocument(
            document_type=request.form['document_type'],
            description=request.form.get('description', ''),
            client_id=client_id,
            case_id=request.form.get('case_id') if request.form.get('case_id') else None
        )

        # معالجة الملف المرفوع
        if 'document_file' in request.files:
            file = request.files['document_file']
            if file and file.filename != '' and allowed_file(file.filename):
                # إنشاء اسم ملف آمن مع timestamp
                filename = safe_filename_with_timestamp(file.filename)

                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)

                doc.filename = filename
                doc.original_filename = file.filename
                doc.file_size = os.path.getsize(file_path)

        db.session.add(doc)
        db.session.commit()
        flash('تم إضافة المستند بنجاح', 'success')

        # إذا كان المستند مرتبط بقضية، العودة لصفحة القضية
        if doc.case_id:
            return redirect(url_for('view_case', case_id=doc.case_id))
        else:
            return redirect(url_for('edit_client', client_id=client_id))

    return render_template_string('''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="utf-8">
    <title>إضافة مستند</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/">🏛️ المحامي فالح بن عقاب آل عيسى</a>
            <div>
                <a class="btn btn-outline-light btn-sm" href="/edit_client/{{ client.id }}">العميل</a>
                <a class="btn btn-outline-light btn-sm ms-2" href="/clients">العملاء</a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="card">
            <div class="card-header bg-success text-white">
                <h3>➕ إضافة مستند جديد للعميل: {{ client.full_name }}</h3>
            </div>
            <div class="card-body">
                <form method="POST" enctype="multipart/form-data">
                    <div class="mb-3">
                        <label class="form-label">نوع المستند *</label>
                        <select class="form-control" name="document_type" required>
                            <option value="">اختر نوع المستند</option>
                            <option value="identity">🆔 الهوية الشخصية</option>
                            <option value="power_of_attorney">📋 الوكالة</option>
                            <option value="contract">📄 العقد</option>
                            <option value="other">📎 مستند آخر</option>
                        </select>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">وصف المستند</label>
                        <textarea class="form-control" name="description" rows="3" placeholder="أدخل وصف تفصيلي للمستند..."></textarea>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">ربط بقضية (اختياري)</label>
                        <select class="form-control" name="case_id">
                            <option value="">لا يرتبط بقضية محددة</option>
                            {% for case in client.cases %}
                            <option value="{{ case.id }}" {{ 'selected' if preselected_case_id == case.id else '' }}>
                                {{ case.case_number }} - {{ case.title }}
                            </option>
                            {% endfor %}
                        </select>
                        {% if preselected_case_id %}
                        <small class="text-success">تم اختيار القضية مسبقاً</small>
                        {% endif %}
                    </div>
                    <div class="mb-3">
                        <label class="form-label">رفع الملف</label>
                        <input type="file" class="form-control" name="document_file" accept=".pdf,.png,.jpg,.jpeg,.gif,.doc,.docx">
                        <small class="text-muted">الملفات المدعومة: PDF, صور, Word</small>
                    </div>
                    <div class="d-flex gap-2">
                        <button type="submit" class="btn btn-success">💾 حفظ المستند</button>
                        <a href="/edit_client/{{ client.id }}" class="btn btn-secondary">❌ إلغاء</a>
                    </div>
                </form>
            </div>
        </div>
    </div>
</body>
</html>
    ''', client=client, preselected_case_id=preselected_case_id)

@app.route('/edit_document/<int:doc_id>', methods=['GET', 'POST'])
@login_required
def edit_document(doc_id):
    doc = ClientDocument.query.get_or_404(doc_id)

    if request.method == 'POST':
        doc.document_type = request.form['document_type']
        doc.description = request.form.get('description', '')

        # معالجة الملف الجديد إذا تم رفعه
        if 'document_file' in request.files:
            file = request.files['document_file']
            if file and file.filename != '' and allowed_file(file.filename):
                # حذف الملف القديم
                if doc.filename:
                    old_file_path = os.path.join(app.config['UPLOAD_FOLDER'], doc.filename)
                    if os.path.exists(old_file_path):
                        os.remove(old_file_path)

                # حفظ الملف الجديد
                filename = safe_filename_with_timestamp(file.filename)

                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)

                doc.filename = filename
                doc.original_filename = file.filename
                doc.file_size = os.path.getsize(file_path)

        db.session.commit()
        flash('تم تحديث المستند بنجاح', 'success')
        return redirect(url_for('edit_client', client_id=doc.client_id))

    return render_template_string('''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="utf-8">
    <title>تعديل المستند</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/">🏛️ المحامي فالح بن عقاب آل عيسى</a>
            <div>
                <a class="btn btn-outline-light btn-sm" href="/edit_client/{{ doc.client_id }}">العميل</a>
                <a class="btn btn-outline-light btn-sm ms-2" href="/clients">العملاء</a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="card">
            <div class="card-header bg-warning text-dark">
                <h3>✏️ تعديل المستند للعميل: {{ doc.client.full_name }}</h3>
            </div>
            <div class="card-body">
                <form method="POST" enctype="multipart/form-data">
                    <div class="mb-3">
                        <label class="form-label">نوع المستند *</label>
                        <select class="form-control" name="document_type" required>
                            <option value="identity" {{ 'selected' if doc.document_type == 'identity' else '' }}>🆔 الهوية الشخصية</option>
                            <option value="power_of_attorney" {{ 'selected' if doc.document_type == 'power_of_attorney' else '' }}>📋 الوكالة</option>
                            <option value="contract" {{ 'selected' if doc.document_type == 'contract' else '' }}>📄 العقد</option>
                            <option value="other" {{ 'selected' if doc.document_type == 'other' else '' }}>📎 مستند آخر</option>
                        </select>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">وصف المستند</label>
                        <textarea class="form-control" name="description" rows="3">{{ doc.description or '' }}</textarea>
                    </div>

                    {% if doc.filename %}
                    <div class="mb-3">
                        <label class="form-label">الملف الحالي</label>
                        <div class="card">
                            <div class="card-body">
                                <div class="d-flex align-items-center">
                                    {% if doc.is_image %}
                                        <img src="{{ url_for('simple_file', filename=doc.filename) }}" class="img-thumbnail me-3" style="max-width: 100px; max-height: 80px;">
                                    {% elif doc.is_pdf %}
                                        <i class="fas fa-file-pdf text-danger me-3" style="font-size: 2em;"></i>
                                    {% else %}
                                        <i class="fas fa-file text-primary me-3" style="font-size: 2em;"></i>
                                    {% endif %}
                                    <div>
                                        <strong>{{ doc.original_filename }}</strong><br>
                                        <small class="text-muted">{{ doc.file_size_mb }} MB</small>
                                    </div>
                                </div>
                                <div class="mt-2">
                                    <button onclick="window.open('{{ url_for('simple_file', filename=doc.filename) }}', '_blank')" class="btn btn-sm btn-primary">👁️ عرض</button>
                                    <a href="{{ url_for('simple_file', filename=doc.filename) }}" class="btn btn-sm btn-success" download="{{ doc.original_filename }}">📥 تحميل</a>
                                </div>
                            </div>
                        </div>
                    </div>
                    {% endif %}

                    <div class="mb-3">
                        <label class="form-label">{{ 'استبدال الملف' if doc.filename else 'رفع ملف جديد' }}</label>
                        <input type="file" class="form-control" name="document_file" accept=".pdf,.png,.jpg,.jpeg,.gif,.doc,.docx">
                        <small class="text-muted">{{ 'اترك فارغاً للاحتفاظ بالملف الحالي' if doc.filename else 'الملفات المدعومة: PDF, صور, Word' }}</small>
                    </div>

                    <div class="d-flex gap-2">
                        <button type="submit" class="btn btn-warning">💾 حفظ التعديلات</button>
                        <a href="/edit_client/{{ doc.client_id }}" class="btn btn-secondary">❌ إلغاء</a>
                    </div>
                </form>
            </div>
        </div>
    </div>
</body>
</html>
    ''', doc=doc)

@app.route('/delete_document/<int:doc_id>')
@login_required
def delete_document(doc_id):
    doc = ClientDocument.query.get_or_404(doc_id)
    client_id = doc.client_id

    # حذف الملف من النظام
    if doc.filename:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], doc.filename)
        if os.path.exists(file_path):
            os.remove(file_path)

    # حذف المستند من قاعدة البيانات
    db.session.delete(doc)
    db.session.commit()

    flash('تم حذف المستند بنجاح', 'success')
    return redirect(url_for('edit_client', client_id=client_id))

@app.route('/appointments')
@login_required
def appointments():
    filter_type = request.args.get('filter', 'all')

    query = Appointment.query.join(Client)

    if filter_type == 'today':
        today = datetime.now().date()
        query = query.filter(db.func.date(Appointment.appointment_date) == today)
    elif filter_type == 'upcoming':
        query = query.filter(Appointment.appointment_date >= datetime.now())
    elif filter_type == 'past':
        query = query.filter(Appointment.appointment_date < datetime.now())

    appointments_list = query.order_by(Appointment.appointment_date.desc()).all()

    return render_template_string('''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="utf-8">
    <title>إدارة المواعيد</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/">🏛️ المحامي فالح بن عقاب آل عيسى</a>
            <div>
                <a class="btn btn-outline-light btn-sm" href="/">الرئيسية</a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="card">
            <div class="card-header d-flex justify-content-between align-items-center">
                <h3>📅 إدارة المواعيد</h3>
                <div>
                    <div class="btn-group me-2" role="group">
                        <a href="/appointments" class="btn btn-outline-secondary {{ 'active' if request.args.get('filter') != 'today' and request.args.get('filter') != 'upcoming' and request.args.get('filter') != 'past' else '' }}">الكل</a>
                        <a href="/appointments?filter=today" class="btn btn-outline-warning {{ 'active' if request.args.get('filter') == 'today' else '' }}">اليوم</a>
                        <a href="/appointments?filter=upcoming" class="btn btn-outline-success {{ 'active' if request.args.get('filter') == 'upcoming' else '' }}">القادمة</a>
                        <a href="/appointments?filter=past" class="btn btn-outline-secondary {{ 'active' if request.args.get('filter') == 'past' else '' }}">السابقة</a>
                    </div>
                    <a href="/add_appointment" class="btn btn-primary">➕ إضافة موعد</a>
                </div>
            </div>
            <div class="card-body">
                {% with messages = get_flashed_messages(with_categories=true) %}
                    {% if messages %}
                        {% for category, message in messages %}
                            <div class="alert alert-{{ category }}">{{ message }}</div>
                        {% endfor %}
                    {% endif %}
                {% endwith %}

                {% if appointments %}
                <div class="table-responsive">
                    <table class="table table-striped">
                        <thead>
                            <tr>
                                <th>العنوان</th>
                                <th>العميل</th>
                                <th>التاريخ والوقت</th>
                                <th>المدة</th>
                                <th>المكان</th>
                                <th>الحالة</th>
                                <th>الإجراءات</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for appointment in appointments %}
                            <tr class="{{ 'table-warning' if appointment.is_today else ('table-light' if appointment.is_past else '') }}">
                                <td>
                                    <strong>{{ appointment.title }}</strong>
                                    {% if appointment.description %}
                                        <br><small class="text-muted">{{ appointment.description[:50] }}...</small>
                                    {% endif %}
                                </td>
                                <td>{{ appointment.client.full_name if appointment.client else '-' }}</td>
                                <td>
                                    {{ appointment.appointment_date.strftime('%Y-%m-%d') }}<br>
                                    <small>{{ appointment.appointment_date.strftime('%H:%M') }}</small>
                                </td>
                                <td>{{ appointment.duration_minutes }} دقيقة</td>
                                <td>{{ appointment.location or '-' }}</td>
                                <td>
                                    <span class="badge bg-{{ appointment.status_badge }}">
                                        {% if appointment.status == 'scheduled' %}مجدول
                                        {% elif appointment.status == 'completed' %}مكتمل
                                        {% elif appointment.status == 'cancelled' %}ملغي
                                        {% else %}معاد جدولته{% endif %}
                                    </span>
                                </td>
                                <td>
                                    <div class="btn-group btn-group-sm" role="group">
                                        <a href="/edit_appointment/{{ appointment.id }}" class="btn btn-outline-warning">✏️ تعديل</a>
                                        {% if appointment.status == 'scheduled' %}
                                            <a href="/complete_appointment/{{ appointment.id }}" class="btn btn-outline-success">✅ إكمال</a>
                                        {% endif %}
                                        <a href="/delete_appointment/{{ appointment.id }}" class="btn btn-outline-danger"
                                           onclick="return confirm('حذف الموعد؟')">🗑️ حذف</a>
                                    </div>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                {% else %}
                <div class="text-center py-5">
                    <h5>لا توجد مواعيد</h5>
                    <a href="/add_appointment" class="btn btn-primary">إضافة موعد جديد</a>
                </div>
                {% endif %}
            </div>
        </div>
    </div>
</body>
</html>
    ''', appointments=appointments_list)

@app.route('/add_appointment', methods=['GET', 'POST'])
@login_required
def add_appointment():
    # الحصول على معرف القضية من الرابط إذا كان موجوداً
    case_id_param = request.args.get('case_id')

    if request.method == 'POST':
        appointment = Appointment(
            title=request.form['title'],
            description=request.form.get('description'),
            appointment_date=datetime.strptime(request.form['appointment_date'], '%Y-%m-%dT%H:%M'),
            duration_minutes=int(request.form.get('duration_minutes', 60)),
            location=request.form.get('location'),
            client_id=request.form.get('client_id') if request.form.get('client_id') else None,
            case_id=request.form.get('case_id') if request.form.get('case_id') else None
        )

        db.session.add(appointment)
        db.session.commit()
        flash('تم إضافة الموعد بنجاح', 'success')

        # إذا كان الموعد مرتبط بقضية، العودة لصفحة القضية
        if appointment.case_id:
            return redirect(url_for('view_case', case_id=appointment.case_id))
        else:
            return redirect(url_for('appointments'))

    clients = Client.query.all()
    cases = Case.query.join(Client).all()
    selected_case = None

    # إذا كان هناك معرف قضية في الرابط، جلب بيانات القضية
    if case_id_param:
        selected_case = Case.query.get(case_id_param)

    return render_template_string('''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="utf-8">
    <title>إضافة موعد جديد</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/">🏛️ المحامي فالح بن عقاب آل عيسى</a>
            <div>
                <a class="btn btn-outline-light btn-sm" href="/appointments">المواعيد</a>
                <a class="btn btn-outline-light btn-sm ms-2" href="/">الرئيسية</a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="card">
            <div class="card-header bg-warning text-dark">
                <h3>➕ إضافة موعد جديد</h3>
            </div>
            <div class="card-body">
                <form method="POST">
                    <div class="mb-3">
                        <label class="form-label">عنوان الموعد *</label>
                        <input type="text" class="form-control" name="title" required placeholder="مثال: اجتماع مع العميل">
                    </div>

                    <div class="row">
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label class="form-label">التاريخ والوقت *</label>
                                <input type="datetime-local" class="form-control" name="appointment_date" required>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label class="form-label">المدة (بالدقائق)</label>
                                <input type="number" class="form-control" name="duration_minutes" value="60" min="15" max="480">
                            </div>
                        </div>
                    </div>

                    <div class="row">
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label class="form-label">العميل</label>
                                <select class="form-control" name="client_id">
                                    <option value="">اختر العميل (اختياري)</option>
                                    {% for client in clients %}
                                    <option value="{{ client.id }}">{{ client.full_name }}</option>
                                    {% endfor %}
                                </select>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label class="form-label">القضية المرتبطة</label>
                                <select class="form-control" name="case_id">
                                    <option value="">اختر القضية (اختياري)</option>
                                    {% for case in cases %}
                                    <option value="{{ case.id }}" {{ 'selected' if selected_case and selected_case.id == case.id else '' }}>{{ case.case_number }} - {{ case.title }}</option>
                                    {% endfor %}
                                </select>
                                {% if selected_case %}
                                <small class="text-info">تم اختيار القضية: {{ selected_case.case_number }}</small>
                                {% endif %}
                            </div>
                        </div>
                    </div>

                    <div class="mb-3">
                        <label class="form-label">المكان</label>
                        <input type="text" class="form-control" name="location" placeholder="مثال: المكتب، المحكمة، عبر الهاتف">
                    </div>

                    <div class="mb-3">
                        <label class="form-label">وصف الموعد</label>
                        <textarea class="form-control" name="description" rows="3" placeholder="تفاصيل الموعد والملاحظات..."></textarea>
                    </div>

                    <div class="text-center">
                        <button type="submit" class="btn btn-warning btn-lg">💾 حفظ الموعد</button>
                        <a href="/appointments" class="btn btn-secondary btn-lg ms-2">❌ إلغاء</a>
                    </div>
                </form>
            </div>
        </div>
    </div>
</body>
</html>
    ''', clients=clients, cases=cases, selected_case=selected_case)

@app.route('/edit_appointment/<int:appointment_id>', methods=['GET', 'POST'])
@login_required
def edit_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)

    if request.method == 'POST':
        appointment.title = request.form['title']
        appointment.description = request.form.get('description')
        appointment.appointment_date = datetime.strptime(request.form['appointment_date'], '%Y-%m-%dT%H:%M')
        appointment.duration_minutes = int(request.form.get('duration_minutes', 60))
        appointment.location = request.form.get('location')
        appointment.status = request.form['status']
        appointment.client_id = request.form.get('client_id') if request.form.get('client_id') else None
        appointment.case_id = request.form.get('case_id') if request.form.get('case_id') else None

        db.session.commit()
        flash('تم تحديث الموعد بنجاح', 'success')
        return redirect(url_for('appointments'))

    clients = Client.query.all()
    cases = Case.query.join(Client).all()

    return render_template_string('''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="utf-8">
    <title>تعديل الموعد</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/">🏛️ المحامي فالح بن عقاب آل عيسى</a>
            <div>
                <a class="btn btn-outline-light btn-sm" href="/appointments">المواعيد</a>
                <a class="btn btn-outline-light btn-sm ms-2" href="/">الرئيسية</a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="card">
            <div class="card-header bg-warning text-dark">
                <h3>✏️ تعديل الموعد</h3>
            </div>
            <div class="card-body">
                <form method="POST">
                    <div class="mb-3">
                        <label class="form-label">عنوان الموعد *</label>
                        <input type="text" class="form-control" name="title" value="{{ appointment.title }}" required>
                    </div>

                    <div class="row">
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label class="form-label">التاريخ والوقت *</label>
                                <input type="datetime-local" class="form-control" name="appointment_date"
                                       value="{{ appointment.appointment_date.strftime('%Y-%m-%dT%H:%M') }}" required>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label class="form-label">المدة (بالدقائق)</label>
                                <input type="number" class="form-control" name="duration_minutes"
                                       value="{{ appointment.duration_minutes }}" min="15" max="480">
                            </div>
                        </div>
                    </div>

                    <div class="row">
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label class="form-label">العميل</label>
                                <select class="form-control" name="client_id">
                                    <option value="">اختر العميل (اختياري)</option>
                                    {% for client in clients %}
                                    <option value="{{ client.id }}" {{ 'selected' if appointment.client_id == client.id else '' }}>{{ client.full_name }}</option>
                                    {% endfor %}
                                </select>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label class="form-label">القضية المرتبطة</label>
                                <select class="form-control" name="case_id">
                                    <option value="">اختر القضية (اختياري)</option>
                                    {% for case in cases %}
                                    <option value="{{ case.id }}" {{ 'selected' if appointment.case_id == case.id else '' }}>{{ case.case_number }} - {{ case.title }}</option>
                                    {% endfor %}
                                </select>
                            </div>
                        </div>
                    </div>

                    <div class="row">
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label class="form-label">المكان</label>
                                <input type="text" class="form-control" name="location" value="{{ appointment.location or '' }}">
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label class="form-label">حالة الموعد</label>
                                <select class="form-control" name="status">
                                    <option value="scheduled" {{ 'selected' if appointment.status == 'scheduled' else '' }}>مجدول</option>
                                    <option value="completed" {{ 'selected' if appointment.status == 'completed' else '' }}>مكتمل</option>
                                    <option value="cancelled" {{ 'selected' if appointment.status == 'cancelled' else '' }}>ملغي</option>
                                    <option value="rescheduled" {{ 'selected' if appointment.status == 'rescheduled' else '' }}>معاد جدولته</option>
                                </select>
                            </div>
                        </div>
                    </div>

                    <div class="mb-3">
                        <label class="form-label">وصف الموعد</label>
                        <textarea class="form-control" name="description" rows="3">{{ appointment.description or '' }}</textarea>
                    </div>

                    <div class="text-center">
                        <button type="submit" class="btn btn-warning btn-lg">💾 حفظ التعديلات</button>
                        <a href="/appointments" class="btn btn-secondary btn-lg ms-2">❌ إلغاء</a>
                    </div>
                </form>
            </div>
        </div>
    </div>
</body>
</html>
    ''', appointment=appointment, clients=clients, cases=cases)

@app.route('/complete_appointment/<int:appointment_id>')
@login_required
def complete_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    appointment.status = 'completed'
    db.session.commit()
    flash('تم تحديد الموعد كمكتمل', 'success')
    return redirect(url_for('appointments'))

@app.route('/delete_appointment/<int:appointment_id>')
@login_required
def delete_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    db.session.delete(appointment)
    db.session.commit()
    flash('تم حذف الموعد', 'success')
    return redirect(url_for('appointments'))

@app.route('/invoices')
@login_required
def invoices():
    filter_type = request.args.get('filter', 'all')

    query = Invoice.query.join(Client)

    if filter_type == 'pending':
        query = query.filter(Invoice.status == 'pending')
    elif filter_type == 'paid':
        query = query.filter(Invoice.status == 'paid')
    elif filter_type == 'partial':
        query = query.filter(Invoice.status == 'partial')
    elif filter_type == 'overdue':
        query = query.filter(Invoice.status.in_(['pending', 'partial']), Invoice.due_date < datetime.now())

    invoices_list = query.order_by(Invoice.created_at.desc()).all()

    return render_template_string('''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="utf-8">
    <title>إدارة الفواتير</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/">🏛️ المحامي فالح بن عقاب آل عيسى</a>
            <div>
                <a class="btn btn-outline-light btn-sm" href="/">الرئيسية</a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="card">
            <div class="card-header d-flex justify-content-between align-items-center">
                <h3>💰 إدارة الفواتير</h3>
                <div>
                    <div class="btn-group me-2" role="group">
                        <a href="/invoices" class="btn btn-outline-secondary {{ 'active' if not request.args.get('filter') else '' }}">الكل</a>
                        <a href="/invoices?filter=pending" class="btn btn-outline-warning {{ 'active' if request.args.get('filter') == 'pending' else '' }}">معلقة</a>
                        <a href="/invoices?filter=partial" class="btn btn-outline-info {{ 'active' if request.args.get('filter') == 'partial' else '' }}">جزئية</a>
                        <a href="/invoices?filter=paid" class="btn btn-outline-success {{ 'active' if request.args.get('filter') == 'paid' else '' }}">مكتملة</a>
                        <a href="/invoices?filter=overdue" class="btn btn-outline-danger {{ 'active' if request.args.get('filter') == 'overdue' else '' }}">متأخرة</a>
                    </div>
                    <a href="/add_invoice" class="btn btn-primary">➕ إضافة فاتورة</a>
                </div>
            </div>
            <div class="card-body">
                {% with messages = get_flashed_messages(with_categories=true) %}
                    {% if messages %}
                        {% for category, message in messages %}
                            <div class="alert alert-{{ category }}">{{ message }}</div>
                        {% endfor %}
                    {% endif %}
                {% endwith %}

                {% if invoices %}
                <div class="table-responsive">
                    <table class="table table-striped">
                        <thead>
                            <tr>
                                <th>رقم الفاتورة</th>
                                <th>العميل</th>
                                <th>القضية</th>
                                <th>المبلغ</th>
                                <th>تاريخ الإصدار</th>
                                <th>تاريخ الاستحقاق</th>
                                <th>الحالة</th>
                                <th>الإجراءات</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for invoice in invoices %}
                            <tr class="{{ 'table-danger' if invoice.is_overdue else '' }}">
                                <td><strong>{{ invoice.invoice_number }}</strong></td>
                                <td>{{ invoice.client.full_name }}</td>
                                <td>{{ invoice.case.case_number if invoice.case else '-' }}</td>
                                <td>
                                    <strong>{{ "{:,.2f}".format(invoice.total_amount) }} {{ riyal_svg()|safe }}</strong>
                                    {% if invoice.paid_amount > 0 %}
                                        <br><small class="text-success">مدفوع: {{ "{:,.2f}".format(invoice.paid_amount) }}</small>
                                        {% if invoice.remaining_amount > 0 %}
                                            <br><small class="text-danger">متبقي: {{ "{:,.2f}".format(invoice.remaining_amount) }}</small>
                                        {% endif %}
                                    {% endif %}
                                    {% if invoice.tax_amount > 0 %}
                                        <br><small class="text-muted">شامل ضريبة: {{ "{:,.2f}".format(invoice.tax_amount) }}</small>
                                    {% endif %}
                                </td>
                                <td>{{ invoice.issue_date.strftime('%Y-%m-%d') }}</td>
                                <td>
                                    {% if invoice.due_date %}
                                        {{ invoice.due_date.strftime('%Y-%m-%d') }}
                                        {% if invoice.is_overdue and invoice.status == 'pending' %}
                                            <br><small class="text-danger">متأخرة</small>
                                        {% endif %}
                                    {% else %}
                                        -
                                    {% endif %}
                                </td>
                                <td>
                                    <span class="badge bg-{{ invoice.status_badge }}">
                                        {% if invoice.status == 'pending' %}معلقة
                                        {% elif invoice.status == 'paid' %}مدفوعة بالكامل
                                        {% elif invoice.status == 'partial' %}مدفوعة جزئياً
                                        {% elif invoice.status == 'overdue' %}متأخرة
                                        {% else %}ملغية{% endif %}
                                    </span>
                                    {% if invoice.payments %}
                                        <br><small class="text-info">{{ invoice.payments|length }} دفعة</small>
                                    {% endif %}
                                    {% if invoice.payment_date and invoice.status == 'paid' %}
                                        <br><small class="text-success">اكتملت في: {{ invoice.payment_date.strftime('%Y-%m-%d') }}</small>
                                    {% endif %}
                                    {% if invoice.status == 'partial' %}
                                        <br><small class="text-warning">{{ "{:.1f}".format(invoice.payment_percentage) }}% مدفوع</small>
                                    {% endif %}
                                </td>
                                <td>
                                    <div class="btn-group btn-group-sm" role="group">
                                        <a href="/view_invoice/{{ invoice.id }}" class="btn btn-outline-info">👁️ عرض</a>
                                        {% if invoice.remaining_amount > 0 %}
                                            <a href="/add_payment/{{ invoice.id }}" class="btn btn-outline-success">💰 دفعة</a>
                                        {% endif %}
                                        <a href="/edit_invoice/{{ invoice.id }}" class="btn btn-outline-warning">✏️ تعديل</a>
                                        <a href="/delete_invoice/{{ invoice.id }}" class="btn btn-outline-danger"
                                           onclick="return confirm('حذف الفاتورة؟')">🗑️ حذف</a>
                                    </div>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                {% else %}
                <div class="text-center py-5">
                    <h5>لا توجد فواتير</h5>
                    <a href="/add_invoice" class="btn btn-primary">إضافة فاتورة جديدة</a>
                </div>
                {% endif %}
            </div>
        </div>
    </div>
</body>
</html>
    ''', invoices=invoices_list)

@app.route('/add_invoice', methods=['GET', 'POST'])
@login_required
def add_invoice():
    # التحقق من وجود case_id في الرابط
    preselected_case_id = request.args.get('case_id', type=int)
    preselected_client_id = None

    if preselected_case_id:
        case = Case.query.get(preselected_case_id)
        if case:
            preselected_client_id = case.client_id
    if request.method == 'POST':
        # حساب المبلغ الإجمالي
        amount = float(request.form['amount'])
        tax_rate = float(request.form.get('tax_rate', 0)) / 100
        tax_amount = amount * tax_rate
        total_amount = amount + tax_amount

        # إنشاء رقم فاتورة تلقائي
        last_invoice = Invoice.query.order_by(Invoice.id.desc()).first()
        if last_invoice:
            last_number = int(last_invoice.invoice_number.split('-')[-1])
            invoice_number = f"INV-{last_number + 1:04d}"
        else:
            invoice_number = "INV-0001"

        invoice = Invoice(
            invoice_number=invoice_number,
            client_id=request.form['client_id'],
            case_id=request.form.get('case_id') if request.form.get('case_id') else None,
            description=request.form.get('description'),
            amount=amount,
            tax_amount=tax_amount,
            total_amount=total_amount,
            notes=request.form.get('notes')
        )

        # تاريخ الاستحقاق
        if request.form.get('due_date'):
            invoice.due_date = datetime.strptime(request.form['due_date'], '%Y-%m-%d')

        db.session.add(invoice)
        db.session.commit()
        flash(f'تم إضافة الفاتورة {invoice_number} بنجاح', 'success')

        # إذا كانت الفاتورة مرتبطة بقضية، العودة لصفحة القضية
        if invoice.case_id:
            return redirect(url_for('view_case', case_id=invoice.case_id))
        else:
            return redirect(url_for('invoices'))

    clients = Client.query.all()
    cases = Case.query.join(Client).all()

    return render_template_string('''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="utf-8">
    <title>إضافة فاتورة جديدة</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
    <script>
        function calculateTotal() {
            const amount = parseFloat(document.getElementById('amount').value) || 0;
            const taxRate = parseFloat(document.getElementById('tax_rate').value) || 0;
            const taxAmount = amount * (taxRate / 100);
            const total = amount + taxAmount;

            document.getElementById('tax_amount_display').textContent = taxAmount.toFixed(2);
            document.getElementById('total_amount_display').textContent = total.toFixed(2);
        }

        function filterCases() {
            const clientId = document.querySelector('select[name="client_id"]').value;
            const caseSelect = document.getElementById('case_select');
            const options = caseSelect.querySelectorAll('option');

            // إظهار جميع الخيارات أولاً
            options.forEach(option => {
                if (option.value === '') {
                    option.style.display = 'block';
                } else if (clientId === '' || option.dataset.client === clientId) {
                    option.style.display = 'block';
                } else {
                    option.style.display = 'none';
                }
            });

            // إعادة تعيين القيمة المختارة إذا لم تعد متاحة
            if (caseSelect.value && caseSelect.querySelector(`option[value="${caseSelect.value}"]`).style.display === 'none') {
                caseSelect.value = '';
            }
        }

        // تشغيل الفلترة عند تحميل الصفحة
        window.onload = function() {
            filterCases();
        }
    </script>
</head>
<body>
    <nav class="navbar navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/">🏛️ المحامي فالح بن عقاب آل عيسى</a>
            <div>
                <a class="btn btn-outline-light btn-sm" href="/invoices">الفواتير</a>
                <a class="btn btn-outline-light btn-sm ms-2" href="/">الرئيسية</a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="card">
            <div class="card-header bg-danger text-white">
                <h3>➕ إضافة فاتورة جديدة</h3>
            </div>
            <div class="card-body">
                <form method="POST">
                    <div class="row">
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label class="form-label">العميل *</label>
                                <select class="form-control" name="client_id" required onchange="filterCases()">
                                    <option value="">اختر العميل</option>
                                    {% for client in clients %}
                                    <option value="{{ client.id }}" {{ 'selected' if preselected_client_id == client.id else '' }}>{{ client.full_name }}</option>
                                    {% endfor %}
                                </select>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label class="form-label">القضية المرتبطة</label>
                                <select class="form-control" name="case_id" id="case_select">
                                    <option value="">اختر القضية (اختياري)</option>
                                    {% for case in cases %}
                                    <option value="{{ case.id }}" data-client="{{ case.client_id }}" {{ 'selected' if preselected_case_id == case.id else '' }}>
                                        {{ case.case_number }} - {{ case.title }}
                                    </option>
                                    {% endfor %}
                                </select>
                                {% if preselected_case_id %}
                                <small class="text-success">تم اختيار القضية مسبقاً</small>
                                {% endif %}
                            </div>
                        </div>
                    </div>

                    <div class="mb-3">
                        <label class="form-label">وصف الخدمة *</label>
                        <textarea class="form-control" name="description" rows="3" required placeholder="وصف الخدمات المقدمة..."></textarea>
                    </div>

                    <div class="row">
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label class="form-label">المبلغ الأساسي *</label>
                                <input type="number" class="form-control" name="amount" id="amount" step="0.01" required onchange="calculateTotal()">
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label class="form-label">نسبة الضريبة (%)</label>
                                <input type="number" class="form-control" name="tax_rate" id="tax_rate" step="0.01" value="15" onchange="calculateTotal()">
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label class="form-label">تاريخ الاستحقاق</label>
                                <input type="date" class="form-control" name="due_date">
                            </div>
                        </div>
                    </div>

                    <div class="card bg-light">
                        <div class="card-body">
                            <h6>ملخص الفاتورة:</h6>
                            <div class="row">
                                <div class="col-md-4">
                                    <strong>مبلغ الضريبة:</strong> <span id="tax_amount_display">0.00</span> {{ riyal_svg()|safe }}
                                </div>
                                <div class="col-md-4">
                                    <strong>المبلغ الإجمالي:</strong> <span id="total_amount_display">0.00</span> {{ riyal_svg()|safe }}
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="mb-3 mt-3">
                        <label class="form-label">ملاحظات</label>
                        <textarea class="form-control" name="notes" rows="2" placeholder="ملاحظات إضافية..."></textarea>
                    </div>

                    <div class="text-center">
                        <button type="submit" class="btn btn-danger btn-lg">💾 حفظ الفاتورة</button>
                        <a href="/invoices" class="btn btn-secondary btn-lg ms-2">❌ إلغاء</a>
                    </div>
                </form>
            </div>
        </div>
    </div>
</body>
</html>
    ''', clients=clients, cases=cases, preselected_case_id=preselected_case_id,
         preselected_client_id=preselected_client_id)

@app.route('/view_invoice/<int:invoice_id>')
@login_required
def view_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    office_settings = OfficeSettings.get_settings()

    return render_template_string('''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="utf-8">
    <title>فاتورة رقم {{ invoice.invoice_number }} - {{ office_settings.office_name }}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/@emran-alhaddad/saudi-riyal-font/index.css" rel="stylesheet">
    <style>
        @page {
            size: A4;
            margin: 0.4in;
        }

        @media print {
            .no-print { display: none !important; }
            body {
                margin: 0;
                font-size: 10pt;
                line-height: 1.2;
                background: white !important;
                position: relative;
            }

            .container {
                max-width: none;
                margin: 0;
                padding: 0;
                width: 100%;
            }
            .invoice-container {
                box-shadow: none !important;
                border: none !important;
                margin: 0 !important;
                page-break-inside: avoid;
            }
            .invoice-header {
                background: #2c3e50 !important;
                -webkit-print-color-adjust: exact;
                color-adjust: exact;
                padding: 12px !important;
            }
            .total-section {
                background: #27ae60 !important;
                -webkit-print-color-adjust: exact;
                color-adjust: exact;
                padding: 12px !important;
                margin: 8px 0 !important;
            }
            .services-table th {
                background: #3498db !important;
                -webkit-print-color-adjust: exact;
                color-adjust: exact;
                padding: 6px !important;
            }
            .services-table td {
                padding: 6px !important;
            }
            .invoice-details {
                padding: 8px !important;
            }
            .info-card {
                padding: 8px !important;
                margin: 6px 0 !important;
            }
            .footer-section {
                padding: 8px !important;
                font-size: 9pt;
            }
            .logo-section {
                justify-content: center !important;
                position: relative !important;
            }
            .logo-section img {
                max-height: 45px !important;
                position: absolute !important;
                left: 50% !important;
                transform: translateX(-50%) !important;
            }
            .logo-section div {
                margin-left: auto !important;
                text-align: left !important;
                padding-left: 80px !important;
                width: 50% !important;
            }
            .office-name {
                font-size: 16px !important;
            }
            .invoice-number {
                font-size: 22px !important;
            }
            .info-row {
                margin-bottom: 3px !important;
                padding-bottom: 3px !important;
            }
            h5 {
                font-size: 11pt !important;
                margin-bottom: 5px !important;
            }
            .payment-info {
                padding: 8px !important;
                margin: 6px 0 !important;
            }

            /* تقليل المسافات بين الأقسام */
            .row {
                margin-bottom: 6px !important;
            }

            h1, h2, h3, h4, h5, h6 {
                margin-bottom: 4px !important;
                margin-top: 4px !important;
            }

            p {
                margin-bottom: 2px !important;
            }

            .status-badge {
                font-size: 9px !important;
                padding: 3px 6px !important;
            }

            /* ضمان ظهور التخطيط الجديد في الطباعة */
            .invoice-details {
                display: block !important;
                width: 100% !important;
            }

            .invoice-details .row {
                display: flex !important;
                flex-wrap: wrap !important;
                margin: 0 !important;
                margin-bottom: 8px !important;
            }

            .invoice-details .col-md-6 {
                width: 48% !important;
                float: right !important;
                margin: 0 1% !important;
                display: block !important;
            }

            .info-card {
                border: 2px solid #3498db !important;
                border-radius: 8px !important;
                padding: 10px !important;
                margin: 5px 0 !important;
                background: white !important;
                box-shadow: none !important;
                page-break-inside: avoid !important;
                display: block !important;
                width: 100% !important;
                box-sizing: border-box !important;
            }

            .info-card h5 {
                color: #2c3e50 !important;
                margin-bottom: 8px !important;
                font-weight: 600 !important;
                font-size: 11pt !important;
                border-bottom: 2px solid #3498db !important;
                padding-bottom: 5px !important;
                display: block !important;
            }

            .info-card h5 i {
                color: #3498db !important;
                margin-left: 5px !important;
            }

            .info-row {
                display: flex !important;
                justify-content: space-between !important;
                margin-bottom: 4px !important;
                padding-bottom: 2px !important;
                font-size: 9pt !important;
                border-bottom: 1px dotted #ddd !important;
            }

            .info-row:last-child {
                border-bottom: none !important;
                margin-bottom: 0 !important;
            }

            .info-label {
                font-weight: 600 !important;
                color: #34495e !important;
                width: 40% !important;
            }

            .info-value {
                color: #2c3e50 !important;
                width: 58% !important;
                text-align: left !important;
            }

            /* إصلاح التخطيط للطباعة */
            .clearfix::after {
                content: "" !important;
                display: table !important;
                clear: both !important;
            }

            /* رمز الريال السعودي الجديد */
            .riyal-symbol {
                display: inline-block !important;
                width: 16px !important;
                height: 16px !important;
                margin: 0 2px !important;
                vertical-align: middle !important;
            }
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f5f5f5;
        }

        .invoice-container {
            background: white;
            box-shadow: 0 0 30px rgba(0,0,0,0.1);
            border-radius: 10px;
            overflow: hidden;
            max-width: 210mm;
            margin: 20px auto;
            position: relative;
        }


        .invoice-header {
            background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
            color: white;
            padding: 20px;
            position: relative;
            z-index: 1;
        }

        .logo-section {
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 20px;
            position: relative;
        }

        .logo-section img {
            max-height: 80px;
            background: white;
            padding: 10px;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            position: absolute;
            left: 50%;
            transform: translateX(-50%);
        }

        .logo-section div {
            margin-left: auto;
            text-align: left;
            padding-left: 120px;
            width: 50%;
        }

        .office-name {
            font-size: 22px;
            font-weight: bold;
            margin: 0;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
        }

        .office-subtitle {
            font-size: 14px;
            opacity: 0.9;
            margin: 5px 0 0 0;
        }

        .invoice-title {
            position: absolute;
            top: 30px;
            left: 30px;
            text-align: left;
        }

        .invoice-number {
            font-size: 32px;
            font-weight: bold;
            margin: 0;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
        }

        .invoice-date {
            font-size: 14px;
            opacity: 0.9;
        }

        .status-badge {
            position: absolute;
            top: 20px;
            right: 20px;
            padding: 10px 20px;
            border-radius: 25px;
            font-weight: bold;
            font-size: 14px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        }

        .status-paid { background: #27ae60; color: white; }
        .status-pending { background: #f39c12; color: white; }
        .status-overdue { background: #e74c3c; color: white; }
        .status-partial { background: #9b59b6; color: white; }



        .client-info {
            background: white;
            padding: 15px;
            border-right: 4px solid #3498db;
            margin: 15px 0;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }

        .invoice-details {
            padding: 15px;
        }

        .services-table {
            margin: 15px 0;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }

        .services-table th {
            background: #3498db;
            color: white;
            padding: 10px;
            font-weight: 600;
            text-align: center;
        }

        .services-table td {
            padding: 10px;
            border-bottom: 1px solid #eee;
            text-align: center;
        }

        .services-table tr:last-child td {
            border-bottom: none;
        }

        .total-section {
            background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%);
            color: white;
            padding: 15px;
            margin: 15px 0;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 5px 20px rgba(39, 174, 96, 0.3);
        }

        .payment-info {
            background: #e8f6f3;
            padding: 12px;
            border-radius: 8px;
            border-right: 4px solid #27ae60;
            margin: 12px 0;
        }

        .footer-section {
            background: #2c3e50;
            color: white;
            padding: 15px;
            text-align: center;
            font-size: 11px;
        }

        .info-card {
            background: white;
            border-radius: 8px;
            padding: 12px;
            margin: 10px 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            border-right: 4px solid #3498db;
            position: relative;
            z-index: 1;
        }

        .info-card h5 {
            color: #2c3e50;
            margin-bottom: 8px;
            font-weight: 600;
            font-size: 14px;
        }

        .info-row {
            display: flex;
            justify-content: space-between;
            margin-bottom: 4px;
            padding-bottom: 4px;
            border-bottom: 1px solid #f8f9fa;
            font-size: 12px;
        }

        .info-row:last-child {
            border-bottom: none;
            margin-bottom: 0;
            padding-bottom: 0;
        }

        .info-label {
            font-weight: 600;
            color: #34495e;
        }

        .info-value {
            color: #2c3e50;
        }
    </style>
</head>
<body>
    <!-- أزرار التحكم -->
    <div class="no-print" style="position: fixed; top: 20px; right: 20px; z-index: 1000;">
        <div class="btn-group">
            <button onclick="window.print()" class="btn btn-primary">
                <i class="fas fa-print me-1"></i>طباعة
            </button>
            <a href="/edit_invoice/{{ invoice.id }}" class="btn btn-warning">
                <i class="fas fa-edit me-1"></i>تعديل
            </a>
            <a href="/invoices" class="btn btn-secondary">
                <i class="fas fa-arrow-right me-1"></i>العودة
            </a>
        </div>
    </div>

    <div class="invoice-container">
        <!-- رأس الفاتورة -->
        <div class="invoice-header">
            <!-- شارة الحالة -->
            <div class="status-badge status-{{ invoice.status }}">
                {% if invoice.status == 'pending' %}معلقة
                {% elif invoice.status == 'paid' %}مدفوعة
                {% elif invoice.status == 'partial' %}جزئية
                {% elif invoice.status == 'overdue' %}متأخرة
                {% else %}ملغية{% endif %}
            </div>

            <!-- معلومات المكتب والشعار -->
            <div class="logo-section">
                {% if office_settings.logo_path %}
                    <img src="{{ url_for('simple_file', filename=office_settings.logo_path) }}" alt="شعار المكتب">
                {% endif %}
                <div>
                    <h1 class="office-name">{{ office_settings.office_name }}</h1>
                    <p class="office-subtitle">{{ office_settings.description or 'مكتب محاماة واستشارات قانونية' }}</p>
                </div>
            </div>

            <!-- رقم الفاتورة والتاريخ -->
            <div class="invoice-title">
                <h2 class="invoice-number">فاتورة #{{ invoice.invoice_number }}</h2>
                <p class="invoice-date">تاريخ الإصدار: {{ invoice.issue_date.strftime('%d/%m/%Y') }}</p>
                {% if invoice.due_date %}
                <p class="invoice-date">تاريخ الاستحقاق: {{ invoice.due_date.strftime('%d/%m/%Y') }}</p>
                {% endif %}
            </div>
        </div>

        <!-- الصف الأول: معلومات المكتب (يمين) ومعلومات التسجيل (يسار) -->
        <div class="invoice-details">
            <div class="row clearfix">
                <!-- معلومات المكتب - يمين -->
                <div class="col-md-6">
                    <div class="info-card">
                        <h5><i class="fas fa-building me-2"></i>معلومات المكتب</h5>
                        <div class="info-row">
                            <span class="info-label">العنوان:</span>
                            <span class="info-value">{{ office_settings.address or 'غير محدد' }}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">المدينة:</span>
                            <span class="info-value">{{ office_settings.city or 'غير محدد' }}</span>
                        </div>
                        {% if office_settings.phone_1 %}
                        <div class="info-row">
                            <span class="info-label">الهاتف:</span>
                            <span class="info-value">{{ office_settings.phone_1 }}</span>
                        </div>
                        {% endif %}
                        {% if office_settings.email %}
                        <div class="info-row">
                            <span class="info-label">البريد الإلكتروني:</span>
                            <span class="info-value">{{ office_settings.email }}</span>
                        </div>
                        {% endif %}
                    </div>
                </div>

                <!-- معلومات التسجيل - يسار -->
                <div class="col-md-6">
                    <div class="info-card">
                        <h5><i class="fas fa-certificate me-2"></i>معلومات التسجيل</h5>
                        {% if office_settings.commercial_register %}
                        <div class="info-row">
                            <span class="info-label">السجل التجاري:</span>
                            <span class="info-value">{{ office_settings.commercial_register }}</span>
                        </div>
                        {% endif %}
                        {% if office_settings.tax_number %}
                        <div class="info-row">
                            <span class="info-label">الرقم الضريبي:</span>
                            <span class="info-value">{{ office_settings.tax_number }}</span>
                        </div>
                        {% endif %}
                        {% if office_settings.license_number %}
                        <div class="info-row">
                            <span class="info-label">رقم الترخيص:</span>
                            <span class="info-value">{{ office_settings.license_number }}</span>
                        </div>
                        {% endif %}
                        {% if office_settings.website %}
                        <div class="info-row">
                            <span class="info-label">الموقع الإلكتروني:</span>
                            <span class="info-value">{{ office_settings.website }}</span>
                        </div>
                        {% endif %}
                    </div>
                </div>
            </div>

            <!-- الصف الثاني: معلومات العميل (يمين) ومعلومات القضية (يسار) -->
            <div class="row clearfix">
                <!-- معلومات العميل - يمين -->
                <div class="col-md-6">
                    <div class="info-card">
                        <h5><i class="fas fa-user me-2"></i>معلومات العميل</h5>
                        <div class="info-row">
                            <span class="info-label">الاسم:</span>
                            <span class="info-value">{{ invoice.client.full_name }}</span>
                        </div>
                        {% if invoice.client.national_id %}
                        <div class="info-row">
                            <span class="info-label">رقم الهوية:</span>
                            <span class="info-value">{{ invoice.client.national_id }}</span>
                        </div>
                        {% endif %}
                        {% if invoice.client.phone %}
                        <div class="info-row">
                            <span class="info-label">الهاتف:</span>
                            <span class="info-value">{{ invoice.client.phone }}</span>
                        </div>
                        {% endif %}
                        {% if invoice.client.email %}
                        <div class="info-row">
                            <span class="info-label">البريد الإلكتروني:</span>
                            <span class="info-value">{{ invoice.client.email }}</span>
                        </div>
                        {% endif %}
                        {% if invoice.client.address %}
                        <div class="info-row">
                            <span class="info-label">العنوان:</span>
                            <span class="info-value">{{ invoice.client.address }}</span>
                        </div>
                        {% endif %}
                    </div>
                </div>

                <!-- معلومات القضية - يسار -->
                <div class="col-md-6">
                    {% if invoice.case %}
                    <div class="info-card">
                        <h5><i class="fas fa-folder me-2"></i>معلومات القضية</h5>
                        <div class="info-row">
                            <span class="info-label">رقم القضية:</span>
                            <span class="info-value">{{ invoice.case.case_number }}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">عنوان القضية:</span>
                            <span class="info-value">{{ invoice.case.title }}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">نوع القضية:</span>
                            <span class="info-value">{{ invoice.case.case_type }}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">حالة القضية:</span>
                            <span class="info-value">
                                {% if invoice.case.status == 'active' %}نشطة
                                {% elif invoice.case.status == 'closed' %}مغلقة
                                {% elif invoice.case.status == 'pending' %}معلقة
                                {% else %}ملغية{% endif %}
                            </span>
                        </div>
                    </div>
                    {% else %}
                    <div class="info-card">
                        <h5><i class="fas fa-info-circle me-2"></i>ملاحظة</h5>
                        <p class="text-muted mb-0">هذه الفاتورة غير مرتبطة بقضية محددة</p>
                    </div>
                    {% endif %}
                </div>
            </div>

            <!-- تفاصيل الخدمات والمبالغ -->
            <table class="table services-table">
                <thead>
                    <tr>
                        <th style="width: 60%">وصف الخدمة</th>
                        <th style="width: 20%">المبلغ</th>
                        <th style="width: 20%">{{ riyal_svg()|safe }}</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td style="text-align: right; padding-right: 20px;">
                            <strong>{{ invoice.description or 'خدمات قانونية' }}</strong>
                            {% if invoice.case %}
                            <br><small class="text-muted">القضية: {{ invoice.case.case_number }} - {{ invoice.case.title }}</small>
                            {% endif %}
                        </td>
                        <td><strong>{{ "%.2f"|format(invoice.amount) }}</strong></td>
                        <td>{{ riyal_svg()|safe }}</td>
                    </tr>
                    {% if invoice.tax_amount > 0 %}
                    <tr>
                        <td style="text-align: right; padding-right: 20px;">
                            <strong>ضريبة القيمة المضافة (15%)</strong>
                        </td>
                        <td><strong>{{ "%.2f"|format(invoice.tax_amount) }}</strong></td>
                        <td>{{ riyal_svg()|safe }}</td>
                    </tr>
                    {% endif %}
                </tbody>
            </table>

            <!-- إجمالي المبلغ -->
            <div class="total-section">
                <div class="row align-items-center">
                    <div class="col-md-8">
                        <h3 class="mb-0">
                            <i class="fas fa-calculator me-2"></i>
                            إجمالي المبلغ المستحق
                        </h3>
                        <p class="mb-0 mt-2 opacity-75">شامل جميع الرسوم والضرائب</p>
                    </div>
                    <div class="col-md-4 text-end">
                        <h2 class="mb-0" style="font-size: 2.5rem; font-weight: bold;">
                            {{ "%.2f"|format(invoice.total_amount) }}
                        </h2>
                        <p class="mb-0 mt-1">{{ riyal_svg()|safe }}</p>
                    </div>
                </div>
            </div>

            <!-- معلومات الدفعات -->
            {% if invoice.payments %}
            <div class="payment-info">
                <h5><i class="fas fa-credit-card me-2"></i>سجل الدفعات</h5>
                <div class="table-responsive">
                    <table class="table table-sm">
                        <thead>
                            <tr>
                                <th>التاريخ</th>
                                <th>المبلغ</th>
                                <th>طريقة الدفع</th>
                                <th>ملاحظات</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for payment in invoice.payments %}
                            <tr>
                                <td>{{ payment.payment_date.strftime('%d/%m/%Y') }}</td>
                                <td>{{ "%.2f"|format(payment.amount) }} {{ riyal_svg()|safe }}</td>
                                <td>{{ payment.payment_method or 'غير محدد' }}</td>
                                <td>{{ payment.notes or '-' }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                <div class="row mt-3">
                    <div class="col-md-6">
                        <strong>إجمالي المدفوع: {{ "%.2f"|format(invoice.paid_amount) }} {{ riyal_svg()|safe }}</strong>
                    </div>
                    <div class="col-md-6 text-end">
                        <strong>المتبقي: {{ "%.2f"|format(invoice.remaining_amount) }} {{ riyal_svg()|safe }}</strong>
                    </div>
                </div>
            </div>
            {% endif %}

            <!-- ملاحظات -->
            {% if invoice.notes %}
            <div class="info-card">
                <h5><i class="fas fa-sticky-note me-2"></i>ملاحظات</h5>
                <p class="mb-0">{{ invoice.notes }}</p>
            </div>
            {% endif %}
        </div>

        <!-- تذييل الفاتورة -->
        <div class="footer-section">
            <div class="row">
                <div class="col-md-4">
                    <strong>{{ office_settings.office_name }}</strong><br>
                    {% if office_settings.phone_1 %}{{ office_settings.phone_1 }}<br>{% endif %}
                    {% if office_settings.email %}{{ office_settings.email }}{% endif %}
                </div>
                <div class="col-md-4 text-center">
                    <strong>شكراً لثقتكم</strong><br>
                    <small>تم إنشاء هذه الفاتورة إلكترونياً</small>
                </div>
                <div class="col-md-4 text-end">
                    {% if office_settings.website %}
                        <strong>{{ office_settings.website }}</strong><br>
                    {% endif %}
                    {% if office_settings.tax_number %}
                        الرقم الضريبي: {{ office_settings.tax_number }}
                    {% endif %}
                </div>
            </div>
        </div>
    </div>

    <!-- أزرار الإجراءات -->
    <div class="no-print" style="text-center; margin: 20px 0;">
        {% if invoice.remaining_amount > 0 %}
            <a href="/add_payment/{{ invoice.id }}" class="btn btn-success btn-lg me-2">
                <i class="fas fa-credit-card me-1"></i>إضافة دفعة
            </a>
        {% endif %}
        {% if invoice.status == 'pending' and invoice.remaining_amount == invoice.total_amount %}
            <a href="/mark_paid/{{ invoice.id }}" class="btn btn-info btn-lg me-2">
                <i class="fas fa-check me-1"></i>دفع كامل
            </a>
        {% endif %}
        <a href="/edit_invoice/{{ invoice.id }}" class="btn btn-warning btn-lg me-2">
            <i class="fas fa-edit me-1"></i>تعديل الفاتورة
        </a>
        <a href="/invoices" class="btn btn-secondary btn-lg">
            <i class="fas fa-arrow-right me-1"></i>العودة للفواتير
        </a>
</body>
</html>
    ''', invoice=invoice, office_settings=office_settings)

@app.route('/edit_invoice/<int:invoice_id>', methods=['GET', 'POST'])
@login_required
def edit_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)

    if request.method == 'POST':
        # تحديث بيانات الفاتورة
        invoice.client_id = request.form['client_id']
        invoice.case_id = request.form.get('case_id') if request.form.get('case_id') else None
        invoice.description = request.form.get('description')

        # حساب المبلغ الإجمالي
        amount = float(request.form['amount'])
        tax_rate = float(request.form.get('tax_rate', 0)) / 100
        tax_amount = amount * tax_rate
        total_amount = amount + tax_amount

        invoice.amount = amount
        invoice.tax_amount = tax_amount
        invoice.total_amount = total_amount
        invoice.notes = request.form.get('notes')
        invoice.status = request.form['status']

        # تاريخ الاستحقاق
        if request.form.get('due_date'):
            invoice.due_date = datetime.strptime(request.form['due_date'], '%Y-%m-%d')
        else:
            invoice.due_date = None

        # تاريخ الدفع
        if invoice.status == 'paid' and not invoice.payment_date:
            invoice.payment_date = datetime.now()
        elif invoice.status != 'paid':
            invoice.payment_date = None

        db.session.commit()
        flash(f'تم تحديث الفاتورة {invoice.invoice_number} بنجاح', 'success')
        return redirect(url_for('view_invoice', invoice_id=invoice_id))

    clients = Client.query.all()
    cases = Case.query.join(Client).all()

    return render_template_string('''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="utf-8">
    <title>تعديل الفاتورة</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
    <script>
        function calculateTotal() {
            const amount = parseFloat(document.getElementById('amount').value) || 0;
            const taxRate = parseFloat(document.getElementById('tax_rate').value) || 0;
            const taxAmount = amount * (taxRate / 100);
            const total = amount + taxAmount;

            document.getElementById('tax_amount_display').textContent = taxAmount.toFixed(2);
            document.getElementById('total_amount_display').textContent = total.toFixed(2);
        }

        window.onload = function() {
            calculateTotal();
        }
    </script>
</head>
<body>
    <nav class="navbar navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/">🏛️ المحامي فالح بن عقاب آل عيسى</a>
            <div>
                <a class="btn btn-outline-light btn-sm" href="/view_invoice/{{ invoice.id }}">عرض الفاتورة</a>
                <a class="btn btn-outline-light btn-sm ms-2" href="/invoices">الفواتير</a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="card">
            <div class="card-header bg-warning text-dark">
                <h3>✏️ تعديل الفاتورة: {{ invoice.invoice_number }}</h3>
            </div>
            <div class="card-body">
                <form method="POST">
                    <div class="row">
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label class="form-label">العميل *</label>
                                <select class="form-control" name="client_id" required>
                                    {% for client in clients %}
                                    <option value="{{ client.id }}" {{ 'selected' if client.id == invoice.client_id else '' }}>{{ client.full_name }}</option>
                                    {% endfor %}
                                </select>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label class="form-label">القضية المرتبطة</label>
                                <select class="form-control" name="case_id">
                                    <option value="">اختر القضية (اختياري)</option>
                                    {% for case in cases %}
                                    <option value="{{ case.id }}" {{ 'selected' if invoice.case_id == case.id else '' }}>{{ case.case_number }} - {{ case.title }}</option>
                                    {% endfor %}
                                </select>
                            </div>
                        </div>
                    </div>

                    <div class="mb-3">
                        <label class="form-label">وصف الخدمة *</label>
                        <textarea class="form-control" name="description" rows="3" required>{{ invoice.description or '' }}</textarea>
                    </div>

                    <div class="row">
                        <div class="col-md-3">
                            <div class="mb-3">
                                <label class="form-label">المبلغ الأساسي *</label>
                                <input type="number" class="form-control" name="amount" id="amount" step="0.01" value="{{ invoice.amount }}" required onchange="calculateTotal()">
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="mb-3">
                                <label class="form-label">نسبة الضريبة (%)</label>
                                <input type="number" class="form-control" name="tax_rate" id="tax_rate" step="0.01"
                                       value="{{ (invoice.tax_amount / invoice.amount * 100) if invoice.amount > 0 else 15 }}" onchange="calculateTotal()">
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="mb-3">
                                <label class="form-label">حالة الفاتورة</label>
                                <select class="form-control" name="status">
                                    <option value="pending" {{ 'selected' if invoice.status == 'pending' else '' }}>معلقة</option>
                                    <option value="paid" {{ 'selected' if invoice.status == 'paid' else '' }}>مدفوعة</option>
                                    <option value="cancelled" {{ 'selected' if invoice.status == 'cancelled' else '' }}>ملغية</option>
                                </select>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="mb-3">
                                <label class="form-label">تاريخ الاستحقاق</label>
                                <input type="date" class="form-control" name="due_date"
                                       value="{{ invoice.due_date.strftime('%Y-%m-%d') if invoice.due_date else '' }}">
                            </div>
                        </div>
                    </div>

                    <div class="card bg-light">
                        <div class="card-body">
                            <h6>ملخص الفاتورة:</h6>
                            <div class="row">
                                <div class="col-md-4">
                                    <strong>مبلغ الضريبة:</strong> <span id="tax_amount_display">{{ "{:.2f}".format(invoice.tax_amount) }}</span> {{ riyal_svg()|safe }}
                                </div>
                                <div class="col-md-4">
                                    <strong>المبلغ الإجمالي:</strong> <span id="total_amount_display">{{ "{:.2f}".format(invoice.total_amount) }}</span> {{ riyal_svg()|safe }}
                                </div>
                                {% if invoice.payment_date %}
                                <div class="col-md-4">
                                    <strong>تاريخ الدفع:</strong> {{ invoice.payment_date.strftime('%Y-%m-%d') }}
                                </div>
                                {% endif %}
                            </div>
                        </div>
                    </div>

                    <div class="mb-3 mt-3">
                        <label class="form-label">ملاحظات</label>
                        <textarea class="form-control" name="notes" rows="2">{{ invoice.notes or '' }}</textarea>
                    </div>

                    <div class="text-center">
                        <button type="submit" class="btn btn-warning btn-lg">💾 حفظ التعديلات</button>
                        <a href="/view_invoice/{{ invoice.id }}" class="btn btn-secondary btn-lg ms-2">❌ إلغاء</a>
                    </div>
                </form>
            </div>
        </div>
    </div>
</body>
</html>
    ''', invoice=invoice, clients=clients, cases=cases)

@app.route('/delete_invoice/<int:invoice_id>')
@login_required
def delete_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    invoice_number = invoice.invoice_number

    try:
        # حذف جميع الدفعات المرتبطة بالفاتورة أولاً
        InvoicePayment.query.filter_by(invoice_id=invoice_id).delete()

        # ثم حذف الفاتورة
        db.session.delete(invoice)
        db.session.commit()

        flash(f'تم حذف الفاتورة {invoice_number} وجميع دفعاتها بنجاح', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء حذف الفاتورة: {str(e)}', 'error')

    return redirect(url_for('invoices'))

@app.route('/add_payment/<int:invoice_id>', methods=['GET', 'POST'])
@login_required
def add_payment(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)

    if request.method == 'POST':
        amount = float(request.form['amount'])

        # التحقق من أن المبلغ لا يتجاوز المتبقي
        if amount > invoice.remaining_amount:
            flash(f'المبلغ المدخل ({amount:,.2f}) أكبر من المبلغ المتبقي ({invoice.remaining_amount:,.2f})', 'danger')
            return redirect(url_for('add_payment', invoice_id=invoice_id))

        # إضافة الدفعة
        payment = InvoicePayment(
            invoice_id=invoice_id,
            amount=amount,
            payment_method=request.form.get('payment_method', 'cash'),
            reference_number=request.form.get('reference_number'),
            notes=request.form.get('notes')
        )

        if request.form.get('payment_date'):
            payment.payment_date = datetime.strptime(request.form['payment_date'], '%Y-%m-%dT%H:%M')

        db.session.add(payment)

        # تحديث حالة الفاتورة
        new_paid_amount = invoice.paid_amount + amount
        if new_paid_amount >= invoice.total_amount:
            invoice.status = 'paid'
            invoice.payment_date = payment.payment_date
        else:
            invoice.status = 'partial'

        db.session.commit()
        flash(f'تم إضافة دفعة بمبلغ {amount:,.2f} ريال للفاتورة {invoice.invoice_number}', 'success')
        return redirect(url_for('view_invoice', invoice_id=invoice_id))

    return render_template_string('''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="utf-8">
    <title>إضافة دفعة</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
    <script>
        function updateRemainingAmount() {
            const amount = parseFloat(document.getElementById('amount').value) || 0;
            const remaining = {{ invoice.remaining_amount }};
            const newRemaining = remaining - amount;

            document.getElementById('new_remaining').textContent = newRemaining.toFixed(2);

            if (amount > remaining) {
                document.getElementById('amount_warning').style.display = 'block';
                document.querySelector('button[type="submit"]').disabled = true;
            } else {
                document.getElementById('amount_warning').style.display = 'none';
                document.querySelector('button[type="submit"]').disabled = false;
            }
        }
    </script>
</head>
<body>
    <nav class="navbar navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/">🏛️ المحامي فالح بن عقاب آل عيسى</a>
            <div>
                <a class="btn btn-outline-light btn-sm" href="/view_invoice/{{ invoice.id }}">عرض الفاتورة</a>
                <a class="btn btn-outline-light btn-sm ms-2" href="/invoices">الفواتير</a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="card">
            <div class="card-header bg-success text-white">
                <h3>💰 إضافة دفعة للفاتورة: {{ invoice.invoice_number }}</h3>
            </div>
            <div class="card-body">
                <!-- ملخص الفاتورة -->
                <div class="card bg-light mb-4">
                    <div class="card-body">
                        <h5>📋 ملخص الفاتورة</h5>
                        <div class="row">
                            <div class="col-md-3">
                                <strong>العميل:</strong><br>{{ invoice.client.full_name }}
                            </div>
                            <div class="col-md-3">
                                <strong>المبلغ الإجمالي:</strong><br>{{ "{:,.2f}".format(invoice.total_amount) }} {{ riyal_svg()|safe }}
                            </div>
                            <div class="col-md-3">
                                <strong>المبلغ المدفوع:</strong><br>
                                <span class="text-success">{{ "{:,.2f}".format(invoice.paid_amount) }} {{ riyal_svg()|safe }}</span>
                            </div>
                            <div class="col-md-3">
                                <strong>المبلغ المتبقي:</strong><br>
                                <span class="text-danger">{{ "{:,.2f}".format(invoice.remaining_amount) }} {{ riyal_svg()|safe }}</span>
                            </div>
                        </div>
                        <div class="progress mt-2">
                            <div class="progress-bar bg-success" style="width: {{ invoice.payment_percentage }}%"></div>
                        </div>
                        <small class="text-muted">نسبة الدفع: {{ "{:.1f}".format(invoice.payment_percentage) }}%</small>
                    </div>
                </div>

                <form method="POST">
                    <div class="row">
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label class="form-label">مبلغ الدفعة *</label>
                                <input type="number" class="form-control" name="amount" id="amount" step="0.01"
                                       max="{{ invoice.remaining_amount }}" required onchange="updateRemainingAmount()">
                                <div id="amount_warning" class="alert alert-danger mt-2" style="display: none;">
                                    المبلغ المدخل أكبر من المبلغ المتبقي!
                                </div>
                                <small class="text-muted">الحد الأقصى: {{ "{:,.2f}".format(invoice.remaining_amount) }} {{ riyal_svg()|safe }}</small>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label class="form-label">تاريخ ووقت الدفع</label>
                                <input type="datetime-local" class="form-control" name="payment_date"
                                       value="{{ datetime.now().strftime('%Y-%m-%dT%H:%M') }}">
                            </div>
                        </div>
                    </div>

                    <div class="row">
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label class="form-label">طريقة الدفع</label>
                                <select class="form-control" name="payment_method">
                                    <option value="cash">نقداً</option>
                                    <option value="bank_transfer">تحويل بنكي</option>
                                    <option value="check">شيك</option>
                                    <option value="card">بطاقة ائتمان</option>
                                    <option value="other">أخرى</option>
                                </select>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label class="form-label">رقم المرجع</label>
                                <input type="text" class="form-control" name="reference_number"
                                       placeholder="رقم الشيك، رقم التحويل، إلخ">
                            </div>
                        </div>
                    </div>

                    <div class="mb-3">
                        <label class="form-label">ملاحظات</label>
                        <textarea class="form-control" name="notes" rows="2"
                                  placeholder="ملاحظات إضافية حول الدفعة..."></textarea>
                    </div>

                    <!-- معاينة المبلغ المتبقي -->
                    <div class="card bg-info text-white mb-3">
                        <div class="card-body">
                            <h6>💡 بعد هذه الدفعة:</h6>
                            <p class="mb-0">المبلغ المتبقي سيكون: <strong><span id="new_remaining">{{ "{:.2f}".format(invoice.remaining_amount) }}</span> {{ riyal_svg()|safe }}</strong></p>
                        </div>
                    </div>

                    <div class="text-center">
                        <button type="submit" class="btn btn-success btn-lg">💾 تسجيل الدفعة</button>
                        <a href="/view_invoice/{{ invoice.id }}" class="btn btn-secondary btn-lg ms-2">❌ إلغاء</a>
                    </div>
                </form>
            </div>
        </div>
    </div>
</body>
</html>
    ''', invoice=invoice, datetime=datetime)

@app.route('/delete_payment/<int:payment_id>')
@login_required
def delete_payment(payment_id):
    payment = InvoicePayment.query.get_or_404(payment_id)
    invoice = payment.invoice

    # حذف الدفعة
    db.session.delete(payment)

    # إعادة حساب حالة الفاتورة
    remaining_payments = InvoicePayment.query.filter_by(invoice_id=invoice.id).filter(InvoicePayment.id != payment_id).all()
    total_paid = sum(p.amount for p in remaining_payments)

    if total_paid == 0:
        invoice.status = 'pending'
        invoice.payment_date = None
    elif total_paid >= invoice.total_amount:
        invoice.status = 'paid'
        # تحديث تاريخ الدفع لآخر دفعة
        if remaining_payments:
            invoice.payment_date = max(p.payment_date for p in remaining_payments)
    else:
        invoice.status = 'partial'
        invoice.payment_date = None

    db.session.commit()
    flash(f'تم حذف الدفعة بمبلغ {payment.amount:,.2f} ريال', 'success')
    return redirect(url_for('view_invoice', invoice_id=invoice.id))

@app.route('/link_document/<int:document_id>/<int:case_id>')
@login_required
def link_document(document_id, case_id):
    document = ClientDocument.query.get_or_404(document_id)
    case = Case.query.get_or_404(case_id)

    # التحقق من أن المستند يخص نفس العميل
    if document.client_id != case.client_id:
        flash('لا يمكن ربط مستند عميل آخر بهذه القضية', 'danger')
        return redirect(url_for('view_case', case_id=case_id))

    # ربط المستند بالقضية
    document.case_id = case_id
    db.session.commit()

    flash(f'تم ربط المستند بالقضية {case.case_number} بنجاح', 'success')
    return redirect(url_for('view_case', case_id=case_id))

@app.route('/unlink_document/<int:document_id>')
@login_required
def unlink_document(document_id):
    document = ClientDocument.query.get_or_404(document_id)
    case_id = document.case_id

    # إلغاء ربط المستند بالقضية
    document.case_id = None
    db.session.commit()

    flash('تم إلغاء ربط المستند بالقضية', 'success')
    return redirect(url_for('view_case', case_id=case_id))

@app.route('/mark_paid/<int:invoice_id>')
@login_required
def mark_paid(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)

    # إضافة دفعة بالمبلغ المتبقي
    if invoice.remaining_amount > 0:
        payment = InvoicePayment(
            invoice_id=invoice_id,
            amount=invoice.remaining_amount,
            payment_method='cash',
            notes='دفع كامل'
        )
        db.session.add(payment)

    invoice.status = 'paid'
    invoice.payment_date = datetime.now()
    db.session.commit()
    flash(f'تم تحديد الفاتورة {invoice.invoice_number} كمدفوعة بالكامل', 'success')
    return redirect(url_for('invoices'))

@app.route('/users')
@login_required
@admin_required
def users():
    """صفحة إدارة المستخدمين"""
    users_list = User.query.all()
    return render_template_string('''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>إدارة المستخدمين</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="/">⚖️ نظام إدارة المكتب القانوني</a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/">الرئيسية</a>
                <a class="nav-link" href="/clients">العملاء</a>
                <a class="nav-link" href="/cases">القضايا</a>
                <a class="nav-link" href="/appointments">المواعيد</a>
                <a class="nav-link" href="/invoices">الفواتير</a>
                <a class="nav-link active" href="/users">المستخدمين</a>
                <a class="nav-link" href="/logout">خروج</a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="row">
            <div class="col-12">
                <div class="card">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h5 class="mb-0">👥 إدارة المستخدمين</h5>
                        <a href="/add_user" class="btn btn-success">
                            <i class="fas fa-plus"></i> إضافة مستخدم جديد
                        </a>
                    </div>
                    <div class="card-body">
                        {% with messages = get_flashed_messages(with_categories=true) %}
                            {% if messages %}
                                {% for category, message in messages %}
                                    <div class="alert alert-{{ 'danger' if category == 'error' else category }} alert-dismissible fade show">
                                        {{ message }}
                                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                                    </div>
                                {% endfor %}
                            {% endif %}
                        {% endwith %}

                        {% if users_list %}
                        <div class="table-responsive">
                            <table class="table table-striped">
                                <thead>
                                    <tr>
                                        <th>الرقم</th>
                                        <th>اسم المستخدم</th>
                                        <th>الاسم الكامل</th>
                                        <th>الدور</th>
                                        <th>تاريخ الإنشاء</th>
                                        <th>الإجراءات</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for user in users_list %}
                                    <tr>
                                        <td>{{ user.id }}</td>
                                        <td>
                                            <strong>{{ user.username }}</strong>
                                            {% if user.id == current_user.id %}
                                            <span class="badge bg-primary">أنت</span>
                                            {% endif %}
                                        </td>
                                        <td>{{ user.full_name }}</td>
                                        <td>
                                            {% if user.role == 'admin' %}
                                            <span class="badge bg-danger">👑 {{ user.role_name }}</span>
                                            {% elif user.role == 'lawyer' %}
                                            <span class="badge bg-success">⚖️ {{ user.role_name }}</span>
                                            {% elif user.role == 'secretary' %}
                                            <span class="badge bg-info">📝 {{ user.role_name }}</span>
                                            {% else %}
                                            <span class="badge bg-secondary">{{ user.role_name }}</span>
                                            {% endif %}
                                        </td>
                                        <td>{{ user.created_at.strftime('%Y-%m-%d') if user.created_at else 'غير محدد' }}</td>
                                        <td>
                                            <div class="btn-group btn-group-sm" role="group">
                                                <a href="/edit_user/{{ user.id }}" class="btn btn-outline-warning">
                                                    <i class="fas fa-edit"></i> تعديل
                                                </a>
                                                {% if user.id != current_user.id %}
                                                <a href="/delete_user/{{ user.id }}" class="btn btn-outline-danger"
                                                   onclick="return confirm('هل أنت متأكد من حذف المستخدم {{ user.username }}؟')">
                                                    <i class="fas fa-trash"></i> حذف
                                                </a>
                                                {% endif %}
                                            </div>
                                        </td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                        {% else %}
                        <div class="text-center py-4">
                            <i class="fas fa-users fa-3x text-muted mb-3"></i>
                            <h5 class="text-muted">لا يوجد مستخدمين</h5>
                            <a href="/add_user" class="btn btn-success">إضافة مستخدم جديد</a>
                        </div>
                        {% endif %}
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
    ''', users_list=users_list)

@app.route('/add_user', methods=['GET', 'POST'])
@login_required
@admin_required
def add_user():
    """إضافة مستخدم جديد"""
    if request.method == 'POST':
        username = request.form['username']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        role = request.form['role']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # التحقق من صحة البيانات
        if not all([username, first_name, last_name, role, password, confirm_password]):
            flash('جميع الحقول مطلوبة', 'danger')
        elif password != confirm_password:
            flash('كلمة المرور وتأكيدها غير متطابقتين', 'danger')
        elif len(password) < 6:
            flash('كلمة المرور يجب أن تكون 6 أحرف على الأقل', 'danger')
        elif User.query.filter_by(username=username).first():
            flash('اسم المستخدم موجود بالفعل', 'danger')
        elif role not in ['admin', 'lawyer', 'secretary']:
            flash('الدور المحدد غير صحيح', 'danger')
        else:
            # إنشاء المستخدم الجديد
            new_user = User(
                username=username,
                first_name=first_name,
                last_name=last_name,
                role=role
            )
            new_user.set_password(password)

            db.session.add(new_user)
            db.session.commit()

            flash(f'تم إضافة المستخدم {username} بدور {new_user.role_name} بنجاح', 'success')
            return redirect(url_for('users'))

    return render_template_string('''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>إضافة مستخدم جديد</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="/">⚖️ نظام إدارة المكتب القانوني</a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/">الرئيسية</a>
                <a class="nav-link" href="/users">المستخدمين</a>
                <a class="nav-link" href="/logout">خروج</a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="row justify-content-center">
            <div class="col-md-8">
                <div class="card">
                    <div class="card-header">
                        <h5 class="mb-0">
                            <i class="fas fa-user-plus"></i> إضافة مستخدم جديد
                        </h5>
                    </div>
                    <div class="card-body">
                        {% with messages = get_flashed_messages(with_categories=true) %}
                            {% if messages %}
                                {% for category, message in messages %}
                                    <div class="alert alert-{{ 'danger' if category == 'error' else category }} alert-dismissible fade show">
                                        {{ message }}
                                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                                    </div>
                                {% endfor %}
                            {% endif %}
                        {% endwith %}

                        <form method="POST">
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">اسم المستخدم *</label>
                                        <input type="text" class="form-control" name="username" required
                                               placeholder="أدخل اسم المستخدم">
                                        <small class="text-muted">يجب أن يكون فريداً</small>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">الاسم الأول *</label>
                                        <input type="text" class="form-control" name="first_name" required
                                               placeholder="أدخل الاسم الأول">
                                    </div>
                                </div>
                            </div>

                            <div class="row">
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">اسم العائلة *</label>
                                        <input type="text" class="form-control" name="last_name" required
                                               placeholder="أدخل اسم العائلة">
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">الدور *</label>
                                        <select class="form-control" name="role" required>
                                            <option value="">اختر الدور</option>
                                            <option value="admin">👑 مدير النظام</option>
                                            <option value="lawyer">⚖️ محامي</option>
                                            <option value="secretary">📝 سكرتير</option>
                                        </select>
                                        <small class="text-muted">يحدد صلاحيات المستخدم</small>
                                    </div>
                                </div>
                            </div>

                            <div class="row">
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">كلمة المرور *</label>
                                        <input type="password" class="form-control" name="password" required
                                               placeholder="أدخل كلمة المرور" minlength="6">
                                        <small class="text-muted">6 أحرف على الأقل</small>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">تأكيد كلمة المرور *</label>
                                        <input type="password" class="form-control" name="confirm_password" required
                                               placeholder="أعد إدخال كلمة المرور">
                                    </div>
                                </div>
                            </div>

                            <div class="d-grid gap-2 d-md-flex justify-content-md-end">
                                <a href="/users" class="btn btn-secondary me-md-2">إلغاء</a>
                                <button type="submit" class="btn btn-success">
                                    <i class="fas fa-save"></i> إضافة المستخدم
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
    ''')

@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    """تعديل بيانات المستخدم"""
    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        username = request.form['username']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        role = request.form['role']
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        # التحقق من صحة البيانات
        if not all([username, first_name, last_name, role]):
            flash('الحقول الأساسية مطلوبة', 'danger')
        elif username != user.username and User.query.filter_by(username=username).first():
            flash('اسم المستخدم موجود بالفعل', 'danger')
        elif role not in ['admin', 'lawyer', 'secretary']:
            flash('الدور المحدد غير صحيح', 'danger')
        elif new_password and len(new_password) < 6:
            flash('كلمة المرور يجب أن تكون 6 أحرف على الأقل', 'danger')
        elif new_password and new_password != confirm_password:
            flash('كلمة المرور وتأكيدها غير متطابقتين', 'danger')
        else:
            # تحديث البيانات
            user.username = username
            user.first_name = first_name
            user.last_name = last_name
            user.role = role

            # تحديث كلمة المرور إذا تم إدخال واحدة جديدة
            if new_password:
                user.set_password(new_password)

            db.session.commit()

            flash(f'تم تحديث بيانات المستخدم {username} بدور {user.role_name} بنجاح', 'success')
            return redirect(url_for('users'))

    return render_template_string('''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تعديل المستخدم</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="/">⚖️ نظام إدارة المكتب القانوني</a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/">الرئيسية</a>
                <a class="nav-link" href="/users">المستخدمين</a>
                <a class="nav-link" href="/logout">خروج</a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="row justify-content-center">
            <div class="col-md-8">
                <div class="card">
                    <div class="card-header">
                        <h5 class="mb-0">
                            <i class="fas fa-user-edit"></i> تعديل المستخدم: {{ user.username }}
                            {% if user.id == current_user.id %}
                            <span class="badge bg-primary">أنت</span>
                            {% endif %}
                        </h5>
                    </div>
                    <div class="card-body">
                        {% with messages = get_flashed_messages(with_categories=true) %}
                            {% if messages %}
                                {% for category, message in messages %}
                                    <div class="alert alert-{{ 'danger' if category == 'error' else category }} alert-dismissible fade show">
                                        {{ message }}
                                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                                    </div>
                                {% endfor %}
                            {% endif %}
                        {% endwith %}

                        <form method="POST">
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">اسم المستخدم *</label>
                                        <input type="text" class="form-control" name="username" required
                                               value="{{ user.username }}" placeholder="أدخل اسم المستخدم">
                                        <small class="text-muted">يجب أن يكون فريداً</small>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">الاسم الأول *</label>
                                        <input type="text" class="form-control" name="first_name" required
                                               value="{{ user.first_name }}" placeholder="أدخل الاسم الأول">
                                    </div>
                                </div>
                            </div>

                            <div class="row">
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">اسم العائلة *</label>
                                        <input type="text" class="form-control" name="last_name" required
                                               value="{{ user.last_name }}" placeholder="أدخل اسم العائلة">
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">الدور *</label>
                                        <select class="form-control" name="role" required>
                                            <option value="admin" {{ 'selected' if user.role == 'admin' else '' }}>👑 مدير النظام</option>
                                            <option value="lawyer" {{ 'selected' if user.role == 'lawyer' else '' }}>⚖️ محامي</option>
                                            <option value="secretary" {{ 'selected' if user.role == 'secretary' else '' }}>📝 سكرتير</option>
                                        </select>
                                        <small class="text-muted">الدور الحالي: {{ user.role_name }}</small>
                                    </div>
                                </div>
                            </div>

                            <hr>
                            <h6 class="text-muted">تغيير كلمة المرور (اختياري)</h6>

                            <div class="row">
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">كلمة المرور الجديدة</label>
                                        <input type="password" class="form-control" name="new_password"
                                               placeholder="اتركه فارغاً إذا لم ترد تغييرها" minlength="6">
                                        <small class="text-muted">6 أحرف على الأقل</small>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">تأكيد كلمة المرور الجديدة</label>
                                        <input type="password" class="form-control" name="confirm_password"
                                               placeholder="أعد إدخال كلمة المرور الجديدة">
                                    </div>
                                </div>
                            </div>

                            <div class="d-grid gap-2 d-md-flex justify-content-md-end">
                                <a href="/users" class="btn btn-secondary me-md-2">إلغاء</a>
                                <button type="submit" class="btn btn-warning">
                                    <i class="fas fa-save"></i> حفظ التغييرات
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
    ''', user=user)

@app.route('/profile')
@login_required
def profile():
    """عرض الملف الشخصي"""
    return render_template_string('''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="utf-8">
    <title>الملف الشخصي - {{ office_settings.office_name }}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-dark bg-dark">
        <div class="container">
            {% if office_settings.logo_path %}
                <a class="navbar-brand d-flex align-items-center" href="/">
                    <img src="/uploads/{{ office_settings.logo_path }}" alt="شعار المكتب" style="height: 40px; margin-left: 10px;">
                    <span>{{ office_settings.office_name }}</span>
                </a>
            {% else %}
                <a class="navbar-brand" href="/">
                    <i class="fas fa-balance-scale me-2"></i>
                    {{ office_settings.office_name }}
                </a>
            {% endif %}
            <div>
                <a class="btn btn-outline-light btn-sm" href="/">الرئيسية</a>
                <a class="btn btn-outline-light btn-sm ms-2" href="/logout">تسجيل الخروج</a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="row">
            <div class="col-lg-8">
                <div class="card">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h5 class="mb-0">👤 الملف الشخصي</h5>
                        <a href="/edit_profile" class="btn btn-primary btn-sm">
                            <i class="fas fa-edit me-1"></i>تعديل
                        </a>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-6">
                                <table class="table table-borderless">
                                    <tr>
                                        <th width="40%">الاسم الكامل:</th>
                                        <td><strong>{{ current_user.first_name }} {{ current_user.last_name }}</strong></td>
                                    </tr>
                                    <tr>
                                        <th>البريد الإلكتروني:</th>
                                        <td>{{ current_user.email }}</td>
                                    </tr>
                                    <tr>
                                        <th>رقم الهاتف:</th>
                                        <td>{{ current_user.phone or 'غير محدد' }}</td>
                                    </tr>
                                    <tr>
                                        <th>الدور:</th>
                                        <td>
                                            <span class="badge bg-primary">
                                                {% if current_user.role == 'admin' %}مدير
                                                {% elif current_user.role == 'lawyer' %}محامي
                                                {% elif current_user.role == 'secretary' %}سكرتير
                                                {% else %}{{ current_user.role }}{% endif %}
                                            </span>
                                        </td>
                                    </tr>
                                    <tr>
                                        <th>تاريخ الانضمام:</th>
                                        <td>{{ current_user.created_at.strftime('%Y-%m-%d') if current_user.created_at else 'غير محدد' }}</td>
                                    </tr>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="col-lg-4">
                <div class="card">
                    <div class="card-header">
                        <h5 class="mb-0">إجراءات سريعة</h5>
                    </div>
                    <div class="card-body">
                        <div class="d-grid gap-2">
                            <a href="/edit_profile" class="btn btn-primary">
                                <i class="fas fa-edit me-2"></i>تعديل الملف الشخصي
                            </a>
                            <a href="/" class="btn btn-outline-secondary">
                                <i class="fas fa-home me-2"></i>الصفحة الرئيسية
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
    ''', office_settings=OfficeSettings.get_settings())

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """تعديل الملف الشخصي"""
    if request.method == 'POST':
        # التحقق من صحة البيانات
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()

        if not first_name or not last_name or not email:
            flash('الاسم الأول والأخير والبريد الإلكتروني مطلوبة', 'danger')
        else:
            # التحقق من عدم تكرار البريد الإلكتروني
            existing_user = User.query.filter(User.email == email, User.id != current_user.id).first()
            if existing_user:
                flash('البريد الإلكتروني مستخدم بالفعل', 'danger')
            else:
                # تحديث البيانات
                current_user.first_name = first_name
                current_user.last_name = last_name
                current_user.email = email
                current_user.phone = phone
                current_user.updated_at = datetime.utcnow()

                db.session.commit()
                flash('تم حفظ التغييرات بنجاح', 'success')
                return redirect('/profile')

    return render_template_string('''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="utf-8">
    <title>تعديل الملف الشخصي - {{ office_settings.office_name }}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-dark bg-dark">
        <div class="container">
            {% if office_settings.logo_path %}
                <a class="navbar-brand d-flex align-items-center" href="/">
                    <img src="/uploads/{{ office_settings.logo_path }}" alt="شعار المكتب" style="height: 40px; margin-left: 10px;">
                    <span>{{ office_settings.office_name }}</span>
                </a>
            {% else %}
                <a class="navbar-brand" href="/">
                    <i class="fas fa-balance-scale me-2"></i>
                    {{ office_settings.office_name }}
                </a>
            {% endif %}
            <div>
                <a class="btn btn-outline-light btn-sm" href="/profile">الملف الشخصي</a>
                <a class="btn btn-outline-light btn-sm ms-2" href="/">الرئيسية</a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="row justify-content-center">
            <div class="col-md-8">
                <div class="card">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h5 class="mb-0">✏️ تعديل الملف الشخصي</h5>
                        <a href="/profile" class="btn btn-outline-secondary btn-sm">
                            <i class="fas fa-arrow-right me-1"></i>العودة
                        </a>
                    </div>
                    <div class="card-body">
                        <form method="POST">
                            <div class="row">
                                <div class="col-md-6 mb-3">
                                    <label class="form-label">الاسم الأول *</label>
                                    <input type="text" class="form-control" name="first_name"
                                           value="{{ current_user.first_name }}" required>
                                </div>
                                <div class="col-md-6 mb-3">
                                    <label class="form-label">الاسم الأخير *</label>
                                    <input type="text" class="form-control" name="last_name"
                                           value="{{ current_user.last_name }}" required>
                                </div>
                            </div>

                            <div class="row">
                                <div class="col-md-6 mb-3">
                                    <label class="form-label">البريد الإلكتروني *</label>
                                    <input type="email" class="form-control" name="email"
                                           value="{{ current_user.email }}" required>
                                </div>
                                <div class="col-md-6 mb-3">
                                    <label class="form-label">رقم الهاتف</label>
                                    <input type="text" class="form-control" name="phone"
                                           value="{{ current_user.phone or '' }}">
                                </div>
                            </div>

                            <div class="d-flex justify-content-between">
                                <a href="/profile" class="btn btn-secondary">إلغاء</a>
                                <button type="submit" class="btn btn-primary">
                                    <i class="fas fa-save me-1"></i>حفظ التغييرات
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
    ''', office_settings=OfficeSettings.get_settings())

@app.route('/delete_user/<int:user_id>')
@login_required
@admin_required
def delete_user(user_id):
    """حذف المستخدم"""
    user = User.query.get_or_404(user_id)

    # منع المستخدم من حذف نفسه
    if user.id == current_user.id:
        flash('لا يمكنك حذف حسابك الخاص', 'danger')
        return redirect(url_for('users'))

    # منع حذف آخر مستخدم في النظام
    if User.query.count() <= 1:
        flash('لا يمكن حذف آخر مستخدم في النظام', 'danger')
        return redirect(url_for('users'))

    username = user.username
    db.session.delete(user)
    db.session.commit()

    flash(f'تم حذف المستخدم {username} بنجاح', 'success')
    return redirect(url_for('users'))

@app.route('/expenses')
@login_required
def expenses():
    """صفحة عرض المصروفات"""
    # الحصول على المصروفات مع إمكانية التصفية
    filter_type = request.args.get('filter', 'all')
    search_query = request.args.get('search', '')

    query = Expense.query

    # تطبيق البحث
    if search_query:
        query = query.filter(
            db.or_(
                Expense.title.contains(search_query),
                Expense.description.contains(search_query),
                Expense.vendor.contains(search_query),
                Expense.category.contains(search_query)
            )
        )

    # تطبيق التصفية حسب الفئة
    if filter_type != 'all':
        query = query.filter(Expense.category == filter_type)

    # ترتيب حسب التاريخ (الأحدث أولاً)
    expenses = query.order_by(Expense.expense_date.desc()).all()

    # حساب إجمالي المصروفات
    total_expenses = sum(expense.amount for expense in expenses)

    # حساب المصروفات حسب الفئة
    categories_stats = {}
    for expense in expenses:
        if expense.category not in categories_stats:
            categories_stats[expense.category] = 0
        categories_stats[expense.category] += expense.amount

    # الحصول على إعدادات المكتب
    office_settings = OfficeSettings.get_settings()

    return render_template_string('''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>إدارة المصروفات - {{ office_settings.office_name }}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Cairo', sans-serif; background: #f8f9fa; }
        .expense-card { transition: transform 0.2s; }
        .expense-card:hover { transform: translateY(-2px); }
        .category-badge { font-size: 0.8em; }
        .stats-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            {{ get_navbar_brand_global()|safe }}
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav me-auto">
                    <li class="nav-item">
                        <a class="nav-link" href="/">
                            <i class="fas fa-home me-1"></i>الرئيسية
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/clients">
                            <i class="fas fa-users me-1"></i>العملاء
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/cases">
                            <i class="fas fa-folder-open me-1"></i>القضايا
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/appointments">
                            <i class="fas fa-calendar-alt me-1"></i>المواعيد
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/invoices">
                            <i class="fas fa-file-invoice-dollar me-1"></i>الفواتير
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link active" href="/expenses">
                            <i class="fas fa-money-bill-wave me-1"></i>المصروفات
                        </a>
                    </li>
                </ul>
                <ul class="navbar-nav">
                    <li class="nav-item dropdown">
                        <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown">
                            <i class="fas fa-user me-1"></i>{{ current_user.first_name }}
                        </a>
                        <ul class="dropdown-menu">
                            <li><a class="dropdown-item" href="/logout">تسجيل الخروج</a></li>
                        </ul>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <!-- إحصائيات سريعة -->
        <div class="row mb-4">
            <div class="col-md-3">
                <div class="card stats-card">
                    <div class="card-body text-center">
                        <i class="fas fa-money-bill-wave fa-2x mb-2"></i>
                        <h4>{{ "{:,.2f}".format(total_expenses) }} {{ riyal_svg()|safe }}</h4>
                        <p class="mb-0">إجمالي المصروفات</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card bg-info text-white">
                    <div class="card-body text-center">
                        <i class="fas fa-list fa-2x mb-2"></i>
                        <h4>{{ expenses|length }}</h4>
                        <p class="mb-0">عدد المصروفات</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card bg-warning text-white">
                    <div class="card-body text-center">
                        <i class="fas fa-tags fa-2x mb-2"></i>
                        <h4>{{ categories_stats|length }}</h4>
                        <p class="mb-0">عدد الفئات</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card bg-success text-white">
                    <div class="card-body text-center">
                        <i class="fas fa-calendar fa-2x mb-2"></i>
                        <h4>{{ expenses|selectattr('expense_date')|selectattr('expense_date', 'ge', (datetime.now() - timedelta(days=30)))|list|length }}</h4>
                        <p class="mb-0">هذا الشهر</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- رأس الصفحة مع أدوات التحكم -->
        <div class="card">
            <div class="card-header d-flex justify-content-between align-items-center">
                <h3><i class="fas fa-money-bill-wave me-2"></i>إدارة المصروفات</h3>
                <div>
                    <div class="btn-group me-2" role="group">
                        <a href="/expenses" class="btn btn-outline-secondary {{ 'active' if not request.args.get('filter') or request.args.get('filter') == 'all' else '' }}">الكل</a>
                        <a href="/expenses?filter=مكتبية" class="btn btn-outline-primary {{ 'active' if request.args.get('filter') == 'مكتبية' else '' }}">مكتبية</a>
                        <a href="/expenses?filter=قانونية" class="btn btn-outline-info {{ 'active' if request.args.get('filter') == 'قانونية' else '' }}">قانونية</a>
                        <a href="/expenses?filter=تشغيلية" class="btn btn-outline-warning {{ 'active' if request.args.get('filter') == 'تشغيلية' else '' }}">تشغيلية</a>
                        <a href="/expenses?filter=أخرى" class="btn btn-outline-secondary {{ 'active' if request.args.get('filter') == 'أخرى' else '' }}">أخرى</a>
                    </div>
                    <a href="/add_expense" class="btn btn-primary">
                        <i class="fas fa-plus me-1"></i>إضافة مصروف
                    </a>
                </div>
            </div>
            <div class="card-body">
                <!-- شريط البحث -->
                <form method="GET" class="mb-4">
                    <div class="row">
                        <div class="col-md-8">
                            <input type="text" class="form-control" name="search"
                                   placeholder="البحث في المصروفات..."
                                   value="{{ request.args.get('search', '') }}">
                        </div>
                        <div class="col-md-4">
                            <button type="submit" class="btn btn-outline-primary">
                                <i class="fas fa-search me-1"></i>بحث
                            </button>
                            {% if request.args.get('search') %}
                            <a href="/expenses" class="btn btn-outline-secondary">
                                <i class="fas fa-times me-1"></i>مسح
                            </a>
                            {% endif %}
                        </div>
                    </div>
                </form>

                <!-- قائمة المصروفات -->
                {% if expenses %}
                <div class="row">
                    {% for expense in expenses %}
                    <div class="col-md-6 col-lg-4 mb-3">
                        <div class="card expense-card h-100">
                            <div class="card-body">
                                <div class="d-flex justify-content-between align-items-start mb-2">
                                    <h6 class="card-title mb-0">{{ expense.title }}</h6>
                                    <span class="badge bg-primary category-badge">{{ expense.category }}</span>
                                </div>

                                <p class="text-muted small mb-2">{{ expense.description or 'لا يوجد وصف' }}</p>

                                <div class="mb-2">
                                    <strong class="text-danger">{{ "{:,.2f}".format(expense.amount) }} {{ riyal_svg()|safe }}</strong>
                                </div>

                                <div class="small text-muted mb-2">
                                    <i class="fas fa-calendar me-1"></i>{{ expense.expense_date.strftime('%Y-%m-%d') }}
                                    {% if expense.vendor %}
                                    <br><i class="fas fa-store me-1"></i>{{ expense.vendor }}
                                    {% endif %}
                                </div>

                                <div class="d-flex justify-content-between align-items-center">
                                    <small class="text-muted">{{ expense.payment_method }}</small>
                                    <div class="btn-group btn-group-sm">
                                        <a href="/edit_expense/{{ expense.id }}" class="btn btn-outline-warning btn-sm">
                                            <i class="fas fa-edit"></i>
                                        </a>
                                        <a href="/delete_expense/{{ expense.id }}" class="btn btn-outline-danger btn-sm"
                                           onclick="return confirm('هل أنت متأكد من حذف هذا المصروف؟')">
                                            <i class="fas fa-trash"></i>
                                        </a>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    {% endfor %}
                </div>
                {% else %}
                <div class="text-center py-5">
                    <i class="fas fa-money-bill-wave fa-3x text-muted mb-3"></i>
                    <h5 class="text-muted">لا توجد مصروفات</h5>
                    <p class="text-muted">ابدأ بإضافة أول مصروف للمكتب</p>
                    <a href="/add_expense" class="btn btn-primary">
                        <i class="fas fa-plus me-1"></i>إضافة مصروف جديد
                    </a>
                </div>
                {% endif %}
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
    ''', expenses=expenses, total_expenses=total_expenses, categories_stats=categories_stats,
         office_settings=office_settings, datetime=datetime, timedelta=timedelta)

@app.route('/add_expense', methods=['GET', 'POST'])
@login_required
def add_expense():
    """صفحة إضافة مصروف جديد"""
    if request.method == 'POST':
        try:
            # إنشاء مصروف جديد
            expense = Expense(
                title=request.form['title'],
                description=request.form.get('description', ''),
                amount=float(request.form['amount']),
                category=request.form['category'],
                expense_date=datetime.strptime(request.form['expense_date'], '%Y-%m-%d'),
                receipt_number=request.form.get('receipt_number', ''),
                vendor=request.form.get('vendor', ''),
                payment_method=request.form.get('payment_method', 'نقدي'),
                notes=request.form.get('notes', ''),
                created_by=current_user.id
            )

            db.session.add(expense)
            db.session.commit()

            flash(f'تم إضافة المصروف "{expense.title}" بنجاح', 'success')
            return redirect(url_for('expenses'))

        except Exception as e:
            flash(f'حدث خطأ أثناء إضافة المصروف: {str(e)}', 'error')

    office_settings = OfficeSettings.get_settings()

    return render_template_string('''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="utf-8">
    <title>إضافة مصروف جديد</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        body { font-family: 'Cairo', sans-serif; background: #f8f9fa; }
    </style>
</head>
<body>
    <nav class="navbar navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/">🏛️ {{ office_settings.office_name }}</a>
            <div>
                <a class="btn btn-outline-light btn-sm" href="/expenses">المصروفات</a>
                <a class="btn btn-outline-light btn-sm ms-2" href="/">الرئيسية</a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="row justify-content-center">
            <div class="col-md-8">
                <div class="card">
                    <div class="card-header">
                        <h3><i class="fas fa-plus me-2"></i>إضافة مصروف جديد</h3>
                    </div>
                    <div class="card-body">
                        {% with messages = get_flashed_messages(with_categories=true) %}
                            {% if messages %}
                                {% for category, message in messages %}
                                    <div class="alert alert-{{ 'danger' if category == 'error' else 'success' }} alert-dismissible fade show">
                                        {{ message }}
                                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                                    </div>
                                {% endfor %}
                            {% endif %}
                        {% endwith %}

                        <form method="POST">
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">عنوان المصروف *</label>
                                        <input type="text" class="form-control" name="title" required
                                               placeholder="مثال: أوراق وقرطاسية">
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">المبلغ *</label>
                                        <div class="input-group">
                                            <input type="number" class="form-control" name="amount" step="0.01" required
                                                   placeholder="0.00">
                                            <span class="input-group-text">{{ riyal_svg()|safe }}</span>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="row">
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">فئة المصروف *</label>
                                        <select class="form-select" name="category" required>
                                            <option value="">اختر الفئة</option>
                                            <option value="مكتبية">مكتبية</option>
                                            <option value="قانونية">قانونية</option>
                                            <option value="تشغيلية">تشغيلية</option>
                                            <option value="صيانة">صيانة</option>
                                            <option value="اتصالات">اتصالات</option>
                                            <option value="مواصلات">مواصلات</option>
                                            <option value="ضيافة">ضيافة</option>
                                            <option value="أخرى">أخرى</option>
                                        </select>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">تاريخ المصروف *</label>
                                        <input type="date" class="form-control" name="expense_date" required
                                               value="{{ datetime.now().strftime('%Y-%m-%d') }}">
                                    </div>
                                </div>
                            </div>

                            <div class="row">
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">رقم الإيصال</label>
                                        <input type="text" class="form-control" name="receipt_number"
                                               placeholder="رقم الإيصال أو الفاتورة">
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">المورد/الجهة</label>
                                        <input type="text" class="form-control" name="vendor"
                                               placeholder="اسم المتجر أو المورد">
                                    </div>
                                </div>
                            </div>

                            <div class="row">
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">طريقة الدفع</label>
                                        <select class="form-select" name="payment_method">
                                            <option value="نقدي">نقدي</option>
                                            <option value="بطاقة ائتمان">بطاقة ائتمان</option>
                                            <option value="بطاقة مدين">بطاقة مدين</option>
                                            <option value="تحويل بنكي">تحويل بنكي</option>
                                            <option value="شيك">شيك</option>
                                        </select>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">وصف المصروف</label>
                                        <textarea class="form-control" name="description" rows="3"
                                                  placeholder="وصف تفصيلي للمصروف..."></textarea>
                                    </div>
                                </div>
                            </div>

                            <div class="mb-3">
                                <label class="form-label">ملاحظات إضافية</label>
                                <textarea class="form-control" name="notes" rows="2"
                                          placeholder="أي ملاحظات إضافية..."></textarea>
                            </div>

                            <div class="text-center">
                                <button type="submit" class="btn btn-primary btn-lg">
                                    <i class="fas fa-save me-1"></i>حفظ المصروف
                                </button>
                                <a href="/expenses" class="btn btn-secondary btn-lg ms-2">
                                    <i class="fas fa-times me-1"></i>إلغاء
                                </a>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
    ''', office_settings=office_settings, datetime=datetime)

@app.route('/edit_expense/<int:expense_id>', methods=['GET', 'POST'])
@login_required
def edit_expense(expense_id):
    """صفحة تعديل مصروف"""
    expense = Expense.query.get_or_404(expense_id)

    if request.method == 'POST':
        try:
            expense.title = request.form['title']
            expense.description = request.form.get('description', '')
            expense.amount = float(request.form['amount'])
            expense.category = request.form['category']
            expense.expense_date = datetime.strptime(request.form['expense_date'], '%Y-%m-%d')
            expense.receipt_number = request.form.get('receipt_number', '')
            expense.vendor = request.form.get('vendor', '')
            expense.payment_method = request.form.get('payment_method', 'نقدي')
            expense.notes = request.form.get('notes', '')
            expense.updated_at = datetime.utcnow()

            db.session.commit()

            flash(f'تم تحديث المصروف "{expense.title}" بنجاح', 'success')
            return redirect(url_for('expenses'))

        except Exception as e:
            flash(f'حدث خطأ أثناء تحديث المصروف: {str(e)}', 'error')

    office_settings = OfficeSettings.get_settings()

    return render_template_string('''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="utf-8">
    <title>تعديل المصروف</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        body { font-family: 'Cairo', sans-serif; background: #f8f9fa; }
    </style>
</head>
<body>
    <nav class="navbar navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/">🏛️ {{ office_settings.office_name }}</a>
            <div>
                <a class="btn btn-outline-light btn-sm" href="/expenses">المصروفات</a>
                <a class="btn btn-outline-light btn-sm ms-2" href="/">الرئيسية</a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="row justify-content-center">
            <div class="col-md-8">
                <div class="card">
                    <div class="card-header">
                        <h3><i class="fas fa-edit me-2"></i>تعديل المصروف</h3>
                    </div>
                    <div class="card-body">
                        {% with messages = get_flashed_messages(with_categories=true) %}
                            {% if messages %}
                                {% for category, message in messages %}
                                    <div class="alert alert-{{ 'danger' if category == 'error' else 'success' }} alert-dismissible fade show">
                                        {{ message }}
                                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                                    </div>
                                {% endfor %}
                            {% endif %}
                        {% endwith %}

                        <form method="POST">
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">عنوان المصروف *</label>
                                        <input type="text" class="form-control" name="title" required
                                               value="{{ expense.title }}">
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">المبلغ *</label>
                                        <div class="input-group">
                                            <input type="number" class="form-control" name="amount" step="0.01" required
                                                   value="{{ expense.amount }}">
                                            <span class="input-group-text">{{ riyal_svg()|safe }}</span>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="row">
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">فئة المصروف *</label>
                                        <select class="form-select" name="category" required>
                                            <option value="مكتبية" {{ 'selected' if expense.category == 'مكتبية' else '' }}>مكتبية</option>
                                            <option value="قانونية" {{ 'selected' if expense.category == 'قانونية' else '' }}>قانونية</option>
                                            <option value="تشغيلية" {{ 'selected' if expense.category == 'تشغيلية' else '' }}>تشغيلية</option>
                                            <option value="صيانة" {{ 'selected' if expense.category == 'صيانة' else '' }}>صيانة</option>
                                            <option value="اتصالات" {{ 'selected' if expense.category == 'اتصالات' else '' }}>اتصالات</option>
                                            <option value="مواصلات" {{ 'selected' if expense.category == 'مواصلات' else '' }}>مواصلات</option>
                                            <option value="ضيافة" {{ 'selected' if expense.category == 'ضيافة' else '' }}>ضيافة</option>
                                            <option value="أخرى" {{ 'selected' if expense.category == 'أخرى' else '' }}>أخرى</option>
                                        </select>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">تاريخ المصروف *</label>
                                        <input type="date" class="form-control" name="expense_date" required
                                               value="{{ expense.expense_date.strftime('%Y-%m-%d') }}">
                                    </div>
                                </div>
                            </div>

                            <div class="row">
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">رقم الإيصال</label>
                                        <input type="text" class="form-control" name="receipt_number"
                                               value="{{ expense.receipt_number or '' }}">
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">المورد/الجهة</label>
                                        <input type="text" class="form-control" name="vendor"
                                               value="{{ expense.vendor or '' }}">
                                    </div>
                                </div>
                            </div>

                            <div class="row">
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">طريقة الدفع</label>
                                        <select class="form-select" name="payment_method">
                                            <option value="نقدي" {{ 'selected' if expense.payment_method == 'نقدي' else '' }}>نقدي</option>
                                            <option value="بطاقة ائتمان" {{ 'selected' if expense.payment_method == 'بطاقة ائتمان' else '' }}>بطاقة ائتمان</option>
                                            <option value="بطاقة مدين" {{ 'selected' if expense.payment_method == 'بطاقة مدين' else '' }}>بطاقة مدين</option>
                                            <option value="تحويل بنكي" {{ 'selected' if expense.payment_method == 'تحويل بنكي' else '' }}>تحويل بنكي</option>
                                            <option value="شيك" {{ 'selected' if expense.payment_method == 'شيك' else '' }}>شيك</option>
                                        </select>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">وصف المصروف</label>
                                        <textarea class="form-control" name="description" rows="3">{{ expense.description or '' }}</textarea>
                                    </div>
                                </div>
                            </div>

                            <div class="mb-3">
                                <label class="form-label">ملاحظات إضافية</label>
                                <textarea class="form-control" name="notes" rows="2">{{ expense.notes or '' }}</textarea>
                            </div>

                            <div class="text-center">
                                <button type="submit" class="btn btn-warning btn-lg">
                                    <i class="fas fa-save me-1"></i>حفظ التعديلات
                                </button>
                                <a href="/expenses" class="btn btn-secondary btn-lg ms-2">
                                    <i class="fas fa-times me-1"></i>إلغاء
                                </a>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
    ''', expense=expense, office_settings=office_settings)

@app.route('/delete_expense/<int:expense_id>')
@login_required
def delete_expense(expense_id):
    """حذف مصروف"""
    expense = Expense.query.get_or_404(expense_id)

    try:
        expense_title = expense.title
        db.session.delete(expense)
        db.session.commit()

        flash(f'تم حذف المصروف "{expense_title}" بنجاح', 'success')
    except Exception as e:
        flash(f'حدث خطأ أثناء حذف المصروف: {str(e)}', 'error')

    return redirect(url_for('expenses'))



@app.route('/reports')
@login_required
def reports():
    # إحصائيات عامة
    total_clients = Client.query.count()
    total_cases = Case.query.count()
    active_cases = Case.query.filter_by(status='active').count()
    closed_cases = Case.query.filter_by(status='closed').count()

    total_invoices = Invoice.query.count()
    pending_invoices = Invoice.query.filter_by(status='pending').count()
    paid_invoices = Invoice.query.filter_by(status='paid').count()

    # إحصائيات مالية
    total_revenue = db.session.query(db.func.sum(Invoice.total_amount)).filter_by(status='paid').scalar() or 0
    pending_amount = db.session.query(db.func.sum(Invoice.total_amount)).filter_by(status='pending').scalar() or 0

    # إحصائيات شهرية
    current_month = datetime.now().month
    current_year = datetime.now().year
    monthly_revenue = db.session.query(db.func.sum(Invoice.total_amount)).filter(
        Invoice.status == 'paid',
        db.extract('month', Invoice.payment_date) == current_month,
        db.extract('year', Invoice.payment_date) == current_year
    ).scalar() or 0

    # أحدث العملاء
    recent_clients = Client.query.order_by(Client.created_at.desc()).limit(5).all()

    # القضايا النشطة
    active_cases_list = Case.query.filter_by(status='active').order_by(Case.created_at.desc()).limit(5).all()

    # الفواتير المعلقة
    pending_invoices_list = Invoice.query.filter_by(status='pending').order_by(Invoice.due_date.asc()).limit(5).all()

    return render_template_string('''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="utf-8">
    <title>التقارير والإحصائيات</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <nav class="navbar navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/">🏛️ المحامي فالح بن عقاب آل عيسى</a>
            <div>
                <a class="btn btn-outline-light btn-sm" href="/">الرئيسية</a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="card">
            <div class="card-header bg-info text-white">
                <h3>📊 التقارير والإحصائيات</h3>
            </div>
            <div class="card-body">
                <!-- الإحصائيات العامة -->
                <div class="row mb-4">
                    <div class="col-md-3">
                        <div class="card text-center border-primary">
                            <div class="card-body">
                                <h2 class="text-primary">{{ total_clients }}</h2>
                                <p>إجمالي العملاء</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card text-center border-success">
                            <div class="card-body">
                                <h2 class="text-success">{{ total_cases }}</h2>
                                <p>إجمالي القضايا</p>
                                <small>نشطة: {{ active_cases }} | مغلقة: {{ closed_cases }}</small>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card text-center border-warning">
                            <div class="card-body">
                                <h2 class="text-warning">{{ total_invoices }}</h2>
                                <p>إجمالي الفواتير</p>
                                <small>معلقة: {{ pending_invoices }} | مدفوعة: {{ paid_invoices }}</small>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card text-center border-danger">
                            <div class="card-body">
                                <h2 class="text-danger">{{ "{:,.0f}".format(total_revenue) }}</h2>
                                <p>إجمالي الإيرادات ({{ riyal_svg()|safe }})</p>
                                <small>هذا الشهر: {{ "{:,.0f}".format(monthly_revenue) }}</small>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- الإحصائيات المالية -->
                <div class="row mb-4">
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header bg-success text-white">
                                <h5>💰 الوضع المالي</h5>
                            </div>
                            <div class="card-body">
                                <div class="row">
                                    <div class="col-6">
                                        <h4 class="text-success">{{ "{:,.2f}".format(total_revenue) }} {{ riyal_svg()|safe }}</h4>
                                        <p>إجمالي الإيرادات المحصلة</p>
                                    </div>
                                    <div class="col-6">
                                        <h4 class="text-warning">{{ "{:,.2f}".format(pending_amount) }} {{ riyal_svg()|safe }}</h4>
                                        <p>المبالغ المعلقة</p>
                                    </div>
                                </div>
                                <div class="progress">
                                    <div class="progress-bar bg-success" style="width: {{ (total_revenue / (total_revenue + pending_amount) * 100) if (total_revenue + pending_amount) > 0 else 0 }}%"></div>
                                </div>
                                <small class="text-muted">نسبة التحصيل: {{ "{:.1f}".format((total_revenue / (total_revenue + pending_amount) * 100) if (total_revenue + pending_amount) > 0 else 0) }}%</small>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header bg-primary text-white">
                                <h5>📁 حالة القضايا</h5>
                            </div>
                            <div class="card-body">
                                <canvas id="casesChart" width="400" height="200"></canvas>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- القوائم -->
                <div class="row">
                    <div class="col-md-4">
                        <div class="card">
                            <div class="card-header">
                                <h6>👥 أحدث العملاء</h6>
                            </div>
                            <div class="card-body">
                                {% if recent_clients %}
                                    {% for client in recent_clients %}
                                    <div class="d-flex justify-content-between align-items-center mb-2">
                                        <span>{{ client.full_name }}</span>
                                        <small class="text-muted">{{ client.created_at.strftime('%m-%d') }}</small>
                                    </div>
                                    {% endfor %}
                                {% else %}
                                    <p class="text-muted">لا توجد عملاء</p>
                                {% endif %}
                                <a href="/clients" class="btn btn-sm btn-primary w-100 mt-2">عرض جميع العملاء</a>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card">
                            <div class="card-header">
                                <h6>📁 القضايا النشطة</h6>
                            </div>
                            <div class="card-body">
                                {% if active_cases_list %}
                                    {% for case in active_cases_list %}
                                    <div class="mb-2">
                                        <strong>{{ case.case_number }}</strong><br>
                                        <small>{{ case.title[:30] }}...</small><br>
                                        <small class="text-muted">{{ case.client.full_name }}</small>
                                    </div>
                                    <hr>
                                    {% endfor %}
                                {% else %}
                                    <p class="text-muted">لا توجد قضايا نشطة</p>
                                {% endif %}
                                <a href="/cases" class="btn btn-sm btn-success w-100 mt-2">عرض جميع القضايا</a>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card">
                            <div class="card-header">
                                <h6>💰 الفواتير المعلقة</h6>
                            </div>
                            <div class="card-body">
                                {% if pending_invoices_list %}
                                    {% for invoice in pending_invoices_list %}
                                    <div class="d-flex justify-content-between align-items-center mb-2">
                                        <div>
                                            <strong>{{ invoice.invoice_number }}</strong><br>
                                            <small>{{ invoice.client.full_name }}</small>
                                        </div>
                                        <div class="text-end">
                                            <strong>{{ "{:,.0f}".format(invoice.total_amount) }}</strong><br>
                                            <small class="text-muted">{{ invoice.due_date.strftime('%m-%d') if invoice.due_date else '-' }}</small>
                                        </div>
                                    </div>
                                    {% endfor %}
                                {% else %}
                                    <p class="text-muted">لا توجد فواتير معلقة</p>
                                {% endif %}
                                <a href="/invoices?filter=pending" class="btn btn-sm btn-warning w-100 mt-2">عرض جميع الفواتير المعلقة</a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // رسم بياني لحالة القضايا
        const ctx = document.getElementById('casesChart').getContext('2d');
        const casesChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['نشطة', 'مغلقة'],
                datasets: [{
                    data: [{{ active_cases }}, {{ closed_cases }}],
                    backgroundColor: ['#28a745', '#6c757d'],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    </script>
</body>
</html>
    ''', total_clients=total_clients, total_cases=total_cases, active_cases=active_cases,
         closed_cases=closed_cases, total_invoices=total_invoices, pending_invoices=pending_invoices,
         paid_invoices=paid_invoices, total_revenue=total_revenue, pending_amount=pending_amount,
         monthly_revenue=monthly_revenue, recent_clients=recent_clients,
         active_cases_list=active_cases_list, pending_invoices_list=pending_invoices_list)

@app.route('/database_status')
@login_required
@admin_required
def database_status():
    """صفحة حالة قاعدة البيانات"""
    db_status = get_database_status()

    return render_template_string('''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>حالة قاعدة البيانات - نظام إدارة المكتب</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .status-card {
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            border: none;
            margin-bottom: 20px;
        }
        .status-success { border-left: 5px solid #28a745; }
        .status-warning { border-left: 5px solid #ffc107; }
        .status-danger { border-left: 5px solid #dc3545; }
        .status-info { border-left: 5px solid #17a2b8; }

        .status-icon {
            font-size: 3rem;
            margin-bottom: 15px;
        }
        .success-icon { color: #28a745; }
        .warning-icon { color: #ffc107; }
        .danger-icon { color: #dc3545; }
        .info-icon { color: #17a2b8; }
    </style>
</head>
<body class="bg-light">
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            {{ get_navbar_brand_global()|safe }}
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/">الرئيسية</a>
                <a class="nav-link" href="/office_settings">الإعدادات</a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="row">
            <div class="col-12">
                <h1 class="mb-4">
                    <i class="fas fa-database me-2"></i>
                    حالة قاعدة البيانات
                </h1>
            </div>
        </div>

        <div class="row">
            <div class="col-md-6">
                <div class="card status-card {% if db_status.persistent %}status-success{% else %}status-warning{% endif %}">
                    <div class="card-body text-center">
                        <div class="status-icon {% if db_status.persistent %}success-icon{% else %}warning-icon{% endif %}">
                            {% if db_status.persistent %}
                                <i class="fas fa-shield-alt"></i>
                            {% else %}
                                <i class="fas fa-exclamation-triangle"></i>
                            {% endif %}
                        </div>
                        <h4>نوع قاعدة البيانات</h4>
                        <p class="lead">{{ db_status.type }}</p>
                        <p class="text-muted">{{ db_status.server }}</p>
                    </div>
                </div>
            </div>

            <div class="col-md-6">
                <div class="card status-card {% if 'متصل ✅' in db_status.status %}status-success{% else %}status-danger{% endif %}">
                    <div class="card-body text-center">
                        <div class="status-icon {% if 'متصل ✅' in db_status.status %}success-icon{% else %}danger-icon{% endif %}">
                            {% if 'متصل ✅' in db_status.status %}
                                <i class="fas fa-check-circle"></i>
                            {% else %}
                                <i class="fas fa-times-circle"></i>
                            {% endif %}
                        </div>
                        <h4>حالة الاتصال</h4>
                        <p class="lead">{{ db_status.status }}</p>
                        {% if db_status.connection_test %}
                            <small class="text-muted">اختبار الاتصال: {{ db_status.connection_test }}</small>
                        {% endif %}
                    </div>
                </div>
            </div>
        </div>

        {% if not db_status.persistent %}
        <div class="row mt-4">
            <div class="col-12">
                <div class="alert alert-warning" role="alert">
                    <h4 class="alert-heading">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        تحذير: البيانات غير محفوظة دائماً!
                    </h4>
                    <p>{{ db_status.warning }}</p>
                    <hr>
                    <h5>لحل هذه المشكلة:</h5>
                    <ol>
                        <li>أنشئ حساب مجاني على <a href="https://supabase.com" target="_blank">Supabase</a></li>
                        <li>أنشئ مشروع جديد وقاعدة بيانات</li>
                        <li>انسخ رابط قاعدة البيانات</li>
                        <li>أضف متغير <code>DATABASE_URL</code> في إعدادات الخادم</li>
                        <li>أعد تشغيل التطبيق</li>
                    </ol>
                    <a href="/migrate_data" class="btn btn-warning">
                        <i class="fas fa-database me-2"></i>
                        نقل البيانات إلى قاعدة خارجية
                    </a>
                </div>
            </div>
        </div>
        {% else %}
        <div class="row mt-4">
            <div class="col-12">
                <div class="alert alert-success" role="alert">
                    <h4 class="alert-heading">
                        <i class="fas fa-check-circle me-2"></i>
                        ممتاز! البيانات محفوظة بأمان
                    </h4>
                    <p>قاعدة البيانات الخارجية تعمل بشكل صحيح. البيانات محفوظة دائماً ولن تُحذف عند إعادة تشغيل الخادم.</p>
                </div>
            </div>
        </div>
        {% endif %}

        <div class="row mt-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-tools me-2"></i>أدوات قاعدة البيانات</h5>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-4">
                                <a href="/test_database" class="btn btn-info w-100 mb-2">
                                    <i class="fas fa-vial me-2"></i>
                                    اختبار الاتصال
                                </a>
                            </div>
                            <div class="col-md-4">
                                <a href="/backup_database" class="btn btn-secondary w-100 mb-2">
                                    <i class="fas fa-download me-2"></i>
                                    نسخة احتياطية
                                </a>
                            </div>
                            <div class="col-md-4">
                                <a href="/office_settings" class="btn btn-primary w-100 mb-2">
                                    <i class="fas fa-cog me-2"></i>
                                    إعدادات المكتب
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
    ''', db_status=db_status)

@app.route('/test_database')
@login_required
@admin_required
def test_database():
    """اختبار الاتصال بقاعدة البيانات"""
    try:
        # اختبار الاتصال
        with db.engine.connect() as conn:
            result = conn.execute(db.text("SELECT 1 as test"))
            test_value = result.fetchone()[0]

            if test_value == 1:
                flash('✅ نجح اختبار الاتصال بقاعدة البيانات!', 'success')
            else:
                flash('❌ فشل اختبار قاعدة البيانات', 'danger')

    except Exception as e:
        flash(f'❌ خطأ في الاتصال: {str(e)}', 'danger')

    return redirect(url_for('database_status'))

@app.route('/backup_database')
@login_required
@admin_required
def backup_database():
    """إنشاء نسخة احتياطية من قاعدة البيانات"""
    try:
        # استدعاء دالة النسخ الاحتياطي الموجودة
        auto_backup_database()
        flash('✅ تم إنشاء النسخة الاحتياطية بنجاح!', 'success')
    except Exception as e:
        flash(f'❌ خطأ في إنشاء النسخة الاحتياطية: {str(e)}', 'danger')

    return redirect(url_for('database_status'))

@app.route('/migrate_data')
@login_required
@admin_required
def migrate_data_page():
    """صفحة نقل البيانات"""
    return render_template_string('''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>نقل البيانات - نظام إدارة المكتب</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            {{ get_navbar_brand_global()|safe }}
        </div>
    </nav>

    <div class="container mt-4">
        <div class="row justify-content-center">
            <div class="col-md-8">
                <div class="card">
                    <div class="card-header bg-warning text-dark">
                        <h4><i class="fas fa-database me-2"></i>نقل البيانات إلى قاعدة بيانات خارجية</h4>
                    </div>
                    <div class="card-body">
                        <div class="alert alert-info">
                            <h5><i class="fas fa-info-circle me-2"></i>قبل البدء:</h5>
                            <ol>
                                <li>تأكد من إنشاء قاعدة بيانات خارجية (Supabase مثلاً)</li>
                                <li>أضف متغير <code>DATABASE_URL</code> في إعدادات الخادم</li>
                                <li>أعد تشغيل التطبيق</li>
                                <li>تأكد من ظهور "PostgreSQL (خارجي)" في حالة قاعدة البيانات</li>
                            </ol>
                        </div>

                        <div class="alert alert-warning">
                            <h5><i class="fas fa-exclamation-triangle me-2"></i>تحذير:</h5>
                            <p>هذه العملية ستنقل جميع البيانات من قاعدة البيانات المحلية إلى القاعدة الخارجية.</p>
                            <p>تأكد من إنشاء نسخة احتياطية أولاً!</p>
                        </div>

                        <div class="text-center">
                            <a href="/database_status" class="btn btn-secondary me-2">
                                <i class="fas fa-arrow-left me-2"></i>
                                العودة لحالة قاعدة البيانات
                            </a>
                            <button class="btn btn-warning" onclick="startMigration()">
                                <i class="fas fa-database me-2"></i>
                                بدء نقل البيانات
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
    function startMigration() {
        if (confirm('هل أنت متأكد من نقل البيانات؟ تأكد من إعداد قاعدة البيانات الخارجية أولاً.')) {
            alert('ميزة نقل البيانات ستكون متاحة قريباً. يرجى اتباع الدليل المرفق لإعداد قاعدة البيانات الخارجية يدوياً.');
        }
    }
    </script>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
    ''')

@app.route('/office_settings')
@login_required
@admin_required
def office_settings():
    """صفحة إعدادات المكتب"""
    # فحص صلاحية المدير
    if not current_user.is_admin():
        flash('هذه الصفحة مخصصة للمديرين فقط', 'danger')
        return redirect(url_for('index'))

    settings = OfficeSettings.get_settings()
    return render_template_string('''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>إعدادات المكتب - {{ settings.office_name }}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <link href="{{ url_for('static', filename='css/custom.css') }}" rel="stylesheet">
    <style>
        .settings-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        .form-section {
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        .section-title {
            color: #667eea;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        .form-control:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25);
        }
        .btn-save {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
            border-radius: 25px;
            padding: 12px 30px;
            color: white;
            font-weight: bold;
            transition: all 0.3s ease;
        }
        .btn-save:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
            color: white;
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark">
        <div class="container">
            {{ navbar_brand | safe }}
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/">
                    <i class="fas fa-tachometer-alt me-1"></i>لوحة التحكم
                </a>
                <a class="nav-link" href="/logout">
                    <i class="fas fa-sign-out-alt me-1"></i>تسجيل الخروج
                </a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <!-- Header Card -->
        <div class="card settings-card mb-4">
            <div class="card-body text-center">
                <i class="fas fa-cogs fa-3x mb-3"></i>
                <h2 class="card-title">⚙️ إعدادات المكتب</h2>
                <p class="card-text">إدارة وتحديث بيانات المكتب والمعلومات الأساسية</p>
            </div>
        </div>

        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ 'success' if category == 'success' else 'danger' }} alert-dismissible fade show">
                        {{ message }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        <!-- قسم حالة قاعدة البيانات -->
        <div class="form-section">
            <h4 class="section-title">
                <i class="fas fa-database me-2"></i>حالة قاعدة البيانات
            </h4>

            {% set db_status = get_db_status() %}
            <div class="row">
                <div class="col-md-8">
                    <div class="d-flex align-items-center">
                        <div class="me-3">
                            {% if db_status.persistent %}
                                <i class="fas fa-shield-alt text-success fa-2x"></i>
                            {% else %}
                                <i class="fas fa-exclamation-triangle text-warning fa-2x"></i>
                            {% endif %}
                        </div>
                        <div>
                            <h6 class="mb-1">{{ db_status.type }}</h6>
                            <p class="mb-1 text-muted">{{ db_status.status }}</p>
                            {% if not db_status.persistent %}
                                <small class="text-warning">
                                    <i class="fas fa-exclamation-triangle me-1"></i>
                                    البيانات ستُحذف عند إعادة التشغيل!
                                </small>
                            {% else %}
                                <small class="text-success">
                                    <i class="fas fa-check-circle me-1"></i>
                                    البيانات محفوظة دائماً
                                </small>
                            {% endif %}
                        </div>
                    </div>
                </div>
                <div class="col-md-4 text-end">
                    <a href="/database_status" class="btn btn-outline-primary">
                        <i class="fas fa-info-circle me-1"></i>
                        تفاصيل أكثر
                    </a>
                </div>
            </div>

            {% if not db_status.persistent %}
            <div class="alert alert-warning mt-3" role="alert">
                <strong>تحذير:</strong> لحل مشكلة فقدان البيانات، يرجى إعداد قاعدة بيانات خارجية.
                <a href="/database_status" class="alert-link">اضغط هنا للحصول على التعليمات</a>
            </div>
            {% endif %}
        </div>

        <form method="POST" enctype="multipart/form-data">
            <!-- معلومات المكتب الأساسية -->
            <div class="form-section">
                <h4 class="section-title">
                    <i class="fas fa-building me-2"></i>معلومات المكتب الأساسية
                </h4>

                <!-- شعار المكتب -->
                <div class="row mb-4">
                    <div class="col-12">
                        <label class="form-label">
                            <i class="fas fa-image me-1"></i>شعار المكتب
                        </label>

                        {% if settings.logo_path %}
                        <div class="current-logo mb-3">
                            <div class="card" style="max-width: 300px;">
                                <div class="card-body text-center">
                                    <img src="{{ url_for('simple_file', filename=settings.logo_path) }}"
                                         class="img-fluid" style="max-height: 150px;" alt="شعار المكتب الحالي">
                                    <div class="mt-2">
                                        <small class="text-muted">الشعار الحالي</small>
                                    </div>
                                </div>
                            </div>
                        </div>
                        {% endif %}

                        <div class="input-group">
                            <input type="file" class="form-control" name="logo" accept="image/*">
                            <label class="input-group-text" for="logo">
                                <i class="fas fa-upload"></i>
                            </label>
                        </div>
                        <small class="form-text text-muted">
                            <i class="fas fa-info-circle me-1"></i>
                            يُفضل استخدام صور بصيغة PNG أو JPG بحجم لا يزيد عن 2 ميجابايت
                        </small>

                        {% if settings.logo_path %}
                        <div class="mt-2">
                            <button type="submit" name="remove_logo" value="1" class="btn btn-outline-danger btn-sm"
                                    onclick="return confirm('هل تريد حذف الشعار الحالي؟')">
                                <i class="fas fa-trash me-1"></i>حذف الشعار
                            </button>
                        </div>
                        {% endif %}
                    </div>
                </div>

                <div class="row">
                    <div class="col-md-6">
                        <div class="mb-3">
                            <label class="form-label">
                                <i class="fas fa-signature me-1"></i>اسم المكتب (عربي) *
                            </label>
                            <input type="text" class="form-control" name="office_name"
                                   value="{{ settings.office_name }}" required>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="mb-3">
                            <label class="form-label">
                                <i class="fas fa-signature me-1"></i>اسم المكتب (إنجليزي)
                            </label>
                            <input type="text" class="form-control" name="office_name_en"
                                   value="{{ settings.office_name_en or '' }}">
                        </div>
                    </div>
                </div>
                <div class="row">
                    <div class="col-md-6">
                        <div class="mb-3">
                            <label class="form-label">
                                <i class="fas fa-calendar me-1"></i>سنة التأسيس
                            </label>
                            <input type="number" class="form-control" name="established_year"
                                   value="{{ settings.established_year or '' }}" min="1900" max="2030">
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="mb-3">
                            <label class="form-label">
                                <i class="fas fa-money-bill me-1"></i>العملة
                            </label>
                            <select class="form-control" name="currency">
                                <option value="ريال" {{ 'selected' if settings.currency == 'ريال' else '' }}>ريال سعودي</option>
                                <option value="درهم" {{ 'selected' if settings.currency == 'درهم' else '' }}>درهم إماراتي</option>
                                <option value="دينار" {{ 'selected' if settings.currency == 'دينار' else '' }}>دينار كويتي</option>
                                <option value="دولار" {{ 'selected' if settings.currency == 'دولار' else '' }}>دولار أمريكي</option>
                            </select>
                        </div>
                    </div>
                </div>
                <div class="mb-3">
                    <label class="form-label">
                        <i class="fas fa-info-circle me-1"></i>وصف المكتب
                    </label>
                    <textarea class="form-control" name="description" rows="3">{{ settings.description or '' }}</textarea>
                </div>
            </div>

            <!-- العنوان ومعلومات الموقع -->
            <div class="form-section">
                <h4 class="section-title">
                    <i class="fas fa-map-marker-alt me-2"></i>العنوان ومعلومات الموقع
                </h4>
                <div class="mb-3">
                    <label class="form-label">
                        <i class="fas fa-home me-1"></i>العنوان التفصيلي
                    </label>
                    <textarea class="form-control" name="address" rows="2">{{ settings.address or '' }}</textarea>
                </div>
                <div class="row">
                    <div class="col-md-4">
                        <div class="mb-3">
                            <label class="form-label">
                                <i class="fas fa-city me-1"></i>المدينة
                            </label>
                            <input type="text" class="form-control" name="city"
                                   value="{{ settings.city or '' }}">
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="mb-3">
                            <label class="form-label">
                                <i class="fas fa-mail-bulk me-1"></i>الرمز البريدي
                            </label>
                            <input type="text" class="form-control" name="postal_code"
                                   value="{{ settings.postal_code or '' }}">
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="mb-3">
                            <label class="form-label">
                                <i class="fas fa-flag me-1"></i>الدولة
                            </label>
                            <input type="text" class="form-control" name="country"
                                   value="{{ settings.country }}">
                        </div>
                    </div>
                </div>
            </div>

            <!-- معلومات التسجيل والترخيص -->
            <div class="form-section">
                <h4 class="section-title">
                    <i class="fas fa-certificate me-2"></i>معلومات التسجيل والترخيص
                </h4>
                <div class="row">
                    <div class="col-md-4">
                        <div class="mb-3">
                            <label class="form-label">
                                <i class="fas fa-file-contract me-1"></i>السجل التجاري
                            </label>
                            <input type="text" class="form-control" name="commercial_register"
                                   value="{{ settings.commercial_register or '' }}">
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="mb-3">
                            <label class="form-label">
                                <i class="fas fa-receipt me-1"></i>الرقم الضريبي
                            </label>
                            <input type="text" class="form-control" name="tax_number"
                                   value="{{ settings.tax_number or '' }}">
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="mb-3">
                            <label class="form-label">
                                <i class="fas fa-id-card me-1"></i>رقم الترخيص
                            </label>
                            <input type="text" class="form-control" name="license_number"
                                   value="{{ settings.license_number or '' }}">
                        </div>
                    </div>
                </div>
            </div>

            <!-- معلومات الاتصال -->
            <div class="form-section">
                <h4 class="section-title">
                    <i class="fas fa-phone me-2"></i>معلومات الاتصال
                </h4>
                <div class="row">
                    <div class="col-md-6">
                        <div class="mb-3">
                            <label class="form-label">
                                <i class="fas fa-phone me-1"></i>الهاتف الأساسي
                            </label>
                            <input type="tel" class="form-control" name="phone_1"
                                   value="{{ settings.phone_1 or '' }}">
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="mb-3">
                            <label class="form-label">
                                <i class="fas fa-phone-alt me-1"></i>هاتف إضافي
                            </label>
                            <input type="tel" class="form-control" name="phone_2"
                                   value="{{ settings.phone_2 or '' }}">
                        </div>
                    </div>
                </div>
                <div class="row">
                    <div class="col-md-4">
                        <div class="mb-3">
                            <label class="form-label">
                                <i class="fas fa-fax me-1"></i>الفاكس
                            </label>
                            <input type="tel" class="form-control" name="fax"
                                   value="{{ settings.fax or '' }}">
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="mb-3">
                            <label class="form-label">
                                <i class="fas fa-envelope me-1"></i>البريد الإلكتروني
                            </label>
                            <input type="email" class="form-control" name="email"
                                   value="{{ settings.email or '' }}">
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="mb-3">
                            <label class="form-label">
                                <i class="fas fa-globe me-1"></i>الموقع الإلكتروني
                            </label>
                            <input type="url" class="form-control" name="website"
                                   value="{{ settings.website or '' }}">
                        </div>
                    </div>
                </div>
            </div>

            <!-- أزرار الحفظ -->
            <div class="text-center mb-4">
                <button type="submit" class="btn btn-save btn-lg">
                    <i class="fas fa-save me-2"></i>حفظ الإعدادات
                </button>
                <a href="/" class="btn btn-secondary btn-lg ms-3">
                    <i class="fas fa-times me-2"></i>إلغاء
                </a>
            </div>
        </form>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
    ''', settings=settings, navbar_brand=get_navbar_brand())

@app.route('/office_settings', methods=['POST'])
@login_required
@admin_required
def update_office_settings():
    """تحديث إعدادات المكتب"""
    try:
        settings = OfficeSettings.get_settings()

        # التحقق من طلب حذف الشعار
        if request.form.get('remove_logo'):
            if settings.logo_path:
                # حذف الملف من النظام
                old_logo_path = os.path.join(app.config['UPLOAD_FOLDER'], settings.logo_path)
                if os.path.exists(old_logo_path):
                    os.remove(old_logo_path)
                settings.logo_path = None
                db.session.commit()
                flash('تم حذف الشعار بنجاح', 'success')
            return redirect(url_for('office_settings'))

        # معالجة رفع الشعار الجديد
        if 'logo' in request.files:
            logo_file = request.files['logo']
            if logo_file and logo_file.filename and allowed_file(logo_file.filename):
                # حذف الشعار القديم إذا كان موجوداً
                if settings.logo_path:
                    old_logo_path = os.path.join(app.config['UPLOAD_FOLDER'], settings.logo_path)
                    if os.path.exists(old_logo_path):
                        os.remove(old_logo_path)

                # حفظ الشعار الجديد
                filename = safe_filename_with_timestamp(logo_file.filename)
                filename = f"logo_{filename}"  # إضافة بادئة logo

                # إنشاء مجلد logos إذا لم يكن موجوداً
                logos_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'logos')
                if not os.path.exists(logos_folder):
                    os.makedirs(logos_folder)

                logo_path = os.path.join(logos_folder, filename)
                logo_file.save(logo_path)

                # حفظ المسار النسبي في قاعدة البيانات
                settings.logo_path = f"logos/{filename}"
                flash('تم رفع الشعار بنجاح', 'success')

        # تحديث البيانات
        settings.office_name = request.form.get('office_name', '').strip()
        settings.office_name_en = request.form.get('office_name_en', '').strip()
        settings.address = request.form.get('address', '').strip()
        settings.city = request.form.get('city', '').strip()
        settings.postal_code = request.form.get('postal_code', '').strip()
        settings.country = request.form.get('country', '').strip()

        # معلومات التسجيل
        settings.commercial_register = request.form.get('commercial_register', '').strip()
        settings.tax_number = request.form.get('tax_number', '').strip()
        settings.license_number = request.form.get('license_number', '').strip()

        # معلومات الاتصال
        settings.phone_1 = request.form.get('phone_1', '').strip()
        settings.phone_2 = request.form.get('phone_2', '').strip()
        settings.fax = request.form.get('fax', '').strip()
        settings.email = request.form.get('email', '').strip()
        settings.website = request.form.get('website', '').strip()

        # معلومات إضافية
        established_year = request.form.get('established_year', '').strip()
        if established_year:
            settings.established_year = int(established_year)
        settings.description = request.form.get('description', '').strip()
        settings.currency = request.form.get('currency', 'ريال')

        # تحديث وقت التعديل
        settings.updated_at = datetime.utcnow()

        db.session.commit()
        flash('تم حفظ إعدادات المكتب بنجاح', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء حفظ الإعدادات: {str(e)}', 'error')

    return redirect(url_for('office_settings'))

# إنشاء الجداول تلقائياً عند بدء التطبيق
def init_database():
    """إنشاء الجداول إذا لم تكن موجودة"""
    try:
        with app.app_context():
            db.create_all()
            print("✅ تم إنشاء/تحديث جداول قاعدة البيانات")

            # إنشاء المستخدم المدير الافتراضي
            if User.query.count() == 0:
                admin = User(
                    username='admin',
                    first_name='المدير',
                    last_name='العام',
                    role='admin'
                )
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
                print("✅ تم إنشاء المستخدم المدير الافتراضي")

            # إنشاء إعدادات المكتب الافتراضية
            if OfficeSettings.query.count() == 0:
                default_settings = OfficeSettings(
                    office_name='مكتب فالح آل عيسى للمحاماة',
                    office_name_en='Faleh Al Issa Law Office',
                    address='الرياض، المملكة العربية السعودية',
                    city='الرياض',
                    country='المملكة العربية السعودية',
                    phone_1='+966501234567',
                    email='info@falehlaw.com',
                    currency='ريال سعودي',
                    language='ar'
                )
                db.session.add(default_settings)
                db.session.commit()
                print("✅ تم إنشاء إعدادات المكتب الافتراضية")

    except Exception as e:
        print(f"⚠️ خطأ في إنشاء الجداول: {e}")

# تنفيذ إنشاء الجداول
init_database()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        # التحقق من وجود عمود case_id في جدول client_document وإضافته إذا لم يكن موجوداً
        try:
            # محاولة تشغيل استعلام يستخدم case_id للتحقق من وجود العمود
            db.session.execute(db.text("SELECT case_id FROM client_document LIMIT 1"))
        except Exception as e:
            if "no such column: client_document.case_id" in str(e):
                print("إضافة عمود case_id إلى جدول client_document...")
                try:
                    db.session.execute(db.text("ALTER TABLE client_document ADD COLUMN case_id INTEGER"))
                    db.session.commit()
                    print("تم إضافة عمود case_id بنجاح")
                except Exception as alter_error:
                    print(f"خطأ في إضافة العمود: {alter_error}")
                    db.session.rollback()

        # التحقق من وجود عمود role في جدول user وإضافته إذا لم يكن موجوداً
        try:
            db.session.execute(db.text("SELECT role FROM user LIMIT 1"))
        except Exception as e:
            if "no such column: user.role" in str(e):
                print("إضافة عمود role إلى جدول user...")
                try:
                    db.session.execute(db.text("ALTER TABLE user ADD COLUMN role TEXT DEFAULT 'lawyer'"))
                    db.session.execute(db.text("ALTER TABLE user ADD COLUMN created_at DATETIME"))
                    db.session.commit()
                    print("تم إضافة أعمدة الأدوار بنجاح")
                    # سجل الأداء بعد إضافة أعمدة الأدوار
                    import logging
                    import time
                    logging.basicConfig(filename='performance.log', level=logging.INFO, format='%(asctime)s %(message)s', encoding='utf-8')
                    logging.info("تم إضافة أعمدة الأدوار إلى جدول المستخدمين (user)")
                    logging.info(f"⏱️ زمن إضافة أعمدة الأدوار: {time.strftime('%H:%M:%S')}")
                    print(f"⏱️ زمن إضافة أعمدة الأدوار: {time.strftime('%H:%M:%S')}")
                except Exception as alter_error:
                    print(f"خطأ في إضافة أعمدة الأدوار: {alter_error}")
                    db.session.rollback()

        if User.query.count() == 0:
            admin = User(username='admin', first_name='فالح', last_name='آل عيسى', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("✅ تم إنشاء المستخدم المدير")
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
                ),
                Expense(
                    title='صيانة الطابعة',
                    description='إصلاح وصيانة طابعة المكتب',
                    amount=150.00,
                    category='صيانة',
                    expense_date=datetime.now(),
                    vendor='مركز الصيانة',
                    payment_method='نقدي',
                    created_by=1
                )
            ]

            for expense in sample_expenses:
                db.session.add(expense)
            db.session.commit()
            print("✅ تم إنشاء مصروفات تجريبية")

    print("\n" + "="*50)
    print("🚀 النظام النهائي متاح على:")
    print("   - محلياً: http://127.0.0.1:8080")
    print("   - من الشبكة: http://[عنوان_IP_جهازك]:8080")
    print("👤 بيانات الدخول: admin / admin123")
    print("⚠️  تأكد من فتح البورت 3080 في جدار الحماية")
    print("="*50 + "\n")

    try:
        print("🔄 بدء تشغيل الخادم...")

        # تفعيل النسخ الاحتياطي التلقائي (مع معالجة الأخطاء)
        try:
            start_backup_scheduler()
        except Exception as backup_error:
            print(f"⚠️ تحذير: لم يتم تفعيل النسخ الاحتياطي: {backup_error}")

        # إعدادات للاستضافة الخارجية
        port = int(os.environ.get('PORT', 10000))  # Render يستخدم PORT
        host = os.environ.get('HOST', '0.0.0.0')   # للإنتاج على Render
        debug_mode = os.environ.get('DEBUG', 'False').lower() == 'true'

        print(f"🚀 تشغيل الخادم على {host}:{port}")
        app.run(debug=debug_mode, host=host, port=port, threaded=True)
    except Exception as e:
        print(f"❌ خطأ في تشغيل الخادم: {e}")
        print("💡 تأكد من أن البورت غير مستخدم من برنامج آخر")
