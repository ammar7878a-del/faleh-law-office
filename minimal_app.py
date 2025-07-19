#!/usr/bin/env python3
from flask import Flask, render_template_string, request

app = Flask(__name__)
app.config['SECRET_KEY'] = 'test'

@app.route('/')
def index():
    return '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="utf-8">
    <title>اختبار</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-4">
        <h1>اختبار التطبيق</h1>
        <a href="/add_client" class="btn btn-primary">إضافة عميل</a>
    </div>
</body>
</html>
    '''

@app.route('/add_client', methods=['GET', 'POST'])
def add_client():
    if request.method == 'POST':
        return f"تم استلام: {request.form}"
    
    return '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="utf-8">
    <title>إضافة عميل</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-4">
        <h2>إضافة عميل جديد</h2>
        <form method="POST">
            <div class="mb-3">
                <label>الاسم الأول *</label>
                <input type="text" class="form-control" name="first_name" required>
            </div>
            <div class="mb-3">
                <label>اسم العائلة *</label>
                <input type="text" class="form-control" name="last_name" required>
            </div>
            <div class="mb-3">
                <label>🆔 رقم الهوية</label>
                <input type="text" class="form-control" name="national_id">
            </div>
            <div class="mb-3">
                <label>📱 الهاتف</label>
                <input type="text" class="form-control" name="phone">
            </div>
            <div class="mb-3">
                <label>📧 البريد</label>
                <input type="email" class="form-control" name="email">
            </div>
            <div class="mb-3">
                <label>🏠 العنوان</label>
                <input type="text" class="form-control" name="address">
            </div>
            
            <hr>
            <h4>📄 المستندات</h4>
            
            <div class="mb-3">
                <label>🆔 الهوية الشخصية</label>
                <input type="text" class="form-control" name="identity_desc">
            </div>
            <div class="mb-3">
                <label>📋 الوكالة</label>
                <input type="text" class="form-control" name="power_of_attorney_desc">
            </div>
            <div class="mb-3">
                <label>📄 العقد</label>
                <input type="text" class="form-control" name="contract_desc">
            </div>
            <div class="mb-3">
                <label>📎 مستندات أخرى</label>
                <input type="text" class="form-control" name="other_desc">
            </div>
            
            <button type="submit" class="btn btn-success">حفظ</button>
            <a href="/" class="btn btn-secondary">إلغاء</a>
        </form>
        
        <div class="mt-4 p-3 bg-light">
            <h6>الحقول المطلوبة:</h6>
            <ul>
                <li>الاسم الأول</li>
                <li>اسم العائلة</li>
                <li>رقم الهوية</li>
                <li>الهاتف</li>
                <li>البريد</li>
                <li>العنوان</li>
                <li>الهوية الشخصية</li>
                <li>الوكالة</li>
                <li>العقد</li>
                <li>مستندات أخرى</li>
            </ul>
        </div>
    </div>
</body>
</html>
    '''

if __name__ == '__main__':
    print("🚀 تطبيق مبسط على http://127.0.0.1:5000")
    app.run(debug=True, host='127.0.0.1', port=5000)
