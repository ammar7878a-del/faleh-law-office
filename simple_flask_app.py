#!/usr/bin/env python3
"""
تطبيق Flask بسيط مع نموذج إضافة العميل
"""

from flask import Flask, render_template_string, request, redirect, url_for, flash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'simple-key'

@app.route('/')
def index():
    return render_template_string('''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="utf-8">
    <title>مكتب المحاماة</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-4">
        <div class="card">
            <div class="card-header bg-primary text-white">
                <h3>🏛️ مكتب المحاماة</h3>
            </div>
            <div class="card-body text-center">
                <h4>مرحباً بك</h4>
                <a href="/add_client" class="btn btn-success btn-lg">➕ إضافة عميل جديد</a>
                <a href="/test_form" class="btn btn-info btn-lg ms-2">🔍 اختبار النموذج</a>
            </div>
        </div>
        
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }} mt-3">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
    </div>
</body>
</html>
    ''')

@app.route('/test_form')
def test_form():
    return render_template_string('''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="utf-8">
    <title>اختبار النموذج</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-4">
        <div class="alert alert-info">
            <h4>🔍 اختبار النموذج من Flask</h4>
            <p>هذا نفس النموذج ولكن من خلال Flask</p>
        </div>
        
        <div class="card">
            <div class="card-header bg-success text-white">
                <h3>➕ إضافة عميل جديد مع المستندات</h3>
            </div>
            <div class="card-body">
                <form>
                    <!-- البيانات الأساسية -->
                    <div class="mb-4">
                        <h5 class="bg-light p-3 rounded">👤 البيانات الأساسية للعميل</h5>
                        
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">الاسم الأول <span class="text-danger">*</span></label>
                                    <input type="text" class="form-control" name="first_name" placeholder="أدخل الاسم الأول">
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">اسم العائلة <span class="text-danger">*</span></label>
                                    <input type="text" class="form-control" name="last_name" placeholder="أدخل اسم العائلة">
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
                    
                    <!-- المستندات -->
                    <div class="mb-4">
                        <h5 class="bg-light p-3 rounded">📄 المستندات والوثائق (اختياري)</h5>
                        
                        <div class="alert alert-info">
                            <strong>💡 تنبيه:</strong> يمكنك إضافة وصف للمستندات هنا.
                        </div>
                        
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">🆔 الهوية الشخصية</label>
                                    <input type="text" class="form-control" name="identity_desc" placeholder="مثال: هوية وطنية رقم 1234567890">
                                    <small class="text-muted">وصف مستند الهوية الشخصية</small>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">📋 الوكالة</label>
                                    <input type="text" class="form-control" name="power_of_attorney_desc" placeholder="مثال: وكالة عامة مؤرخة 2025/01/15">
                                    <small class="text-muted">وصف مستند الوكالة</small>
                                </div>
                            </div>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">📄 العقد</label>
                                    <input type="text" class="form-control" name="contract_desc" placeholder="مثال: عقد استشارة قانونية">
                                    <small class="text-muted">وصف العقد أو الاتفاقية</small>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">📎 مستندات أخرى</label>
                                    <input type="text" class="form-control" name="other_desc" placeholder="مثال: شهادات، تقارير، مراسلات">
                                    <small class="text-muted">أي مستندات إضافية</small>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="text-center">
                        <button type="submit" class="btn btn-success btn-lg">💾 حفظ العميل والمستندات</button>
                        <a href="/" class="btn btn-secondary btn-lg ms-2">← العودة</a>
                    </div>
                </form>
            </div>
        </div>
        
        <div class="card mt-4">
            <div class="card-body">
                <h6><strong>📋 الحقول المتوفرة:</strong></h6>
                <div class="row">
                    <div class="col-md-6">
                        <ul>
                            <li>✅ الاسم الأول (مطلوب)</li>
                            <li>✅ اسم العائلة (مطلوب)</li>
                            <li>✅ رقم الهوية الوطنية</li>
                            <li>✅ رقم الهاتف</li>
                            <li>✅ البريد الإلكتروني</li>
                            <li>✅ العنوان</li>
                        </ul>
                    </div>
                    <div class="col-md-6">
                        <ul>
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

@app.route('/add_client', methods=['GET', 'POST'])
def add_client():
    if request.method == 'POST':
        # معالجة البيانات
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        national_id = request.form.get('national_id')
        phone = request.form.get('phone')
        email = request.form.get('email')
        address = request.form.get('address')
        
        # المستندات
        identity_desc = request.form.get('identity_desc')
        power_of_attorney_desc = request.form.get('power_of_attorney_desc')
        contract_desc = request.form.get('contract_desc')
        other_desc = request.form.get('other_desc')
        
        # عد المستندات
        documents_count = sum(1 for doc in [identity_desc, power_of_attorney_desc, contract_desc, other_desc] if doc and doc.strip())
        
        flash(f'تم استلام البيانات: {first_name} {last_name} مع {documents_count} مستندات', 'success')
        return redirect(url_for('index'))
    
    # نفس النموذج من test_form ولكن مع POST
    return render_template_string('''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="utf-8">
    <title>إضافة عميل</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-4">
        <div class="card">
            <div class="card-header bg-success text-white">
                <h3>➕ إضافة عميل جديد مع المستندات</h3>
            </div>
            <div class="card-body">
                <form method="POST">
                    <!-- البيانات الأساسية -->
                    <div class="mb-4">
                        <h5 class="bg-light p-3 rounded">👤 البيانات الأساسية للعميل</h5>
                        
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">الاسم الأول <span class="text-danger">*</span></label>
                                    <input type="text" class="form-control" name="first_name" required placeholder="أدخل الاسم الأول">
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">اسم العائلة <span class="text-danger">*</span></label>
                                    <input type="text" class="form-control" name="last_name" required placeholder="أدخل اسم العائلة">
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
                    
                    <!-- المستندات -->
                    <div class="mb-4">
                        <h5 class="bg-light p-3 rounded">📄 المستندات والوثائق (اختياري)</h5>
                        
                        <div class="alert alert-info">
                            <strong>💡 تنبيه:</strong> يمكنك إضافة وصف للمستندات هنا.
                        </div>
                        
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">🆔 الهوية الشخصية</label>
                                    <input type="text" class="form-control" name="identity_desc" placeholder="مثال: هوية وطنية رقم 1234567890">
                                    <small class="text-muted">وصف مستند الهوية الشخصية</small>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">📋 الوكالة</label>
                                    <input type="text" class="form-control" name="power_of_attorney_desc" placeholder="مثال: وكالة عامة مؤرخة 2025/01/15">
                                    <small class="text-muted">وصف مستند الوكالة</small>
                                </div>
                            </div>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">📄 العقد</label>
                                    <input type="text" class="form-control" name="contract_desc" placeholder="مثال: عقد استشارة قانونية">
                                    <small class="text-muted">وصف العقد أو الاتفاقية</small>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">📎 مستندات أخرى</label>
                                    <input type="text" class="form-control" name="other_desc" placeholder="مثال: شهادات، تقارير، مراسلات">
                                    <small class="text-muted">أي مستندات إضافية</small>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="text-center">
                        <button type="submit" class="btn btn-success btn-lg">💾 حفظ العميل والمستندات</button>
                        <a href="/" class="btn btn-secondary btn-lg ms-2">← العودة</a>
                    </div>
                </form>
            </div>
        </div>
    </div>
</body>
</html>
    ''')

if __name__ == '__main__':
    print("🚀 تطبيق Flask البسيط على http://127.0.0.1:5000")
    print("📋 يحتوي على جميع الحقول المطلوبة")
    app.run(debug=True, host='127.0.0.1', port=5000)
