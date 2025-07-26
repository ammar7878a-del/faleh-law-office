# نظام إدارة مكتب المحاماة - تشغيل آمن
# Law Office Management System - Safe Start

# تعيين ترميز UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "🏛️  نظام إدارة مكتب المحاماة" -ForegroundColor Yellow
Write-Host "⚖️  Law Office Management System" -ForegroundColor Yellow  
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "🔍 فحص إعدادات قاعدة البيانات..." -ForegroundColor Blue

# فحص متغير قاعدة البيانات
$DATABASE_URL = $env:DATABASE_URL
$DATABASE_OK = $false

if ($DATABASE_URL -and ($DATABASE_URL -like "*postgresql*" -or $DATABASE_URL -like "*postgres*")) {
    Write-Host "✅ تم العثور على قاعدة بيانات خارجية!" -ForegroundColor Green
    Write-Host "🔒 البيانات محفوظة دائماً - لن تُحذف أبداً!" -ForegroundColor Green
    Write-Host "🎉 مشكلة فقدان البيانات محلولة!" -ForegroundColor Green
    
    # إخفاء كلمة المرور في العرض
    $safe_url = $DATABASE_URL
    if ($safe_url -match "@" -and $safe_url -match ":") {
        $safe_url = $safe_url -replace ":[^@]*@", ":****@"
    }
    
    $server = ($safe_url -split "@")[1] -split "/" | Select-Object -First 1
    Write-Host "🌐 الخادم: $server" -ForegroundColor Cyan
    $DATABASE_OK = $true
} else {
    Write-Host "🚨 تحذير: لا توجد قاعدة بيانات خارجية!" -ForegroundColor Red
    Write-Host "⚠️  البيانات ستُحذف عند إعادة التشغيل!" -ForegroundColor Yellow
    Write-Host "💥 هذا يعني أن جميع البيانات ستفقد!" -ForegroundColor Red
    Write-Host ""
    Write-Host "🔧 لحل هذه المشكلة:" -ForegroundColor Yellow
    Write-Host "   1. راجع ملف QUICK_DATABASE_FIX.md" -ForegroundColor White
    Write-Host "   2. أنشئ قاعدة بيانات مجانية على Supabase" -ForegroundColor White
    Write-Host "   3. أضف متغير DATABASE_URL في إعدادات الخادم" -ForegroundColor White
    Write-Host "   4. أعد تشغيل التطبيق" -ForegroundColor White
    Write-Host ""
    Write-Host "🔗 رابط Supabase: https://supabase.com" -ForegroundColor Cyan
    Write-Host "📖 دليل سريع: QUICK_DATABASE_FIX.md" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan

# فحص الملفات المطلوبة
Write-Host "📁 فحص الملفات المطلوبة..." -ForegroundColor Blue

$required_files = @("final_working.py", "requirements.txt")
$missing_files = @()

foreach ($file in $required_files) {
    if (Test-Path $file) {
        Write-Host "   ✅ $file" -ForegroundColor Green
    } else {
        Write-Host "   ❌ $file" -ForegroundColor Red
        $missing_files += $file
    }
}

if ($missing_files.Count -gt 0) {
    Write-Host ""
    Write-Host "❌ ملفات مفقودة: $($missing_files -join ', ')" -ForegroundColor Red
    Write-Host "لا يمكن المتابعة بدون هذه الملفات." -ForegroundColor Red
    Read-Host "اضغط Enter للخروج"
    exit 1
}

# إنشاء المجلدات المطلوبة
Write-Host ""
Write-Host "📂 إنشاء المجلدات المطلوبة..." -ForegroundColor Blue

$directories = @("uploads", "uploads/documents", "uploads/logos", "instance")

foreach ($dir in $directories) {
    try {
        if (!(Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
        }
        Write-Host "   ✅ $dir" -ForegroundColor Green
    } catch {
        Write-Host "   ❌ خطأ في إنشاء $dir`: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "🚀 معلومات التشغيل:" -ForegroundColor Yellow
Write-Host "================================================================" -ForegroundColor Cyan

if ($DATABASE_OK) {
    Write-Host "✅ قاعدة البيانات: محفوظة دائماً (PostgreSQL)" -ForegroundColor Green
    Write-Host "🔒 البيانات آمنة ولن تُحذف" -ForegroundColor Green
} else {
    Write-Host "⚠️  قاعدة البيانات: مؤقتة (SQLite)" -ForegroundColor Yellow
    Write-Host "💥 البيانات ستُحذف عند إعادة التشغيل!" -ForegroundColor Red
    Write-Host "🔧 يجب إعداد قاعدة بيانات خارجية" -ForegroundColor Yellow
}

$port = if ($env:PORT) { $env:PORT } else { "5000" }
$flask_env = if ($env:FLASK_ENV) { $env:FLASK_ENV } else { "production" }

Write-Host "🌐 المنفذ: $port" -ForegroundColor Cyan
Write-Host "🔧 البيئة: $flask_env" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan

if (-not $DATABASE_OK) {
    Write-Host ""
    Write-Host ("🚨" * 20) -ForegroundColor Red
    Write-Host "تحذير مهم: البيانات ستُحذف عند إعادة التشغيل!" -ForegroundColor Red
    Write-Host "لحل هذه المشكلة، راجع ملف: QUICK_DATABASE_FIX.md" -ForegroundColor Yellow
    Write-Host ("🚨" * 20) -ForegroundColor Red
    Write-Host ""
    
    $continue = Read-Host "هل تريد المتابعة رغم ذلك؟ (y/n)"
    if ($continue -ne "y" -and $continue -ne "yes") {
        Write-Host "تم إلغاء التشغيل." -ForegroundColor Yellow
        exit 0
    }
}

Write-Host ""
Write-Host "🎯 التطبيق جاهز للتشغيل!" -ForegroundColor Green
Read-Host "اضغط Enter لبدء التشغيل"

Write-Host ""
Write-Host "🚀 بدء تشغيل التطبيق..." -ForegroundColor Green
Write-Host "⏳ يرجى الانتظار..." -ForegroundColor Yellow
Write-Host ""

# تشغيل التطبيق
try {
    if (Test-Path "final_working.py") {
        python final_working.py
    } elseif (Test-Path "app.py") {
        python app.py
    } else {
        Write-Host "❌ ملف التطبيق غير موجود!" -ForegroundColor Red
        Write-Host "تأكد من وجود final_working.py أو app.py" -ForegroundColor Yellow
        Read-Host "اضغط Enter للخروج"
        exit 1
    }
} catch {
    Write-Host ""
    Write-Host "❌ خطأ في تشغيل التطبيق: $($_.Exception.Message)" -ForegroundColor Red
} finally {
    Write-Host ""
    Write-Host "🛑 تم إيقاف التطبيق" -ForegroundColor Yellow
    Read-Host "اضغط Enter للخروج"
}
