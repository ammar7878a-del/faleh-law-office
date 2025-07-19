#!/usr/bin/env python3
"""
نظام إدارة مكتب المحاماة - النسخة النهائية الكاملة
المحامي فالح بن عقاب آل عيسى
"""

from flask import Flask, render_template_string, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import random

# إنشاء التطبيق
app = Flask(__name__)
app.config['SECRET_KEY'] = 'law-office-final-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///law_office_complete.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# إعداد قاعدة البيانات
db = SQLAlchemy(app)

# إعداد نظام تسجيل الدخول
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
    role = db.Column(db.String(20), default='lawyer')
    
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
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    client = db.relationship('Client', backref='client_documents')

class Case(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    case_number = db.Column(db.String(50), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    case_type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='active')
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    client = db.relationship('Client', backref='cases')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# الصفحة الرئيسية
@app.route('/')
def index():
    if current_user.is_authenticated:
        clients_count = Client.query.count()
        cases_count = Case.query.count()
        documents_count = ClientDocument.query.count()
        
        current_date = datetime.now().strftime('%Y-%m-%d')

        return render_template_string('''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="utf-8">
    <title>المحامي فالح بن عقاب آل عيسى</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
    <style>
        .stats-card { transition: transform 0.2s; }
        .stats-card:hover { transform: translateY(-5px); }
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
        
        <!-- الإحصائيات -->
        <div class="row mb-4">
            <div class="col-md-4">
                <div class="card text-white bg-primary stats-card">
                    <div class="card-body text-center">
                        <h2>👥</h2>
                        <h4>{{ clients_count }}</h4>
                        <p>العملاء المسجلين</p>
                        <a href="/clients" class="btn btn-light btn-sm">عرض العملاء</a>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card text-white bg-success stats-card">
                    <div class="card-body text-center">
                        <h2>📁</h2>
                        <h4>{{ cases_count }}</h4>
                        <p>القضايا المسجلة</p>
                        <a href="/cases" class="btn btn-light btn-sm">عرض القضايا</a>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card text-white bg-info stats-card">
                    <div class="card-body text-center">
                        <h2>📄</h2>
                        <h4>{{ documents_count }}</h4>
                        <p>المستندات المحفوظة</p>
                        <a href="/all_documents" class="btn btn-light btn-sm">عرض المستندات</a>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- الإجراءات السريعة -->
        <div class="row">
            <div class="col-md-8">
                <div class="card">
                    <div class="card-header bg-primary text-white">
                        <h5>🚀 الإجراءات السريعة</h5>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <a href="/add_client" class="btn btn-success btn-lg w-100">
                                    ➕ إضافة عميل جديد مع المستندات
                                </a>
                            </div>
                            <div class="col-md-6 mb-3">
                                <a href="/add_case" class="btn btn-primary btn-lg w-100">
                                    📁 إضافة قضية جديدة
                                </a>
                            </div>
                            <div class="col-md-6 mb-3">
                                <a href="/clients" class="btn btn-info btn-lg w-100">
                                    👥 إدارة العملاء
                                </a>
                            </div>
                            <div class="col-md-6 mb-3">
                                <a href="/cases" class="btn btn-warning btn-lg w-100">
                                    📋 إدارة القضايا
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card">
                    <div class="card-header bg-secondary text-white">
                        <h5>📊 معلومات النظام</h5>
                    </div>
                    <div class="card-body">
                        <ul class="list-unstyled">
                            <li><strong>المستخدم:</strong> {{ current_user.full_name }}</li>
                            <li><strong>الدور:</strong> {{ current_user.role }}</li>
                            <li><strong>التاريخ:</strong> {{ current_date }}</li>
                            <li><strong>الإصدار:</strong> 1.0</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
        ''', clients_count=clients_count, cases_count=cases_count, documents_count=documents_count, current_date=current_date)
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
            flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'danger')
    
    return render_template_string('''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="utf-8">
    <title>تسجيل الدخول</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
    <style>
        body { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            min-height: 100vh; 
        }
        .login-card { 
            box-shadow: 0 10px 30px rgba(0,0,0,0.3); 
            border-radius: 15px;
        }
    </style>
</head>
<body class="d-flex align-items-center">
    <div class="container">
        <div class="row justify-content-center">
            <div class="col-md-5">
                <div class="card login-card">
                    <div class="card-header text-center bg-primary text-white">
                        <h3>⚖️ المحامي فالح بن عقاب آل عيسى</h3>
                        <p class="mb-0">نظام إدارة مكتب المحاماة</p>
                    </div>
                    <div class="card-body p-4">
                        {% with messages = get_flashed_messages(with_categories=true) %}
                            {% if messages %}
                                {% for category, message in messages %}
                                    <div class="alert alert-{{ 'danger' if category == 'error' else category }}">{{ message }}</div>
                                {% endfor %}
                            {% endif %}
                        {% endwith %}
                        
                        <form method="POST">
                            <div class="mb-3">
                                <label for="username" class="form-label">👤 اسم المستخدم</label>
                                <input type="text" class="form-control form-control-lg" id="username" name="username" required>
                            </div>
                            <div class="mb-3">
                                <label for="password" class="form-label">🔒 كلمة المرور</label>
                                <input type="password" class="form-control form-control-lg" id="password" name="password" required>
                            </div>
                            <button type="submit" class="btn btn-primary btn-lg w-100">🚀 تسجيل الدخول</button>
                        </form>
                        
                        <hr>
                        <div class="text-center">
                            <small class="text-muted">
                                <strong>المستخدم الافتراضي:</strong><br>
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
    <title>إدارة العملاء</title>
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
            <div class="card-header d-flex justify-content-between align-items-center">
                <h3>👥 إدارة العملاء</h3>
                <a href="/add_client" class="btn btn-primary">➕ إضافة عميل جديد</a>
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

                {% if clients %}
                <div class="table-responsive">
                    <table class="table table-striped table-hover">
                        <thead class="table-dark">
                            <tr>
                                <th>الاسم الكامل</th>
                                <th>رقم الهوية</th>
                                <th>الهاتف</th>
                                <th>البريد الإلكتروني</th>
                                <th>القضايا</th>
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
                                    <span class="badge bg-primary">{{ client.cases|length }}</span>
                                    {% if client.cases|length > 0 %}
                                        <a href="/client_cases/{{ client.id }}" class="btn btn-sm btn-outline-primary ms-1">📁 عرض</a>
                                    {% endif %}
                                </td>
                                <td>
                                    <span class="badge bg-info">{{ client.client_documents|length }}</span>
                                    <a href="/client_documents/{{ client.id }}" class="btn btn-sm btn-outline-info ms-1">📄 عرض</a>
                                </td>
                                <td>
                                    <div class="btn-group" role="group">
                                        <a href="/edit_client/{{ client.id }}" class="btn btn-sm btn-warning">✏️ تعديل</a>
                                        <a href="/delete_client/{{ client.id }}" class="btn btn-sm btn-danger"
                                           onclick="return confirm('هل أنت متأكد من حذف العميل {{ client.full_name }}؟')">🗑️ حذف</a>
                                    </div>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                {% else %}
                <div class="text-center py-5">
                    <h4>📋 لا توجد عملاء مسجلين</h4>
                    <p class="text-muted">ابدأ بإضافة عميل جديد لبناء قاعدة بيانات العملاء</p>
                    <a href="/add_client" class="btn btn-primary btn-lg">➕ إضافة عميل جديد</a>
                </div>
                {% endif %}
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
    ''', clients=clients_list)

@app.route('/add_client', methods=['GET', 'POST'])
@login_required
def add_client():
    if request.method == 'POST':
        # إنشاء العميل
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

        # إضافة المستندات
        documents_added = 0
        document_types = [
            ('identity', 'الهوية الشخصية'),
            ('power_of_attorney', 'الوكالة'),
            ('contract', 'العقد'),
            ('other', 'مستندات أخرى')
        ]

        for doc_type, doc_name in document_types:
            desc_field = f'{doc_type}_desc'
            if desc_field in request.form and request.form[desc_field].strip():
                doc = ClientDocument(
                    document_type=doc_type,
                    description=request.form[desc_field],
                    client_id=client.id
                )
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
    <style>
        .form-section { margin-bottom: 30px; }
        .section-header {
            background: linear-gradient(45deg, #007bff, #0056b3);
            color: white;
            padding: 15px;
            border-radius: 10px 10px 0 0;
            margin-bottom: 0;
        }
        .required { color: red; font-weight: bold; }
        .form-control:focus { border-color: #007bff; box-shadow: 0 0 0 0.2rem rgba(0,123,255,.25); }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/">🏛️ المحامي فالح بن عقاب آل عيسى</a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/clients">العملاء</a>
                <a class="nav-link" href="/">الرئيسية</a>
                <a class="nav-link" href="/logout">تسجيل الخروج</a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="card shadow-lg">
            <div class="section-header">
                <h3 class="mb-0">➕ إضافة عميل جديد مع المستندات</h3>
                <small>املأ البيانات المطلوبة لإضافة عميل جديد إلى النظام</small>
            </div>
            <div class="card-body p-4">
                <form method="POST">
                    <!-- البيانات الأساسية -->
                    <div class="form-section">
                        <div class="card border-primary">
                            <div class="card-header bg-primary text-white">
                                <h5 class="mb-0">👤 البيانات الأساسية للعميل</h5>
                            </div>
                            <div class="card-body">
                                <div class="row">
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label class="form-label">الاسم الأول <span class="required">*</span></label>
                                            <input type="text" class="form-control form-control-lg" name="first_name" required
                                                   placeholder="أدخل الاسم الأول">
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label class="form-label">اسم العائلة <span class="required">*</span></label>
                                            <input type="text" class="form-control form-control-lg" name="last_name" required
                                                   placeholder="أدخل اسم العائلة">
                                        </div>
                                    </div>
                                </div>

                                <div class="row">
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label class="form-label">🆔 رقم الهوية الوطنية</label>
                                            <input type="text" class="form-control form-control-lg" name="national_id"
                                                   placeholder="مثال: 1234567890">
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label class="form-label">📱 رقم الهاتف</label>
                                            <input type="text" class="form-control form-control-lg" name="phone"
                                                   placeholder="مثال: 0501234567">
                                        </div>
                                    </div>
                                </div>

                                <div class="row">
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label class="form-label">📧 البريد الإلكتروني</label>
                                            <input type="email" class="form-control form-control-lg" name="email"
                                                   placeholder="مثال: client@email.com">
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label class="form-label">🏠 العنوان</label>
                                            <input type="text" class="form-control form-control-lg" name="address"
                                                   placeholder="العنوان الكامل">
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- المستندات -->
                    <div class="form-section">
                        <div class="card border-success">
                            <div class="card-header bg-success text-white">
                                <h5 class="mb-0">📄 المستندات والوثائق (اختياري)</h5>
                            </div>
                            <div class="card-body">
                                <div class="alert alert-info">
                                    <i class="fas fa-info-circle"></i>
                                    <strong>💡 ملاحظة:</strong> يمكنك إضافة وصف للمستندات هنا. سيتم إنشاء سجلات للمستندات ويمكن إدارتها لاحقاً من صفحة العميل.
                                </div>

                                <div class="row">
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label class="form-label">🆔 الهوية الشخصية</label>
                                            <input type="text" class="form-control form-control-lg" name="identity_desc"
                                                   placeholder="مثال: هوية وطنية رقم 1234567890">
                                            <small class="text-muted">وصف مستند الهوية الشخصية</small>
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label class="form-label">📋 الوكالة</label>
                                            <input type="text" class="form-control form-control-lg" name="power_of_attorney_desc"
                                                   placeholder="مثال: وكالة عامة مؤرخة 2025/01/15">
                                            <small class="text-muted">وصف مستند الوكالة</small>
                                        </div>
                                    </div>
                                </div>

                                <div class="row">
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label class="form-label">📄 العقد</label>
                                            <input type="text" class="form-control form-control-lg" name="contract_desc"
                                                   placeholder="مثال: عقد استشارة قانونية">
                                            <small class="text-muted">وصف العقد أو الاتفاقية</small>
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label class="form-label">📎 مستندات أخرى</label>
                                            <input type="text" class="form-control form-control-lg" name="other_desc"
                                                   placeholder="مثال: شهادات، تقارير، مراسلات">
                                            <small class="text-muted">أي مستندات إضافية</small>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- أزرار الحفظ -->
                    <div class="text-center">
                        <button type="submit" class="btn btn-success btn-lg me-3">
                            <i class="fas fa-save"></i> 💾 حفظ العميل والمستندات
                        </button>
                        <a href="/clients" class="btn btn-secondary btn-lg">
                            <i class="fas fa-times"></i> ❌ إلغاء
                        </a>
                    </div>
                </form>
            </div>
        </div>

        <!-- معلومات إضافية -->
        <div class="card mt-4">
            <div class="card-body">
                <h6><strong>📋 ملخص الحقول المتوفرة:</strong></h6>
                <div class="row">
                    <div class="col-md-6">
                        <h6 class="text-primary">البيانات الأساسية:</h6>
                        <ul class="list-unstyled">
                            <li>✅ الاسم الأول (مطلوب)</li>
                            <li>✅ اسم العائلة (مطلوب)</li>
                            <li>✅ رقم الهوية الوطنية</li>
                            <li>✅ رقم الهاتف</li>
                            <li>✅ البريد الإلكتروني</li>
                            <li>✅ العنوان</li>
                        </ul>
                    </div>
                    <div class="col-md-6">
                        <h6 class="text-success">المستندات:</h6>
                        <ul class="list-unstyled">
                            <li>✅ وصف الهوية الشخصية</li>
                            <li>✅ وصف الوكالة</li>
                            <li>✅ وصف العقد</li>
                            <li>✅ وصف المستندات الأخرى</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
    ''')

@app.route('/client_documents/<int:client_id>')
@login_required
def client_documents(client_id):
    client = Client.query.get_or_404(client_id)
    documents = ClientDocument.query.filter_by(client_id=client_id).all()

    return render_template_string('''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="utf-8">
    <title>مستندات العميل</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/">🏛️ المحامي فالح بن عقاب آل عيسى</a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/clients">العملاء</a>
                <a class="nav-link" href="/">الرئيسية</a>
                <a class="nav-link" href="/logout">تسجيل الخروج</a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="card">
            <div class="card-header d-flex justify-content-between align-items-center">
                <h3>📄 مستندات العميل: {{ client.full_name }}</h3>
                <a href="/add_client_document/{{ client.id }}" class="btn btn-primary">➕ إضافة مستند جديد</a>
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

                {% if documents %}
                <div class="row">
                    {% for doc in documents %}
                    <div class="col-md-6 mb-3">
                        <div class="card border-primary h-100">
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
                                <p class="card-text">{{ doc.description or 'لا يوجد وصف' }}</p>
                                <small class="text-muted">تاريخ الإضافة: {{ doc.created_at.strftime('%Y-%m-%d %H:%M') }}</small>
                                <div class="mt-2">
                                    <a href="/edit_client_document/{{ doc.id }}" class="btn btn-sm btn-outline-warning">✏️ تعديل</a>
                                    <a href="/delete_client_document/{{ doc.id }}" class="btn btn-sm btn-outline-danger"
                                       onclick="return confirm('هل أنت متأكد من حذف هذا المستند؟')">🗑️ حذف</a>
                                </div>
                            </div>
                        </div>
                    </div>
                    {% endfor %}
                </div>
                {% else %}
                <div class="text-center py-5">
                    <h5>📄 لا توجد مستندات لهذا العميل</h5>
                    <p class="text-muted">يمكنك إضافة مستندات جديدة مثل الهوية، الوكالة، العقود، وغيرها</p>
                    <a href="/add_client_document/{{ client.id }}" class="btn btn-primary btn-lg">➕ إضافة مستند جديد</a>
                </div>
                {% endif %}

                <div class="mt-4">
                    <a href="/clients" class="btn btn-secondary">← العودة للعملاء</a>
                    <a href="/edit_client/{{ client.id }}" class="btn btn-warning">✏️ تعديل بيانات العميل</a>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
    ''', client=client, documents=documents)

@app.route('/add_client_document/<int:client_id>', methods=['GET', 'POST'])
@login_required
def add_client_document(client_id):
    client = Client.query.get_or_404(client_id)

    if request.method == 'POST':
        doc = ClientDocument(
            document_type=request.form['document_type'],
            description=request.form.get('description'),
            client_id=client_id
        )
        db.session.add(doc)
        db.session.commit()
        flash('تم إضافة المستند بنجاح', 'success')
        return redirect(url_for('client_documents', client_id=client_id))

    return render_template_string('''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="utf-8">
    <title>إضافة مستند</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/">🏛️ المحامي فالح بن عقاب آل عيسى</a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/clients">العملاء</a>
                <a class="nav-link" href="/">الرئيسية</a>
                <a class="nav-link" href="/logout">تسجيل الخروج</a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="card">
            <div class="card-header">
                <h3>➕ إضافة مستند للعميل: {{ client.full_name }}</h3>
            </div>
            <div class="card-body">
                <form method="POST">
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
                    <div class="d-flex gap-2">
                        <button type="submit" class="btn btn-success">💾 حفظ المستند</button>
                        <a href="/client_documents/{{ client.id }}" class="btn btn-secondary">❌ إلغاء</a>
                    </div>
                </form>
            </div>
        </div>
    </div>
</body>
</html>
    ''', client=client)

@app.route('/delete_client_document/<int:doc_id>')
@login_required
def delete_client_document(doc_id):
    doc = ClientDocument.query.get_or_404(doc_id)
    client_id = doc.client_id
    db.session.delete(doc)
    db.session.commit()
    flash('تم حذف المستند بنجاح', 'success')
    return redirect(url_for('client_documents', client_id=client_id))

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
                <h3>📄 جميع المستندات في النظام</h3>
            </div>
            <div class="card-body">
                {% if documents %}
                <div class="table-responsive">
                    <table class="table table-striped">
                        <thead class="table-dark">
                            <tr>
                                <th>العميل</th>
                                <th>نوع المستند</th>
                                <th>الوصف</th>
                                <th>تاريخ الإضافة</th>
                                <th>الإجراءات</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for doc in documents %}
                            <tr>
                                <td><strong>{{ doc.client.full_name }}</strong></td>
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
                                <td>
                                    <a href="/client_documents/{{ doc.client_id }}" class="btn btn-sm btn-outline-info">👁️ عرض</a>
                                    <a href="/delete_client_document/{{ doc.id }}" class="btn btn-sm btn-outline-danger"
                                       onclick="return confirm('هل أنت متأكد من حذف هذا المستند؟')">🗑️ حذف</a>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                {% else %}
                <div class="text-center py-5">
                    <h5>📄 لا توجد مستندات في النظام</h5>
                    <p class="text-muted">ابدأ بإضافة عملاء ومستنداتهم</p>
                    <a href="/add_client" class="btn btn-primary">➕ إضافة عميل جديد</a>
                </div>
                {% endif %}
            </div>
        </div>
    </div>
</body>
</html>
    ''', documents=documents)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # إنشاء المستخدم الافتراضي
        if User.query.count() == 0:
            admin = User(
                username='admin', 
                first_name='فالح', 
                last_name='آل عيسى', 
                role='admin'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("✅ تم إنشاء المستخدم الافتراضي")
    
    print("🚀 نظام إدارة مكتب المحاماة على http://127.0.0.1:8080")
    print("👤 تسجيل الدخول: admin / admin123")
    print("🏛️ المحامي فالح بن عقاب آل عيسى")
    app.run(debug=True, host='127.0.0.1', port=8080)
