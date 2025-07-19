#!/usr/bin/env python3
from flask import Flask, render_template_string

app = Flask(__name__)

@app.route('/')
def index():
    return render_template_string('''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="utf-8">
    <title>نموذج إضافة العميل - عرض توضيحي</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
    <style>
        .demo-note { background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
    </style>
</head>
<body>
    <div class="container mt-4">
        <div class="demo-note">
            <h4>🎯 عرض توضيحي: نموذج إضافة العميل مع جميع الحقول</h4>
            <p>هذا النموذج يحتوي على جميع الحقول المطلوبة بما في ذلك رقم الهوية والمستندات</p>
        </div>
        
        <form>
            <!-- البيانات الأساسية -->
            <div class="card mb-4">
                <div class="card-header bg-primary text-white">
                    <h5>👤 البيانات الأساسية</h5>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label class="form-label">الاسم الأول <span class="text-danger">*</span></label>
                                <input type="text" class="form-control" name="first_name" required>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label class="form-label">اسم العائلة <span class="text-danger">*</span></label>
                                <input type="text" class="form-control" name="last_name" required>
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
            </div>
            
            <!-- المستندات -->
            <div class="card mb-4">
                <div class="card-header bg-success text-white">
                    <h5>📄 المستندات والوثائق (اختياري)</h5>
                </div>
                <div class="card-body">
                    <div class="alert alert-info">
                        <strong>💡 ملاحظة:</strong> يمكنك إضافة وصف للمستندات هنا. سيتم حفظها كسجلات ويمكن إدارتها لاحقاً.
                    </div>
                    
                    <div class="row">
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label class="form-label">🆔 الهوية الشخصية</label>
                                <input type="text" class="form-control" name="identity_desc" 
                                       placeholder="مثال: هوية وطنية رقم 1234567890">
                                <small class="text-muted">وصف مستند الهوية الشخصية</small>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label class="form-label">📋 الوكالة</label>
                                <input type="text" class="form-control" name="power_of_attorney_desc" 
                                       placeholder="مثال: وكالة عامة مؤرخة 2025/01/15">
                                <small class="text-muted">وصف مستند الوكالة</small>
                            </div>
                        </div>
                    </div>
                    
                    <div class="row">
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label class="form-label">📄 العقد</label>
                                <input type="text" class="form-control" name="contract_desc" 
                                       placeholder="مثال: عقد استشارة قانونية">
                                <small class="text-muted">وصف العقد أو الاتفاقية</small>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label class="form-label">📎 مستندات أخرى</label>
                                <input type="text" class="form-control" name="other_desc" 
                                       placeholder="مثال: شهادات، تقارير، مراسلات">
                                <small class="text-muted">أي مستندات إضافية</small>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- أزرار الحفظ -->
            <div class="card">
                <div class="card-body text-center">
                    <button type="submit" class="btn btn-success btn-lg me-3">
                        💾 حفظ العميل والمستندات
                    </button>
                    <button type="reset" class="btn btn-secondary btn-lg">
                        🔄 إعادة تعيين
                    </button>
                </div>
            </div>
        </form>
        
        <div class="mt-4 p-3 bg-light rounded">
            <h6><strong>✅ الحقول المتوفرة في هذا النموذج:</strong></h6>
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
                <strong>⚠️ هام:</strong> إذا كانت هذه الحقول لا تظهر في التطبيق الأصلي، فهناك مشكلة في الكود أو في عرض المتصفح.
            </div>
        </div>
    </div>
</body>
</html>
    ''')

if __name__ == '__main__':
    print("🚀 عرض توضيحي للنموذج على http://127.0.0.1:5000")
    print("📋 يحتوي على جميع الحقول المطلوبة")
    app.run(debug=True, host='127.0.0.1', port=5000)
