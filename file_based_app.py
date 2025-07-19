#!/usr/bin/env python3
"""
تطبيق Flask مع ملفات HTML منفصلة
"""

from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'file-based-key'

@app.route('/')
def index():
    return '''
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
                <a href="/add_client" class="btn btn-success btn-lg">➕ إضافة عميل جديد مع المستندات</a>
            </div>
        </div>
        
        <div class="mt-3">
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="alert alert-{{ category }}">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
        </div>
    </div>
</body>
</html>
    '''

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
        
        flash(f'تم حفظ العميل: {first_name} {last_name} مع {documents_count} مستندات', 'success')
        flash(f'البيانات: هوية={national_id}, هاتف={phone}, بريد={email}, عنوان={address}', 'info')
        flash(f'المستندات: هوية={identity_desc}, وكالة={power_of_attorney_desc}, عقد={contract_desc}, أخرى={other_desc}', 'info')
        
        return redirect(url_for('index'))
    
    # استخدام ملف HTML منفصل
    return render_template('add_client.html')

if __name__ == '__main__':
    print("🚀 تطبيق مع ملفات HTML منفصلة على http://127.0.0.1:5000")
    print("📁 يستخدم ملف templates/add_client.html")
    app.run(debug=True, host='127.0.0.1', port=5000)
