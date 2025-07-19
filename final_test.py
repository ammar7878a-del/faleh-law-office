#!/usr/bin/env python3
from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    return '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="utf-8">
    <title>الاختبار النهائي</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-4">
        <div class="alert alert-success">
            <h2>🎉 التطبيق الجديد يعمل!</h2>
            <p>إذا رأيت هذه الرسالة، فالتطبيق الجديد يعمل بشكل صحيح</p>
        </div>
        <a href="/form" class="btn btn-primary btn-lg">📋 جرب النموذج الكامل</a>
    </div>
</body>
</html>
    '''

@app.route('/form')
def form():
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
        <div class="alert alert-info">
            <h4>📋 النموذج الكامل - اختبار نهائي</h4>
        </div>
        
        <form>
            <div class="card mb-3">
                <div class="card-header bg-primary text-white">
                    <h5>👤 البيانات الأساسية</h5>
                </div>
                <div class="card-body">
                    <div class="mb-3">
                        <label class="form-label">الاسم الأول *</label>
                        <input type="text" class="form-control" name="first_name" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">اسم العائلة *</label>
                        <input type="text" class="form-control" name="last_name" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">🆔 رقم الهوية الوطنية</label>
                        <input type="text" class="form-control" name="national_id" placeholder="مثال: 1234567890">
                    </div>
                    <div class="mb-3">
                        <label class="form-label">📱 رقم الهاتف</label>
                        <input type="text" class="form-control" name="phone" placeholder="مثال: 0501234567">
                    </div>
                    <div class="mb-3">
                        <label class="form-label">📧 البريد الإلكتروني</label>
                        <input type="email" class="form-control" name="email" placeholder="مثال: client@email.com">
                    </div>
                    <div class="mb-3">
                        <label class="form-label">🏠 العنوان</label>
                        <input type="text" class="form-control" name="address" placeholder="العنوان الكامل">
                    </div>
                </div>
            </div>
            
            <div class="card mb-3">
                <div class="card-header bg-success text-white">
                    <h5>📄 المستندات والوثائق</h5>
                </div>
                <div class="card-body">
                    <div class="alert alert-info">
                        <strong>💡 ملاحظة:</strong> يمكنك إضافة وصف للمستندات هنا
                    </div>
                    
                    <div class="mb-3">
                        <label class="form-label">🆔 الهوية الشخصية</label>
                        <input type="text" class="form-control" name="identity_desc" placeholder="مثال: هوية وطنية رقم 1234567890">
                        <small class="text-muted">وصف مستند الهوية الشخصية</small>
                    </div>
                    
                    <div class="mb-3">
                        <label class="form-label">📋 الوكالة</label>
                        <input type="text" class="form-control" name="power_of_attorney_desc" placeholder="مثال: وكالة عامة مؤرخة 2025/01/15">
                        <small class="text-muted">وصف مستند الوكالة</small>
                    </div>
                    
                    <div class="mb-3">
                        <label class="form-label">📄 العقد</label>
                        <input type="text" class="form-control" name="contract_desc" placeholder="مثال: عقد استشارة قانونية">
                        <small class="text-muted">وصف العقد أو الاتفاقية</small>
                    </div>
                    
                    <div class="mb-3">
                        <label class="form-label">📎 مستندات أخرى</label>
                        <input type="text" class="form-control" name="other_desc" placeholder="مثال: شهادات، تقارير، مراسلات">
                        <small class="text-muted">أي مستندات إضافية</small>
                    </div>
                </div>
            </div>
            
            <div class="text-center">
                <button type="submit" class="btn btn-success btn-lg">💾 حفظ العميل والمستندات</button>
                <a href="/" class="btn btn-secondary btn-lg ms-2">← العودة</a>
            </div>
        </form>
        
        <div class="card mt-4">
            <div class="card-body">
                <h6><strong>📋 جميع الحقول المطلوبة:</strong></h6>
                <div class="row">
                    <div class="col-md-6">
                        <h6 class="text-primary">البيانات الأساسية:</h6>
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
                        <h6 class="text-success">المستندات:</h6>
                        <ul>
                            <li>✅ وصف الهوية الشخصية</li>
                            <li>✅ وصف الوكالة</li>
                            <li>✅ وصف العقد</li>
                            <li>✅ وصف المستندات الأخرى</li>
                        </ul>
                    </div>
                </div>
                
                <div class="alert alert-warning mt-3">
                    <strong>🔍 اختبار:</strong> إذا رأيت جميع هذه الحقول، فالمشكلة محلولة!
                </div>
            </div>
        </div>
    </div>
</body>
</html>
    '''

if __name__ == '__main__':
    print("🚀 الاختبار النهائي على http://127.0.0.1:8080")
    print("📋 منفذ مختلف لتجنب التداخل")
    app.run(debug=True, host='127.0.0.1', port=8080)
