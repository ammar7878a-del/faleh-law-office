<?php
/*
نظام إدارة مكتب المحاماة
المحامي فالح بن عقاب آل عيسى

هذا الملف يعيد توجيه المستخدم لتطبيق Python Flask
*/

// التحقق من وجود تطبيق Python
$python_app_url = 'http://localhost:8080';  // غير هذا لرابط تطبيقك

// إعادة توجيه للتطبيق
header("Location: $python_app_url");
exit();
?>

<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>نظام إدارة مكتب المحاماة</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
    <style>
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .loading-card {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
        }
        .spinner-border {
            width: 3rem;
            height: 3rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="row justify-content-center">
            <div class="col-md-6">
                <div class="loading-card p-5 text-center">
                    <div class="mb-4">
                        <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">جاري التحميل...</span>
                        </div>
                    </div>
                    <h2 class="mb-3">🏛️ نظام إدارة مكتب المحاماة</h2>
                    <h5 class="text-muted mb-4">المحامي فالح بن عقاب آل عيسى</h5>
                    <p class="mb-4">جاري تحميل النظام...</p>
                    
                    <div class="alert alert-info">
                        <strong>ملاحظة:</strong> إذا لم يتم التحويل تلقائياً، 
                        <a href="app_for_hosting.py" class="alert-link">اضغط هنا</a>
                    </div>
                    
                    <div class="mt-4">
                        <small class="text-muted">
                            نظام شامل لإدارة العملاء والقضايا والفواتير والمستندات
                        </small>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // إعادة توجيه تلقائي بعد 3 ثواني
        setTimeout(function() {
            window.location.href = 'app_for_hosting.py';
        }, 3000);
    </script>
</body>
</html>
