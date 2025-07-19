Write-Host "========================================" -ForegroundColor Green
Write-Host "    نظام إدارة المكتب القانوني" -ForegroundColor Yellow
Write-Host "    Law Office Management System" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "✅ تم إصلاح خطأ قاعدة البيانات بنجاح!" -ForegroundColor Green
Write-Host "✅ Database error has been fixed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "🚀 بدء التطبيق..." -ForegroundColor Cyan
Write-Host "🚀 Starting application..." -ForegroundColor Cyan
Write-Host ""
Write-Host "🌐 المتصفح: http://127.0.0.1:8080" -ForegroundColor Blue
Write-Host "🌐 Browser: http://127.0.0.1:8080" -ForegroundColor Blue
Write-Host ""
Write-Host "👤 المستخدم: admin" -ForegroundColor Magenta
Write-Host "🔑 كلمة المرور: admin123" -ForegroundColor Magenta
Write-Host "👤 Username: admin" -ForegroundColor Magenta
Write-Host "🔑 Password: admin123" -ForegroundColor Magenta
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Start the application
python final_working.py

Write-Host ""
Write-Host "اضغط أي مفتاح للخروج..." -ForegroundColor Yellow
Write-Host "Press any key to exit..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
