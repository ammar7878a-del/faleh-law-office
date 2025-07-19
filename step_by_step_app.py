#!/usr/bin/env python3
"""
تطبيق تدريجي لاختبار المشكلة
"""

from flask import Flask, request

app = Flask(__name__)

@app.route('/')
def index():
    return '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="utf-8">
    <title>اختبار تدريجي</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-4">
        <h1>🔍 اختبار تدريجي</h1>
        <div class="list-group">
            <a href="/step1" class="list-group-item">الخطوة 1: الحقول الأساسية فقط</a>
            <a href="/step2" class="list-group-item">الخطوة 2: إضافة رقم الهوية</a>
            <a href="/step3" class="list-group-item">الخطوة 3: إضافة العنوان</a>
            <a href="/step4" class="list-group-item">الخطوة 4: إضافة المستندات</a>
            <a href="/final" class="list-group-item">النموذج الكامل</a>
        </div>
    </div>
</body>
</html>
    '''

@app.route('/step1')
def step1():
    return '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="utf-8">
    <title>الخطوة 1</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-4">
        <h2>الخطوة 1: الحقول الأساسية فقط</h2>
        <form>
            <div class="mb-3">
                <label>الاسم الأول *</label>
                <input type="text" class="form-control" name="first_name">
            </div>
            <div class="mb-3">
                <label>اسم العائلة *</label>
                <input type="text" class="form-control" name="last_name">
            </div>
            <div class="mb-3">
                <label>البريد الإلكتروني</label>
                <input type="email" class="form-control" name="email">
            </div>
            <div class="mb-3">
                <label>الهاتف</label>
                <input type="text" class="form-control" name="phone">
            </div>
        </form>
        <a href="/" class="btn btn-secondary">← العودة</a>
        <a href="/step2" class="btn btn-primary">الخطوة التالية →</a>
    </div>
</body>
</html>
    '''

@app.route('/step2')
def step2():
    return '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="utf-8">
    <title>الخطوة 2</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-4">
        <h2>الخطوة 2: إضافة رقم الهوية</h2>
        <form>
            <div class="mb-3">
                <label>الاسم الأول *</label>
                <input type="text" class="form-control" name="first_name">
            </div>
            <div class="mb-3">
                <label>اسم العائلة *</label>
                <input type="text" class="form-control" name="last_name">
            </div>
            <div class="mb-3">
                <label>🆔 رقم الهوية الوطنية</label>
                <input type="text" class="form-control" name="national_id">
            </div>
            <div class="mb-3">
                <label>البريد الإلكتروني</label>
                <input type="email" class="form-control" name="email">
            </div>
            <div class="mb-3">
                <label>الهاتف</label>
                <input type="text" class="form-control" name="phone">
            </div>
        </form>
        <a href="/step1" class="btn btn-secondary">← السابق</a>
        <a href="/step3" class="btn btn-primary">التالي →</a>
    </div>
</body>
</html>
    '''

@app.route('/step3')
def step3():
    return '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="utf-8">
    <title>الخطوة 3</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-4">
        <h2>الخطوة 3: إضافة العنوان</h2>
        <form>
            <div class="mb-3">
                <label>الاسم الأول *</label>
                <input type="text" class="form-control" name="first_name">
            </div>
            <div class="mb-3">
                <label>اسم العائلة *</label>
                <input type="text" class="form-control" name="last_name">
            </div>
            <div class="mb-3">
                <label>🆔 رقم الهوية الوطنية</label>
                <input type="text" class="form-control" name="national_id">
            </div>
            <div class="mb-3">
                <label>🏠 العنوان</label>
                <input type="text" class="form-control" name="address">
            </div>
            <div class="mb-3">
                <label>البريد الإلكتروني</label>
                <input type="email" class="form-control" name="email">
            </div>
            <div class="mb-3">
                <label>الهاتف</label>
                <input type="text" class="form-control" name="phone">
            </div>
        </form>
        <a href="/step2" class="btn btn-secondary">← السابق</a>
        <a href="/step4" class="btn btn-primary">التالي →</a>
    </div>
</body>
</html>
    '''

@app.route('/step4')
def step4():
    return '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="utf-8">
    <title>الخطوة 4</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-4">
        <h2>الخطوة 4: إضافة المستندات</h2>
        <form>
            <h5>البيانات الأساسية</h5>
            <div class="mb-3">
                <label>الاسم الأول *</label>
                <input type="text" class="form-control" name="first_name">
            </div>
            <div class="mb-3">
                <label>اسم العائلة *</label>
                <input type="text" class="form-control" name="last_name">
            </div>
            <div class="mb-3">
                <label>🆔 رقم الهوية الوطنية</label>
                <input type="text" class="form-control" name="national_id">
            </div>
            <div class="mb-3">
                <label>🏠 العنوان</label>
                <input type="text" class="form-control" name="address">
            </div>
            <div class="mb-3">
                <label>البريد الإلكتروني</label>
                <input type="email" class="form-control" name="email">
            </div>
            <div class="mb-3">
                <label>الهاتف</label>
                <input type="text" class="form-control" name="phone">
            </div>
            
            <hr>
            <h5>📄 المستندات</h5>
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
        </form>
        <a href="/step3" class="btn btn-secondary">← السابق</a>
        <a href="/final" class="btn btn-success">النموذج الكامل →</a>
    </div>
</body>
</html>
    '''

@app.route('/final')
def final():
    return '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="utf-8">
    <title>النموذج الكامل</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-4">
        <div class="alert alert-success">
            <h4>🎉 النموذج الكامل</h4>
            <p>إذا وصلت هنا ورأيت جميع الحقول، فالمشكلة محلولة!</p>
        </div>
        
        <form method="POST" action="/save">
            <div class="card mb-3">
                <div class="card-header">👤 البيانات الأساسية</div>
                <div class="card-body">
                    <div class="mb-3">
                        <label>الاسم الأول *</label>
                        <input type="text" class="form-control" name="first_name" required>
                    </div>
                    <div class="mb-3">
                        <label>اسم العائلة *</label>
                        <input type="text" class="form-control" name="last_name" required>
                    </div>
                    <div class="mb-3">
                        <label>🆔 رقم الهوية الوطنية</label>
                        <input type="text" class="form-control" name="national_id">
                    </div>
                    <div class="mb-3">
                        <label>🏠 العنوان</label>
                        <input type="text" class="form-control" name="address">
                    </div>
                    <div class="mb-3">
                        <label>📧 البريد الإلكتروني</label>
                        <input type="email" class="form-control" name="email">
                    </div>
                    <div class="mb-3">
                        <label>📱 الهاتف</label>
                        <input type="text" class="form-control" name="phone">
                    </div>
                </div>
            </div>
            
            <div class="card mb-3">
                <div class="card-header">📄 المستندات</div>
                <div class="card-body">
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
                </div>
            </div>
            
            <button type="submit" class="btn btn-success">💾 حفظ العميل والمستندات</button>
            <a href="/" class="btn btn-secondary">← العودة</a>
        </form>
    </div>
</body>
</html>
    '''

@app.route('/save', methods=['POST'])
def save():
    data = dict(request.form)
    return f'''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="utf-8">
    <title>تم الحفظ</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-4">
        <div class="alert alert-success">
            <h4>✅ تم حفظ البيانات بنجاح!</h4>
            <pre>{data}</pre>
        </div>
        <a href="/" class="btn btn-primary">← العودة للرئيسية</a>
        <a href="/final" class="btn btn-secondary">إضافة عميل آخر</a>
    </div>
</body>
</html>
    '''

if __name__ == '__main__':
    print("🚀 اختبار تدريجي على http://127.0.0.1:5000")
    print("🔍 سنختبر كل خطوة لمعرفة أين تتوقف المشكلة")
    app.run(debug=True, host='127.0.0.1', port=5000)
