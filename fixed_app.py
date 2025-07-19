#!/usr/bin/env python3
"""
نظام إدارة مكتب المحاماة - النسخة المصححة
"""

from flask import Flask, render_template_string, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import random

# إنشاء التطبيق
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key-for-testing'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fixed_law_system.db'
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
    email = db.Column(db.String(120), unique=True, nullable=False)
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
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    national_id = db.Column(db.String(20))  # رقم الهوية
    address = db.Column(db.Text)  # العنوان
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

class ClientDocument(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    document_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200))
    file_name = db.Column(db.String(255), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    client = db.relationship('Client', backref='client_documents')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# الصفحة الرئيسية
@app.route('/')
def index():
    if current_user.is_authenticated:
        clients_count = Client.query.count()
        return render_template_string('''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="utf-8">
    <title>المحامي فالح بن عقاب آل عيسى</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
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
        
        <div class="row">
            <div class="col-md-3">
                <div class="card">
                    <div class="card-header bg-primary text-white">
                        <h5>📋 القائمة الرئيسية</h5>
                    </div>
                    <div class="list-group list-group-flush">
                        <a href="/" class="list-group-item list-group-item-action active">🏠 الرئيسية</a>
                        <a href="/clients" class="list-group-item list-group-item-action">👥 العملاء ({{ clients_count }})</a>
                    </div>
                </div>
            </div>
            <div class="col-md-9">
                <div class="card text-white bg-primary mb-3">
                    <div class="card-body text-center">
                        <h2>👥</h2>
                        <h4>{{ clients_count }}</h4>
                        <p>العملاء المسجلين</p>
                        <a href="/clients" class="btn btn-light btn-sm">عرض العملاء</a>
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header">
                        <h5>🚀 الإجراءات السريعة</h5>
                    </div>
                    <div class="card-body">
                        <div class="d-grid gap-2">
                            <a href="/add_client" class="btn btn-primary btn-lg">👥 إضافة عميل جديد مع المستندات</a>
                            <a href="/clients" class="btn btn-success btn-lg">📋 عرض جميع العملاء</a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
        ''', clients_count=clients_count)
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
        body { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
    </style>
</head>
<body class="d-flex align-items-center">
    <div class="container">
        <div class="row justify-content-center">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header text-center bg-primary text-white">
                        <h3>⚖️ المحامي فالح بن عقاب آل عيسى</h3>
                    </div>
                    <div class="card-body">
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
                                <input type="text" class="form-control" id="username" name="username" required>
                            </div>
                            <div class="mb-3">
                                <label for="password" class="form-label">🔒 كلمة المرور</label>
                                <input type="password" class="form-control" id="password" name="password" required>
                            </div>
                            <button type="submit" class="btn btn-primary w-100">🚀 تسجيل الدخول</button>
                        </form>
                        <hr>
                        <div class="text-center">
                            <small><strong>admin</strong> / <strong>admin123</strong></small>
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
            <div class="card-header d-flex justify-content-between">
                <h3>👥 العملاء</h3>
                <a href="/add_client" class="btn btn-primary">➕ إضافة عميل</a>
            </div>
            <div class="card-body">
                {% with messages = get_flashed_messages(with_categories=true) %}
                    {% if messages %}
                        {% for category, message in messages %}
                            <div class="alert alert-{{ 'danger' if category == 'error' else category }}">{{ message }}</div>
                        {% endfor %}
                    {% endif %}
                {% endwith %}
                <table class="table">
                    <thead>
                        <tr><th>الاسم</th><th>رقم الهوية</th><th>الهاتف</th><th>البريد</th><th>المستندات</th><th>الإجراءات</th></tr>
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
                                <a href="/client_documents/{{ client.id }}" class="btn btn-sm btn-outline-info ms-1">📄 عرض</a>
                            </td>
                            <td>
                                <a href="/edit_client/{{ client.id }}" class="btn btn-sm btn-outline-warning">✏️ تعديل</a>
                                <a href="/delete_client/{{ client.id }}" class="btn btn-sm btn-outline-danger"
                                   onclick="return confirm('هل أنت متأكد من حذف العميل {{ client.full_name }}؟')">🗑️ حذف</a>
                            </td>
                        </tr>
                        {% else %}
                        <tr><td colspan="6" class="text-center">
                            <div class="py-4">
                                <h5>لا توجد عملاء مسجلين</h5>
                                <p class="text-muted">ابدأ بإضافة عميل جديد</p>
                                <a href="/add_client" class="btn btn-primary">➕ إضافة عميل جديد</a>
                            </div>
                        </td></tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
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
            email=request.form.get('email'),
            phone=request.form.get('phone'),
            national_id=request.form.get('national_id'),
            address=request.form.get('address')
        )
        db.session.add(client)
        db.session.flush()  # للحصول على ID العميل

        # إضافة المستندات
        document_types = [
            ('identity', '🆔 الهوية الشخصية'),
            ('power_of_attorney', '📋 الوكالة'),
            ('contract', '📄 العقد'),
            ('other', '📎 مستندات أخرى')
        ]

        for doc_type, doc_name in document_types:
            desc_field = f'{doc_type}_desc'
            if desc_field in request.form and request.form[desc_field].strip():
                doc = ClientDocument(
                    document_type=doc_type,
                    description=request.form[desc_field],
                    file_name=f"doc_{client.id}_{doc_type}.txt",
                    client_id=client.id
                )
                db.session.add(doc)

        db.session.commit()
        flash(f'تم إضافة العميل {client.full_name} بنجاح مع {len([d for d in document_types if f"{d[0]}_desc" in request.form and request.form[f"{d[0]}_desc"].strip()])} مستندات', 'success')
        return redirect(url_for('clients'))

    return render_template_string('''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="utf-8">
    <title>إضافة عميل</title>
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
            <div class="card-header bg-primary text-white">
                <h3>➕ إضافة عميل جديد مع المستندات</h3>
            </div>
            <div class="card-body">
                <form method="POST">
                    <!-- البيانات الأساسية -->
                    <div class="card mb-4">
                        <div class="card-header bg-light">
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
                                        <label class="form-label">رقم الهوية</label>
                                        <input type="text" class="form-control" name="national_id" placeholder="مثال: 1234567890">
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">الهاتف</label>
                                        <input type="text" class="form-control" name="phone" placeholder="مثال: 0501234567">
                                    </div>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">البريد الإلكتروني</label>
                                        <input type="email" class="form-control" name="email" placeholder="مثال: client@email.com">
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">العنوان</label>
                                        <input type="text" class="form-control" name="address" placeholder="العنوان الكامل">
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- المستندات -->
                    <div class="card mb-4">
                        <div class="card-header bg-info text-white">
                            <h5>📄 المستندات (اختياري)</h5>
                        </div>
                        <div class="card-body">
                            <div class="alert alert-info">
                                <i class="fas fa-info-circle"></i> يمكنك إضافة وصف للمستندات هنا. سيتم إنشاء سجلات للمستندات ويمكنك إدارتها لاحقاً.
                            </div>
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">🆔 الهوية الشخصية</label>
                                        <input type="text" class="form-control" name="identity_desc" placeholder="مثال: هوية وطنية رقم 1234567890">
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">📋 الوكالة</label>
                                        <input type="text" class="form-control" name="power_of_attorney_desc" placeholder="مثال: وكالة عامة مؤرخة 2025/01/15">
                                    </div>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">📄 العقد</label>
                                        <input type="text" class="form-control" name="contract_desc" placeholder="مثال: عقد استشارة قانونية">
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">📎 مستندات أخرى</label>
                                        <input type="text" class="form-control" name="other_desc" placeholder="مثال: شهادات، تقارير، إلخ">
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="d-flex gap-2">
                        <button type="submit" class="btn btn-success btn-lg">💾 حفظ العميل والمستندات</button>
                        <a href="/clients" class="btn btn-secondary btn-lg">❌ إلغاء</a>
                    </div>
                </form>
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
            admin = User(username='admin', email='admin@example.com', 
                        first_name='مدير', last_name='النظام', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("✅ تم إنشاء المستخدم الافتراضي")
    
    print("🚀 تشغيل التطبيق على http://127.0.0.1:5000")
    print("👤 تسجيل الدخول: admin / admin123")
    app.run(debug=True, host='127.0.0.1', port=5000, use_reloader=False)
