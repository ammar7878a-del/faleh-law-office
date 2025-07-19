#!/usr/bin/env python3
"""
تطبيق مكتب المحاماة - النسخة النهائية العاملة
"""

from flask import Flask, render_template_string, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'final-working-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///final_working.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

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
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    client = db.relationship('Client', backref='client_documents')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    if current_user.is_authenticated:
        clients_count = Client.query.count()
        return render_template_string('''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="utf-8">
    <title>مكتب المحاماة</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-dark bg-dark">
        <div class="container">
            <span class="navbar-brand">🏛️ مكتب المحاماة</span>
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
                    <div class="alert alert-{{ category }} alert-dismissible fade show">
                        {{ message }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        <div class="row">
            <div class="col-md-4">
                <div class="card text-white bg-primary">
                    <div class="card-body text-center">
                        <h2>👥</h2>
                        <h4>{{ clients_count }}</h4>
                        <p>العملاء</p>
                        <a href="/clients" class="btn btn-light">عرض العملاء</a>
                    </div>
                </div>
            </div>
            <div class="col-md-8">
                <div class="card">
                    <div class="card-header">
                        <h5>الإجراءات السريعة</h5>
                    </div>
                    <div class="card-body">
                        <a href="/add_client" class="btn btn-success btn-lg">➕ إضافة عميل جديد مع المستندات</a>
                        <a href="/clients" class="btn btn-primary btn-lg ms-2">👥 عرض العملاء</a>
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
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('تم تسجيل الدخول بنجاح', 'success')
            return redirect(url_for('index'))
        else:
            flash('خطأ في اسم المستخدم أو كلمة المرور', 'danger')
    
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
                        <h4>🏛️ مكتب المحاماة</h4>
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
                                <label class="form-label">اسم المستخدم</label>
                                <input type="text" class="form-control" name="username" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">كلمة المرور</label>
                                <input type="password" class="form-control" name="password" required>
                            </div>
                            <button type="submit" class="btn btn-primary w-100">دخول</button>
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
def logout():
    logout_user()
    flash('تم تسجيل الخروج', 'info')
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
            <a class="navbar-brand" href="/">🏛️ مكتب المحاماة</a>
            <div>
                <a class="btn btn-outline-light btn-sm" href="/">الرئيسية</a>
                <a class="btn btn-outline-light btn-sm ms-2" href="/logout">خروج</a>
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
                <table class="table table-striped">
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
                                <a href="/edit_client/{{ client.id }}" class="btn btn-sm btn-warning">✏️</a>
                                <a href="/delete_client/{{ client.id }}" class="btn btn-sm btn-danger" 
                                   onclick="return confirm('حذف {{ client.full_name }}؟')">🗑️</a>
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
        .section-title { background: #f8f9fa; padding: 15px; margin-bottom: 20px; border-radius: 5px; border-left: 4px solid #007bff; }
        .required { color: red; font-weight: bold; }
        .form-control-lg { font-size: 1.1rem; }
    </style>
</head>
<body>
    <nav class="navbar navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/">🏛️ مكتب المحاماة</a>
            <div>
                <a class="btn btn-outline-light btn-sm" href="/clients">العملاء</a>
                <a class="btn btn-outline-light btn-sm ms-2" href="/">الرئيسية</a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="card shadow">
            <div class="card-header bg-success text-white">
                <h3 class="mb-0">➕ إضافة عميل جديد مع المستندات</h3>
            </div>
            <div class="card-body">
                <form method="POST">
                    <!-- البيانات الأساسية -->
                    <div class="form-section">
                        <div class="section-title">
                            <h5 class="mb-0">👤 البيانات الأساسية للعميل</h5>
                        </div>

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

                    <!-- المستندات -->
                    <div class="form-section">
                        <div class="section-title">
                            <h5 class="mb-0">📄 المستندات والوثائق (اختياري)</h5>
                        </div>

                        <div class="alert alert-info">
                            <strong>💡 تنبيه:</strong> يمكنك إضافة وصف للمستندات هنا. سيتم إنشاء سجلات للمستندات ويمكن إدارتها لاحقاً من صفحة العميل.
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

                    <!-- أزرار الحفظ -->
                    <div class="text-center">
                        <button type="submit" class="btn btn-success btn-lg me-3">
                            💾 حفظ العميل والمستندات
                        </button>
                        <a href="/clients" class="btn btn-secondary btn-lg">
                            ❌ إلغاء
                        </a>
                    </div>
                </form>
            </div>
        </div>

        <!-- معلومات إضافية -->
        <div class="card mt-4">
            <div class="card-body">
                <h6><strong>📋 الحقول المتوفرة في هذا النموذج:</strong></h6>
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
</body>
</html>
    ''')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        if User.query.count() == 0:
            admin = User(username='admin', first_name='مدير', last_name='النظام')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("✅ تم إنشاء المستخدم الافتراضي")
    
    print("🚀 التطبيق النهائي العامل على http://127.0.0.1:5000")
    print("👤 تسجيل الدخول: admin / admin123")
    app.run(debug=True, host='127.0.0.1', port=5000, use_reloader=False)
