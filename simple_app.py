#!/usr/bin/env python3
"""
تطبيق مبسط جداً لنظام إدارة مكتب المحاماة
"""

import os
from flask import Flask, render_template_string, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# إنشاء التطبيق
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key-for-testing'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///simple_law_office.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# إعداد قاعدة البيانات
db = SQLAlchemy(app)

# إعداد نظام تسجيل الدخول
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'يرجى تسجيل الدخول للوصول إلى هذه الصفحة.'
login_manager.login_message_category = 'info'

# نموذج المستخدم
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    role = db.Column(db.String(20), default='lawyer')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

# نموذج العميل
class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    mobile = db.Column(db.String(20))
    address = db.Column(db.Text)
    national_id = db.Column(db.String(20))
    company = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

# نموذج القضية
class Case(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    case_number = db.Column(db.String(50), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    case_type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='active')
    priority = db.Column(db.String(20), default='medium')
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    lawyer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    court_name = db.Column(db.String(200))
    judge_name = db.Column(db.String(100))
    opposing_party = db.Column(db.String(200))
    start_date = db.Column(db.Date, default=datetime.utcnow)
    end_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    client = db.relationship('Client', backref='cases')
    lawyer = db.relationship('User', backref='cases')

# نموذج الموعد
class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    appointment_type = db.Column(db.String(50), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(200))
    status = db.Column(db.String(20), default='scheduled')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'))
    case_id = db.Column(db.Integer, db.ForeignKey('case.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='appointments')
    client = db.relationship('Client', backref='appointments')
    case = db.relationship('Case', backref='appointments')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# الصفحة الرئيسية
@app.route('/')
def index():
    if current_user.is_authenticated:
        return render_template_string('''
        <!DOCTYPE html>
        <html lang="ar" dir="rtl">
        <head>
            <meta charset="utf-8">
            <title>المحامي فالح بن عقاب آل عيسى</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
            <style>
                .navbar-brand { font-weight: bold; }
                .card { box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
            </style>
        </head>
        <body>
            <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
                <div class="container">
                    <a class="navbar-brand" href="/">🏛️ المحامي فالح بن عقاب آل عيسى</a>
                    <div class="navbar-nav ms-auto">
                        <span class="navbar-text me-3">مرحباً {{ current_user.full_name }}</span>
                        <a class="nav-link" href="/logout">تسجيل الخروج</a>
                    </div>
                </div>
            </nav>
            <div class="container mt-4">
                <div class="row">
                    <div class="col-md-3">
                        <div class="card">
                            <div class="card-header bg-primary text-white">
                                <h5>📋 القائمة الرئيسية</h5>
                            </div>
                            <div class="list-group list-group-flush">
                                <a href="/" class="list-group-item list-group-item-action active">
                                    🏠 الرئيسية
                                </a>
                                <a href="/clients" class="list-group-item list-group-item-action">
                                    👥 العملاء
                                </a>
                                <a href="/cases" class="list-group-item list-group-item-action">
                                    📁 القضايا
                                </a>
                                <a href="/appointments" class="list-group-item list-group-item-action">
                                    📅 المواعيد
                                </a>
                                <a href="/invoices" class="list-group-item list-group-item-action">
                                    💰 الفواتير
                                </a>
                                <a href="/documents" class="list-group-item list-group-item-action">
                                    📄 المستندات
                                </a>
                                {% if current_user.role == 'admin' %}
                                <a href="/users" class="list-group-item list-group-item-action">
                                    ⚙️ إدارة المستخدمين
                                </a>
                                <a href="/reports" class="list-group-item list-group-item-action">
                                    📊 التقارير
                                </a>
                                {% endif %}
                            </div>
                        </div>

                        <div class="card mt-3">
                            <div class="card-header bg-info text-white">
                                <h6>👤 معلومات المستخدم</h6>
                            </div>
                            <div class="card-body">
                                <p><strong>الاسم:</strong> {{ current_user.full_name }}</p>
                                <p><strong>الدور:</strong>
                                    {% if current_user.role == 'admin' %}
                                        <span class="badge bg-danger">👑 مدير</span>
                                    {% elif current_user.role == 'lawyer' %}
                                        <span class="badge bg-primary">⚖️ محامي</span>
                                    {% else %}
                                        <span class="badge bg-secondary">📝 سكرتير</span>
                                    {% endif %}
                                </p>
                                <p><strong>البريد:</strong> {{ current_user.email }}</p>
                            </div>
                        </div>
                    </div>

                    <div class="col-md-9">
                        <div class="alert alert-success">
                            <h4>✅ مرحباً بك {{ current_user.full_name }}</h4>
                            <p>تم تسجيل دخولك بنجاح في نظام إدارة مكتب المحاماة</p>
                        </div>

                        <!-- إحصائيات سريعة -->
                        <div class="row mb-4">
                            <div class="col-md-3">
                                <div class="card text-white bg-primary">
                                    <div class="card-body text-center">
                                        <h2>👥</h2>
                                        <h4>15</h4>
                                        <p>العملاء</p>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="card text-white bg-success">
                                    <div class="card-body text-center">
                                        <h2>📁</h2>
                                        <h4>8</h4>
                                        <p>القضايا النشطة</p>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="card text-white bg-warning">
                                    <div class="card-body text-center">
                                        <h2>📅</h2>
                                        <h4>3</h4>
                                        <p>مواعيد اليوم</p>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="card text-white bg-info">
                                    <div class="card-body text-center">
                                        <h2>💰</h2>
                                        <h4>12</h4>
                                        <p>فواتير معلقة</p>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- الأنشطة الحديثة -->
                        <div class="card">
                            <div class="card-header">
                                <h5>📈 الأنشطة الحديثة</h5>
                            </div>
                            <div class="card-body">
                                <div class="list-group">
                                    <div class="list-group-item">
                                        <div class="d-flex w-100 justify-content-between">
                                            <h6 class="mb-1">📁 قضية جديدة: نزاع تجاري</h6>
                                            <small>منذ ساعتين</small>
                                        </div>
                                        <p class="mb-1">تم إضافة قضية جديدة للعميل أحمد محمد</p>
                                    </div>
                                    <div class="list-group-item">
                                        <div class="d-flex w-100 justify-content-between">
                                            <h6 class="mb-1">📅 موعد جلسة محكمة</h6>
                                            <small>منذ 3 ساعات</small>
                                        </div>
                                        <p class="mb-1">جلسة محكمة غداً الساعة 10:00 صباحاً</p>
                                    </div>
                                    <div class="list-group-item">
                                        <div class="d-flex w-100 justify-content-between">
                                            <h6 class="mb-1">💰 فاتورة مدفوعة</h6>
                                            <small>منذ 5 ساعات</small>
                                        </div>
                                        <p class="mb-1">تم دفع فاتورة بقيمة 15,000 ريال</p>
                                    </div>
                                    <div class="list-group-item">
                                        <div class="d-flex w-100 justify-content-between">
                                            <h6 class="mb-1">👤 عميل جديد</h6>
                                            <small>أمس</small>
                                        </div>
                                        <p class="mb-1">تم تسجيل عميل جديد: سارة أحمد</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        </body>
        </html>
        ''')
    else:
        return redirect(url_for('login'))

# تسجيل الدخول
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password) and user.is_active:
            login_user(user)
            flash(f'مرحباً {user.full_name}', 'success')
            return redirect(url_for('index'))
        else:
            flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'danger')
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="utf-8">
        <title>تسجيل الدخول - المحامي فالح بن عقاب آل عيسى</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            body { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
            .login-card { box-shadow: 0 10px 30px rgba(0,0,0,0.3); border-radius: 15px; }
        </style>
    </head>
    <body class="d-flex align-items-center">
        <div class="container">
            <div class="row justify-content-center">
                <div class="col-md-6">
                    <div class="card login-card">
                        <div class="card-header text-center bg-primary text-white">
                            <h3>⚖️ المحامي فالح بن عقاب آل عيسى</h3>
                            <p class="mb-0">محاماة واستشارات قانونية</p>
                        </div>
                        <div class="card-body p-4">
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
                                    <label for="username" class="form-label">👤 اسم المستخدم</label>
                                    <input type="text" class="form-control" id="username" name="username" required>
                                </div>
                                <div class="mb-3">
                                    <label for="password" class="form-label">🔒 كلمة المرور</label>
                                    <input type="password" class="form-control" id="password" name="password" required>
                                </div>
                                <button type="submit" class="btn btn-primary w-100">
                                    🚀 تسجيل الدخول
                                </button>
                            </form>
                            <hr>
                            <div class="text-center">
                                <small class="text-muted">
                                    <strong>بيانات تجريبية:</strong><br>
                                    <span class="badge bg-danger">👑 مدير:</span> admin / admin123<br>
                                    <span class="badge bg-primary">⚖️ محامي:</span> lawyer1 / lawyer123<br>
                                    <span class="badge bg-secondary">📝 سكرتير:</span> secretary1 / secretary123
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
    ''')

# تسجيل الخروج
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('تم تسجيل الخروج بنجاح', 'info')
    return redirect(url_for('login'))

# صفحة العملاء
@app.route('/clients')
@login_required
def clients():
    clients_list = Client.query.all()
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="utf-8">
        <title>العملاء - المحامي فالح بن عقاب آل عيسى</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
    </head>
    <body>
        <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
            <div class="container">
                <a class="navbar-brand" href="/">🏛️ المحامي فالح بن عقاب آل عيسى</a>
                <div class="navbar-nav ms-auto">
                    <a class="nav-link" href="/">الرئيسية</a>
                    <a class="nav-link" href="/logout">تسجيل الخروج</a>
                </div>
            </div>
        </nav>
        <div class="container mt-4">
            <div class="card">
                <div class="card-header">
                    <h3>👥 إدارة العملاء</h3>
                </div>
                <div class="card-body">
                    <a href="/add_client" class="btn btn-primary mb-3">➕ إضافة عميل جديد</a>
                    <div class="table-responsive">
                        <table class="table table-hover">
                            <thead>
                                <tr>
                                    <th>الاسم</th>
                                    <th>الهاتف</th>
                                    <th>البريد الإلكتروني</th>
                                    <th>عدد القضايا</th>
                                    <th>الإجراءات</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for client in clients %}
                                <tr>
                                    <td>{{ client.full_name }}</td>
                                    <td>{{ client.phone or client.mobile or '-' }}</td>
                                    <td>{{ client.email or '-' }}</td>
                                    <td><span class="badge bg-primary">{{ client.cases|length }}</span></td>
                                    <td>
                                        <button class="btn btn-sm btn-outline-primary">👁️ عرض</button>
                                        <button class="btn btn-sm btn-outline-warning">✏️ تعديل</button>
                                    </td>
                                </tr>
                                {% else %}
                                <tr>
                                    <td colspan="5" class="text-center">لا توجد عملاء مسجلين</td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    ''', clients=clients_list)

# إضافة عميل جديد
@app.route('/add_client', methods=['GET', 'POST'])
@login_required
def add_client():
    if request.method == 'POST':
        client = Client(
            first_name=request.form['first_name'],
            last_name=request.form['last_name'],
            email=request.form['email'],
            phone=request.form['phone'],
            mobile=request.form['mobile'],
            address=request.form['address'],
            national_id=request.form['national_id'],
            company=request.form['company']
        )
        db.session.add(client)
        db.session.commit()
        flash(f'تم إضافة العميل {client.full_name} بنجاح', 'success')
        return redirect(url_for('clients'))

    return render_template_string('''
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="utf-8">
        <title>إضافة عميل جديد - المحامي فالح بن عقاب آل عيسى</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
    </head>
    <body>
        <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
            <div class="container">
                <a class="navbar-brand" href="/">🏛️ المحامي فالح بن عقاب آل عيسى</a>
                <div class="navbar-nav ms-auto">
                    <a class="nav-link" href="/">الرئيسية</a>
                    <a class="nav-link" href="/clients">العملاء</a>
                    <a class="nav-link" href="/logout">تسجيل الخروج</a>
                </div>
            </div>
        </nav>
        <div class="container mt-4">
            <div class="card">
                <div class="card-header">
                    <h3>➕ إضافة عميل جديد</h3>
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
                                    <label for="first_name" class="form-label">الاسم الأول *</label>
                                    <input type="text" class="form-control" id="first_name" name="first_name" required>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label for="last_name" class="form-label">اسم العائلة *</label>
                                    <input type="text" class="form-control" id="last_name" name="last_name" required>
                                </div>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label for="email" class="form-label">البريد الإلكتروني</label>
                                    <input type="email" class="form-control" id="email" name="email">
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label for="phone" class="form-label">الهاتف</label>
                                    <input type="text" class="form-control" id="phone" name="phone">
                                </div>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label for="mobile" class="form-label">الجوال</label>
                                    <input type="text" class="form-control" id="mobile" name="mobile">
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label for="national_id" class="form-label">رقم الهوية</label>
                                    <input type="text" class="form-control" id="national_id" name="national_id">
                                </div>
                            </div>
                        </div>
                        <div class="mb-3">
                            <label for="company" class="form-label">الشركة</label>
                            <input type="text" class="form-control" id="company" name="company">
                        </div>
                        <div class="mb-3">
                            <label for="address" class="form-label">العنوان</label>
                            <textarea class="form-control" id="address" name="address" rows="3"></textarea>
                        </div>
                        <div class="d-flex gap-2">
                            <button type="submit" class="btn btn-success">💾 حفظ العميل</button>
                            <a href="/clients" class="btn btn-secondary">❌ إلغاء</a>
                        </div>
                    </form>
                </div>
            </div>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    ''')

# صفحة القضايا
@app.route('/cases')
@login_required
def cases():
    cases_list = Case.query.all()
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="utf-8">
        <title>القضايا - المحامي فالح بن عقاب آل عيسى</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
    </head>
    <body>
        <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
            <div class="container">
                <a class="navbar-brand" href="/">🏛️ المحامي فالح بن عقاب آل عيسى</a>
                <div class="navbar-nav ms-auto">
                    <a class="nav-link" href="/">الرئيسية</a>
                    <a class="nav-link" href="/logout">تسجيل الخروج</a>
                </div>
            </div>
        </nav>
        <div class="container mt-4">
            <div class="card">
                <div class="card-header">
                    <h3>📁 إدارة القضايا</h3>
                </div>
                <div class="card-body">
                    <a href="/add_case" class="btn btn-success mb-3">➕ إضافة قضية جديدة</a>
                    <div class="table-responsive">
                        <table class="table table-hover">
                            <thead>
                                <tr>
                                    <th>رقم القضية</th>
                                    <th>العنوان</th>
                                    <th>العميل</th>
                                    <th>النوع</th>
                                    <th>الحالة</th>
                                    <th>الأولوية</th>
                                    <th>الإجراءات</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for case in cases %}
                                <tr>
                                    <td>{{ case.case_number }}</td>
                                    <td>{{ case.title }}</td>
                                    <td>{{ case.client.full_name if case.client else '-' }}</td>
                                    <td>
                                        {% if case.case_type == 'commercial' %}
                                            <span class="badge bg-info">تجاري</span>
                                        {% elif case.case_type == 'labor' %}
                                            <span class="badge bg-warning">عمالي</span>
                                        {% elif case.case_type == 'civil' %}
                                            <span class="badge bg-primary">مدني</span>
                                        {% elif case.case_type == 'criminal' %}
                                            <span class="badge bg-danger">جنائي</span>
                                        {% else %}
                                            <span class="badge bg-secondary">{{ case.case_type }}</span>
                                        {% endif %}
                                    </td>
                                    <td>
                                        {% if case.status == 'active' %}
                                            <span class="badge bg-success">نشط</span>
                                        {% elif case.status == 'closed' %}
                                            <span class="badge bg-secondary">مغلق</span>
                                        {% elif case.status == 'pending' %}
                                            <span class="badge bg-warning">معلق</span>
                                        {% else %}
                                            <span class="badge bg-info">{{ case.status }}</span>
                                        {% endif %}
                                    </td>
                                    <td>
                                        {% if case.priority == 'high' %}
                                            <span class="badge bg-danger">عالية</span>
                                        {% elif case.priority == 'medium' %}
                                            <span class="badge bg-warning">متوسطة</span>
                                        {% elif case.priority == 'low' %}
                                            <span class="badge bg-success">منخفضة</span>
                                        {% endif %}
                                    </td>
                                    <td>
                                        <button class="btn btn-sm btn-outline-primary">👁️ عرض</button>
                                        <button class="btn btn-sm btn-outline-warning">✏️ تعديل</button>
                                    </td>
                                </tr>
                                {% else %}
                                <tr>
                                    <td colspan="7" class="text-center">لا توجد قضايا مسجلة</td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    ''', cases=cases_list)

# إضافة قضية جديدة
@app.route('/add_case', methods=['GET', 'POST'])
@login_required
def add_case():
    if request.method == 'POST':
        # إنشاء رقم قضية تلقائي
        import random
        case_number = f"C2025-{random.randint(1000, 9999)}"

        case = Case(
            case_number=case_number,
            title=request.form['title'],
            description=request.form['description'],
            case_type=request.form['case_type'],
            status=request.form['status'],
            priority=request.form['priority'],
            client_id=request.form['client_id'],
            lawyer_id=current_user.id,
            court_name=request.form['court_name'],
            judge_name=request.form['judge_name'],
            opposing_party=request.form['opposing_party']
        )
        db.session.add(case)
        db.session.commit()
        flash(f'تم إضافة القضية {case.case_number} بنجاح', 'success')
        return redirect(url_for('cases'))

    clients_list = Client.query.all()
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="utf-8">
        <title>إضافة قضية جديدة - المحامي فالح بن عقاب آل عيسى</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
    </head>
    <body>
        <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
            <div class="container">
                <a class="navbar-brand" href="/">🏛️ المحامي فالح بن عقاب آل عيسى</a>
                <div class="navbar-nav ms-auto">
                    <a class="nav-link" href="/">الرئيسية</a>
                    <a class="nav-link" href="/cases">القضايا</a>
                    <a class="nav-link" href="/logout">تسجيل الخروج</a>
                </div>
            </div>
        </nav>
        <div class="container mt-4">
            <div class="card">
                <div class="card-header">
                    <h3>➕ إضافة قضية جديدة</h3>
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
                                    <label for="title" class="form-label">عنوان القضية *</label>
                                    <input type="text" class="form-control" id="title" name="title" required>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label for="client_id" class="form-label">العميل *</label>
                                    <select class="form-control" id="client_id" name="client_id" required>
                                        <option value="">اختر العميل</option>
                                        {% for client in clients %}
                                        <option value="{{ client.id }}">{{ client.full_name }}</option>
                                        {% endfor %}
                                    </select>
                                </div>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <label for="case_type" class="form-label">نوع القضية *</label>
                                    <select class="form-control" id="case_type" name="case_type" required>
                                        <option value="">اختر النوع</option>
                                        <option value="commercial">تجاري</option>
                                        <option value="labor">عمالي</option>
                                        <option value="civil">مدني</option>
                                        <option value="criminal">جنائي</option>
                                        <option value="family">أحوال شخصية</option>
                                    </select>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <label for="status" class="form-label">الحالة *</label>
                                    <select class="form-control" id="status" name="status" required>
                                        <option value="active">نشط</option>
                                        <option value="pending">معلق</option>
                                        <option value="closed">مغلق</option>
                                    </select>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <label for="priority" class="form-label">الأولوية *</label>
                                    <select class="form-control" id="priority" name="priority" required>
                                        <option value="medium">متوسطة</option>
                                        <option value="high">عالية</option>
                                        <option value="low">منخفضة</option>
                                    </select>
                                </div>
                            </div>
                        </div>
                        <div class="mb-3">
                            <label for="description" class="form-label">وصف القضية</label>
                            <textarea class="form-control" id="description" name="description" rows="3"></textarea>
                        </div>
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label for="court_name" class="form-label">اسم المحكمة</label>
                                    <input type="text" class="form-control" id="court_name" name="court_name">
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label for="judge_name" class="form-label">اسم القاضي</label>
                                    <input type="text" class="form-control" id="judge_name" name="judge_name">
                                </div>
                            </div>
                        </div>
                        <div class="mb-3">
                            <label for="opposing_party" class="form-label">الطرف المقابل</label>
                            <input type="text" class="form-control" id="opposing_party" name="opposing_party">
                        </div>
                        <div class="d-flex gap-2">
                            <button type="submit" class="btn btn-success">💾 حفظ القضية</button>
                            <a href="/cases" class="btn btn-secondary">❌ إلغاء</a>
                        </div>
                    </form>
                </div>
            </div>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    ''', clients=clients_list)

# صفحة المواعيد
@app.route('/appointments')
@login_required
def appointments():
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="utf-8">
        <title>المواعيد - المحامي فالح بن عقاب آل عيسى</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
    </head>
    <body>
        <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
            <div class="container">
                <a class="navbar-brand" href="/">🏛️ المحامي فالح بن عقاب آل عيسى</a>
                <div class="navbar-nav ms-auto">
                    <a class="nav-link" href="/">الرئيسية</a>
                    <a class="nav-link" href="/logout">تسجيل الخروج</a>
                </div>
            </div>
        </nav>
        <div class="container mt-4">
            <div class="card">
                <div class="card-header">
                    <h3>📅 إدارة المواعيد</h3>
                </div>
                <div class="card-body">
                    <button class="btn btn-warning mb-3">➕ إضافة موعد جديد</button>
                    <div class="row">
                        <div class="col-md-4">
                            <div class="card border-primary">
                                <div class="card-header bg-primary text-white">
                                    <h6>📅 اليوم - 13 يوليو 2025</h6>
                                </div>
                                <div class="card-body">
                                    <div class="mb-2">
                                        <strong>10:00 ص</strong> - جلسة محكمة<br>
                                        <small class="text-muted">قضية: نزاع تجاري</small>
                                    </div>
                                    <div class="mb-2">
                                        <strong>2:00 م</strong> - اجتماع عميل<br>
                                        <small class="text-muted">العميل: أحمد محمد</small>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="card border-warning">
                                <div class="card-header bg-warning text-dark">
                                    <h6>📅 غداً - 14 يوليو 2025</h6>
                                </div>
                                <div class="card-body">
                                    <div class="mb-2">
                                        <strong>9:00 ص</strong> - استشارة قانونية<br>
                                        <small class="text-muted">العميل: سارة أحمد</small>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="card border-info">
                                <div class="card-header bg-info text-white">
                                    <h6>📅 الأسبوع القادم</h6>
                                </div>
                                <div class="card-body">
                                    <div class="mb-2">
                                        <strong>الاثنين</strong> - جلسة محكمة<br>
                                        <small class="text-muted">قضية: قضية عمالية</small>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    ''')

# صفحة الفواتير
@app.route('/invoices')
@login_required
def invoices():
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="utf-8">
        <title>الفواتير - المحامي فالح بن عقاب آل عيسى</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
    </head>
    <body>
        <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
            <div class="container">
                <a class="navbar-brand" href="/">🏛️ المحامي فالح بن عقاب آل عيسى</a>
                <div class="navbar-nav ms-auto">
                    <a class="nav-link" href="/">الرئيسية</a>
                    <a class="nav-link" href="/logout">تسجيل الخروج</a>
                </div>
            </div>
        </nav>
        <div class="container mt-4">
            <div class="card">
                <div class="card-header">
                    <h3>💰 إدارة الفواتير</h3>
                </div>
                <div class="card-body">
                    <button class="btn btn-info mb-3">➕ إنشاء فاتورة جديدة</button>
                    <div class="table-responsive">
                        <table class="table table-hover">
                            <thead>
                                <tr>
                                    <th>رقم الفاتورة</th>
                                    <th>العميل</th>
                                    <th>المبلغ</th>
                                    <th>تاريخ الإصدار</th>
                                    <th>تاريخ الاستحقاق</th>
                                    <th>الحالة</th>
                                    <th>الإجراءات</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td>INV-2024-001</td>
                                    <td>أحمد محمد</td>
                                    <td>15,000 ريال</td>
                                    <td>2025-07-01</td>
                                    <td>2025-07-15</td>
                                    <td><span class="badge bg-success">مدفوعة</span></td>
                                    <td>
                                        <button class="btn btn-sm btn-outline-primary">👁️ عرض</button>
                                        <button class="btn btn-sm btn-outline-secondary">🖨️ طباعة</button>
                                    </td>
                                </tr>
                                <tr>
                                    <td>INV-2024-002</td>
                                    <td>سارة أحمد</td>
                                    <td>8,000 ريال</td>
                                    <td>2025-07-05</td>
                                    <td>2025-07-20</td>
                                    <td><span class="badge bg-warning">معلقة</span></td>
                                    <td>
                                        <button class="btn btn-sm btn-outline-primary">👁️ عرض</button>
                                        <button class="btn btn-sm btn-outline-secondary">🖨️ طباعة</button>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    ''')

# صفحة المستندات
@app.route('/documents')
@login_required
def documents():
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="utf-8">
        <title>المستندات - المحامي فالح بن عقاب آل عيسى</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
    </head>
    <body>
        <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
            <div class="container">
                <a class="navbar-brand" href="/">🏛️ المحامي فالح بن عقاب آل عيسى</a>
                <div class="navbar-nav ms-auto">
                    <a class="nav-link" href="/">الرئيسية</a>
                    <a class="nav-link" href="/logout">تسجيل الخروج</a>
                </div>
            </div>
        </nav>
        <div class="container mt-4">
            <div class="card">
                <div class="card-header">
                    <h3>📄 إدارة المستندات</h3>
                </div>
                <div class="card-body">
                    <button class="btn btn-secondary mb-3">📤 رفع مستند جديد</button>
                    <div class="row">
                        <div class="col-md-3">
                            <div class="card">
                                <div class="card-body text-center">
                                    <h2>📄</h2>
                                    <h6>عقد توكيل</h6>
                                    <small class="text-muted">أحمد محمد</small><br>
                                    <button class="btn btn-sm btn-outline-primary mt-2">تحميل</button>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="card">
                                <div class="card-body text-center">
                                    <h2>📋</h2>
                                    <h6>مذكرة دفاع</h6>
                                    <small class="text-muted">قضية تجارية</small><br>
                                    <button class="btn btn-sm btn-outline-primary mt-2">تحميل</button>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="card">
                                <div class="card-body text-center">
                                    <h2>📊</h2>
                                    <h6>تقرير خبير</h6>
                                    <small class="text-muted">قضية عمالية</small><br>
                                    <button class="btn btn-sm btn-outline-primary mt-2">تحميل</button>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="card">
                                <div class="card-body text-center">
                                    <h2>🏛️</h2>
                                    <h6>حكم محكمة</h6>
                                    <small class="text-muted">قضية مدنية</small><br>
                                    <button class="btn btn-sm btn-outline-primary mt-2">تحميل</button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    ''')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # إنشاء المستخدمين الافتراضيين إذا لم يكونوا موجودين
        if User.query.count() == 0:
            print("إنشاء المستخدمين الافتراضيين...")
            
            admin = User(username='admin', email='admin@example.com', 
                        first_name='مدير', last_name='النظام', role='admin')
            admin.set_password('admin123')
            
            lawyer = User(username='lawyer1', email='lawyer1@example.com',
                         first_name='محامي', last_name='أول', role='lawyer')
            lawyer.set_password('lawyer123')
            
            secretary = User(username='secretary1', email='secretary1@example.com',
                           first_name='سكرتير', last_name='أول', role='secretary')
            secretary.set_password('secretary123')
            
            db.session.add_all([admin, lawyer, secretary])
            db.session.commit()
            print("✅ تم إنشاء المستخدمين الافتراضيين")
    
    print("=" * 60)
    print("🏛️ المحامي فالح بن عقاب آل عيسى")
    print("=" * 60)
    print("🚀 تشغيل التطبيق...")
    print("🌐 الرابط: http://127.0.0.1:5000")
    print("👤 مدير: admin / admin123")
    print("👤 محامي: lawyer1 / lawyer123")
    print("👤 سكرتير: secretary1 / secretary123")
    print("=" * 60)
    print("اضغط Ctrl+C لإيقاف التطبيق")
    print("=" * 60)
    
    app.run(debug=True, host='127.0.0.1', port=5000, use_reloader=False)
