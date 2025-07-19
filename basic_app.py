#!/usr/bin/env python3
"""
تطبيق أساسي لاختبار Flask
"""

from flask import Flask, render_template_string

app = Flask(__name__)
app.config['SECRET_KEY'] = 'test-secret-key'

@app.route('/')
def index():
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="utf-8">
        <title>اختبار التطبيق</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-5">
            <div class="row justify-content-center">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header text-center">
                            <h3>🏛️ المحامي فالح بن عقاب آل عيسى</h3>
                        </div>
                        <div class="card-body text-center">
                            <h5>✅ التطبيق يعمل بنجاح!</h5>
                            <p>هذا اختبار أساسي للتأكد من عمل Flask</p>
                            <hr>
                            <div class="alert alert-info">
                                <strong>المشكلة:</strong> التطبيق الأساسي يعمل<br>
                                <strong>الحل:</strong> المشكلة في التطبيق الرئيسي
                            </div>
                            <a href="/test" class="btn btn-primary">اختبار صفحة أخرى</a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    ''')

@app.route('/test')
def test():
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="utf-8">
        <title>صفحة الاختبار</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-5">
            <div class="alert alert-success text-center">
                <h4>🎉 صفحة الاختبار تعمل!</h4>
                <p>Flask يعمل بشكل صحيح</p>
                <a href="/" class="btn btn-secondary">العودة للرئيسية</a>
            </div>
        </div>
    </body>
    </html>
    ''')

if __name__ == '__main__':
    print("🚀 تشغيل التطبيق الأساسي...")
    print("🌐 الرابط: http://127.0.0.1:5000")
    print("اضغط Ctrl+C لإيقاف التطبيق")
    app.run(debug=True, host='127.0.0.1', port=5000)
