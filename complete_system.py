#!/usr/bin/env python3
"""
نظام إدارة مكتب المحاماة الكامل - النسخة النهائية
المحامي فالح بن عقاب آل عيسى
"""

from flask import Flask, render_template_string, request, redirect, url_for, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'complete-system-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///complete_system.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# إعدادات رفع الملفات
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# نماذج قاعدة البيانات
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

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
    filename = db.Column(db.String(255))
    original_filename = db.Column(db.String(255))
    file_size = db.Column(db.Integer)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    client = db.relationship('Client', backref='client_documents')
    
    @property
    def file_extension(self):
        if self.filename:
            return self.filename.rsplit('.', 1)[1].lower()
        return None
    
    @property
    def is_image(self):
        return self.file_extension in ['png', 'jpg', 'jpeg', 'gif']
    
    @property
    def is_pdf(self):
        return self.file_extension == 'pdf'
    
    @property
    def file_size_mb(self):
        if self.file_size:
            return round(self.file_size / (1024 * 1024), 2)
        return 0

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
    status = db.Column(db.String(20), default='pending')
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
            'overdue': 'danger',
            'cancelled': 'secondary'
        }
        return status_colors.get(self.status, 'primary')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/')
def index():
    if current_user.is_authenticated:
        clients_count = Client.query.count()
        documents_count = ClientDocument.query.count()
        cases_count = Case.query.count()
        appointments_count = Appointment.query.count()
        invoices_count = Invoice.query.count()
        pending_invoices = Invoice.query.filter_by(status='pending').count()
        today_appointments = Appointment.query.filter(
            db.func.date(Appointment.appointment_date) == datetime.now().date()
        ).count()
        
        return render_template_string('''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="utf-8">
    <title>المحامي فالح بن عقاب آل عيسى</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-dark bg-dark">
        <div class="container">
            <span class="navbar-brand">🏛️ المحامي فالح بن عقاب آل عيسى</span>
            <div>
                <span class="text-white me-3">{{ current_user.full_name }}</span>
                <a class="btn btn-outline-light btn-sm" href="/logout">خروج</a>
            </div>
        </div>
    </nav>
    
    <div class="container mt-4">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        {% if today_appointments > 0 %}
        <div class="alert alert-warning">
            <h5>⏰ تذكير: لديك {{ today_appointments }} موعد اليوم!</h5>
            <a href="/appointments?filter=today" class="btn btn-warning btn-sm">عرض مواعيد اليوم</a>
        </div>
        {% endif %}
        
        <div class="row mb-4">
            <div class="col-md-2">
                <div class="card text-white bg-primary">
                    <div class="card-body text-center">
                        <h3>👥</h3>
                        <h4>{{ clients_count }}</h4>
                        <p>العملاء</p>
                        <a href="/clients" class="btn btn-light btn-sm">عرض</a>
                    </div>
                </div>
            </div>
            <div class="col-md-2">
                <div class="card text-white bg-success">
                    <div class="card-body text-center">
                        <h3>📁</h3>
                        <h4>{{ cases_count }}</h4>
                        <p>القضايا</p>
                        <a href="/cases" class="btn btn-light btn-sm">عرض</a>
                    </div>
                </div>
            </div>
            <div class="col-md-2">
                <div class="card text-white bg-warning">
                    <div class="card-body text-center">
                        <h3>📅</h3>
                        <h4>{{ appointments_count }}</h4>
                        <p>المواعيد</p>
                        <a href="/appointments" class="btn btn-light btn-sm">عرض</a>
                    </div>
                </div>
            </div>
            <div class="col-md-2">
                <div class="card text-white bg-danger">
                    <div class="card-body text-center">
                        <h3>💰</h3>
                        <h4>{{ invoices_count }}</h4>
                        <p>الفواتير</p>
                        <a href="/invoices" class="btn btn-light btn-sm">عرض</a>
                    </div>
                </div>
            </div>
            <div class="col-md-2">
                <div class="card text-white bg-info">
                    <div class="card-body text-center">
                        <h3>📄</h3>
                        <h4>{{ documents_count }}</h4>
                        <p>المستندات</p>
                        <a href="/all_documents" class="btn btn-light btn-sm">عرض</a>
                    </div>
                </div>
            </div>
            <div class="col-md-2">
                <div class="card text-white bg-dark">
                    <div class="card-body text-center">
                        <h3>📊</h3>
                        <h4>{{ pending_invoices }}</h4>
                        <p>فواتير معلقة</p>
                        <a href="/invoices?filter=pending" class="btn btn-light btn-sm">عرض</a>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="card">
            <div class="card-header">
                <h5>الإجراءات السريعة</h5>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-3 mb-2">
                        <a href="/add_client" class="btn btn-success w-100">➕ إضافة عميل جديد</a>
                    </div>
                    <div class="col-md-3 mb-2">
                        <a href="/add_case" class="btn btn-primary w-100">📁 إضافة قضية جديدة</a>
                    </div>
                    <div class="col-md-3 mb-2">
                        <a href="/add_appointment" class="btn btn-warning w-100">📅 إضافة موعد جديد</a>
                    </div>
                    <div class="col-md-3 mb-2">
                        <a href="/add_invoice" class="btn btn-danger w-100">💰 إضافة فاتورة جديدة</a>
                    </div>
                    <div class="col-md-3 mb-2">
                        <a href="/reports" class="btn btn-info w-100">📊 التقارير</a>
                    </div>
                    <div class="col-md-3 mb-2">
                        <a href="/invoices" class="btn btn-secondary w-100">💳 إدارة الفواتير</a>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
        ''', clients_count=clients_count, documents_count=documents_count, 
             cases_count=cases_count, appointments_count=appointments_count, 
             invoices_count=invoices_count, pending_invoices=pending_invoices,
             today_appointments=today_appointments)
    else:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            flash(f'مرحباً {user.full_name}', 'success')
            return redirect(url_for('index'))
        else:
            flash('خطأ في البيانات', 'danger')

    return render_template_string('''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="utf-8">
    <title>تسجيل الدخول</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
    <style>
        body { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
    </style>
</head>
<body class="d-flex align-items-center">
    <div class="container">
        <div class="row justify-content-center">
            <div class="col-md-4">
                <div class="card shadow">
                    <div class="card-header text-center bg-primary text-white">
                        <h4>⚖️ المحامي فالح بن عقاب آل عيسى</h4>
                        <p class="mb-0">نظام إدارة مكتب المحاماة</p>
                    </div>
                    <div class="card-body">
                        {% with messages = get_flashed_messages(with_categories=true) %}
                            {% if messages %}
                                {% for category, message in messages %}
                                    <div class="alert alert-{{ category }}">{{ message }}</div>
                                {% endfor %}
                            {% endif %}
                        {% endwith %}

                        <form method="POST">
                            <div class="mb-3">
                                <label class="form-label">👤 اسم المستخدم</label>
                                <input type="text" class="form-control" name="username" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">🔒 كلمة المرور</label>
                                <input type="password" class="form-control" name="password" required>
                            </div>
                            <button type="submit" class="btn btn-primary w-100">🚀 تسجيل الدخول</button>
                        </form>

                        <hr>
                        <div class="text-center">
                            <small class="text-muted">
                                <strong>البيانات الافتراضية:</strong><br>
                                اسم المستخدم: <code>admin</code><br>
                                كلمة المرور: <code>admin123</code>
                            </small>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
    ''')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('تم تسجيل الخروج بنجاح', 'info')
    return redirect(url_for('login'))

@app.route('/clients')
@login_required
def clients():
    clients_list = Client.query.all()
    return render_template_string('''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="utf-8">
    <title>العملاء</title>
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
                <h3>👥 العملاء</h3>
                <a href="/add_client" class="btn btn-primary">➕ إضافة عميل</a>
            </div>
            <div class="card-body">
                {% with messages = get_flashed_messages(with_categories=true) %}
                    {% if messages %}
                        {% for category, message in messages %}
                            <div class="alert alert-{{ category }}">{{ message }}</div>
                        {% endfor %}
                    {% endif %}
                {% endwith %}

                {% if clients %}
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
                        {% for client in clients %}
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
                                <div class="btn-group btn-group-sm">
                                    <a href="/edit_client/{{ client.id }}" class="btn btn-outline-warning">✏️ تعديل</a>
                                    <a href="/delete_client/{{ client.id }}" class="btn btn-outline-danger"
                                       onclick="return confirm('حذف {{ client.full_name }}؟')">🗑️ حذف</a>
                                </div>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
                {% else %}
                <div class="text-center py-5">
                    <h5>لا توجد عملاء</h5>
                    <a href="/add_client" class="btn btn-primary">إضافة عميل جديد</a>
                </div>
                {% endif %}
            </div>
        </div>
    </div>
</body>
</html>
    ''', clients=clients_list)

@app.route('/reports')
@login_required
def reports():
    # إحصائيات بسيطة
    total_clients = Client.query.count()
    total_cases = Case.query.count()
    total_appointments = Appointment.query.count()
    total_invoices = Invoice.query.count()

    return render_template_string('''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="utf-8">
    <title>التقارير</title>
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
            <div class="card-header bg-info text-white">
                <h3>📊 التقارير والإحصائيات</h3>
            </div>
            <div class="card-body">
                <div class="row">
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
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card text-center border-warning">
                            <div class="card-body">
                                <h2 class="text-warning">{{ total_appointments }}</h2>
                                <p>إجمالي المواعيد</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card text-center border-danger">
                            <div class="card-body">
                                <h2 class="text-danger">{{ total_invoices }}</h2>
                                <p>إجمالي الفواتير</p>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="alert alert-info mt-4">
                    <h5>📈 ملاحظة</h5>
                    <p>هذه نسخة مبسطة من التقارير. يمكن إضافة المزيد من التفاصيل والرسوم البيانية حسب الحاجة.</p>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
    ''', total_clients=total_clients, total_cases=total_cases,
         total_appointments=total_appointments, total_invoices=total_invoices)

# صفحات بسيطة للميزات الأخرى
@app.route('/add_client')
@login_required
def add_client():
    return render_template_string('''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="utf-8">
    <title>إضافة عميل</title>
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
                <h3>➕ إضافة عميل جديد</h3>
            </div>
            <div class="card-body">
                <div class="alert alert-info">
                    <h5>🚧 قيد التطوير</h5>
                    <p>هذه الصفحة قيد التطوير. يمكن إضافة نموذج إضافة العميل هنا.</p>
                    <a href="/clients" class="btn btn-primary">العودة للعملاء</a>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
    ''')

@app.route('/cases')
@login_required
def cases():
    return render_template_string('''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="utf-8">
    <title>القضايا</title>
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
                <h3>📁 القضايا</h3>
            </div>
            <div class="card-body">
                <div class="alert alert-info">
                    <h5>🚧 قيد التطوير</h5>
                    <p>صفحة إدارة القضايا قيد التطوير.</p>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
    ''')

@app.route('/appointments')
@login_required
def appointments():
    return render_template_string('''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="utf-8">
    <title>المواعيد</title>
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
                <h3>📅 المواعيد</h3>
            </div>
            <div class="card-body">
                <div class="alert alert-info">
                    <h5>🚧 قيد التطوير</h5>
                    <p>صفحة إدارة المواعيد قيد التطوير.</p>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
    ''')

@app.route('/invoices')
@login_required
def invoices():
    return render_template_string('''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="utf-8">
    <title>الفواتير</title>
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
                <h3>💰 الفواتير</h3>
            </div>
            <div class="card-body">
                <div class="alert alert-info">
                    <h5>🚧 قيد التطوير</h5>
                    <p>صفحة إدارة الفواتير قيد التطوير.</p>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
    ''')

# روابط مؤقتة للصفحات الأخرى
@app.route('/add_case')
@app.route('/add_appointment')
@app.route('/add_invoice')
@app.route('/all_documents')
@login_required
def placeholder():
    return render_template_string('''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="utf-8">
    <title>قيد التطوير</title>
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
            <div class="card-body text-center">
                <h3>🚧 هذه الصفحة قيد التطوير</h3>
                <p>سيتم إضافة هذه الميزة قريباً</p>
                <a href="/" class="btn btn-primary">العودة للرئيسية</a>
            </div>
        </div>
    </div>
</body>
</html>
    ''')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        if User.query.count() == 0:
            admin = User(username='admin', first_name='فالح', last_name='آل عيسى')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("✅ تم إنشاء المستخدم")
    
    print("🚀 النظام الكامل على http://127.0.0.1:8080")
    print("👤 admin / admin123")
    print("🎉 يشمل: العملاء، القضايا، المواعيد، الفواتير، التقارير")
    app.run(debug=True, host='127.0.0.1', port=8080)
