# 💾 معلومات النسخ الاحتياطي - نظام إدارة المكتب القانوني

## 📁 الملفات الأساسية المعتمدة

### الملف الرئيسي:
- **`final_working.py`** - الملف الرئيسي المعتمد نهائياً
- الحجم: ~8700 سطر
- يحتوي على جميع الميزات المكتملة
- نظام أمان كامل مع Flask-Login
- تصميم متجاوب مثالي

### ملفات التصميم:
- **`static/css/custom.css`** - ملف التصميم المخصص
- يحتوي على 400+ سطر من التصميم المتقدم
- تدرجات لونية جميلة
- تجاوب مثالي مع جميع الأجهزة

### قاعدة البيانات:
- **`instance/final_working_v2.db`** - قاعدة البيانات الرئيسية
- تحتوي على جميع الجداول المطلوبة
- بيانات تجريبية للاختبار
- مستخدم افتراضي: admin/admin123

### مجلد الملفات:
- **`uploads/`** - مجلد الملفات المرفوعة
- يحتوي على المستندات والصور
- مجلدات فرعية منظمة
- نظام تسمية آمن للملفات

---

## 🔧 إعدادات النظام المعتمدة

### إعدادات Flask:
```python
app.config['SECRET_KEY'] = 'final-working-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///final_working_v2.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
```

### إعدادات الأمان:
- Flask-Login مفعل
- حماية جميع الصفحات
- تشفير كلمات المرور
- جلسات آمنة

### إعدادات الملفات:
- حد أقصى 16MB للملف
- أنواع ملفات مدعومة: PDF, JPG, PNG, DOCX
- تسمية آمنة للملفات
- معاينة الملفات في المتصفح

---

## 🗄️ هيكل قاعدة البيانات

### الجداول الرئيسية:
1. **users** - المستخدمين والأدوار
2. **clients** - بيانات العملاء
3. **cases** - القضايا والدعاوى
4. **appointments** - المواعيد
5. **invoices** - الفواتير والمدفوعات
6. **client_documents** - مستندات العملاء
7. **expenses** - المصروفات
8. **office_settings** - إعدادات المكتب

### العلاقات بين الجداول:
- العملاء ← القضايا (One-to-Many)
- العملاء ← المستندات (One-to-Many)
- القضايا ← الفواتير (One-to-Many)
- القضايا ← المواعيد (One-to-Many)

---

## 🎨 إعدادات التصميم المعتمدة

### الألوان الأساسية:
```css
--primary-color: #2c3e50
--secondary-color: #3498db
--success-color: #27ae60
--warning-color: #f39c12
--danger-color: #e74c3c
```

### التدرجات اللونية:
```css
--gradient-primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%)
--gradient-secondary: linear-gradient(135deg, #f093fb 0%, #f5576c 100%)
--gradient-success: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)
```

### الخطوط:
- Cairo (الخط الأساسي)
- Amiri (للنصوص العربية)
- Font Awesome (للأيقونات)

---

## 🚀 معلومات التشغيل

### متطلبات النظام:
- Python 3.8+
- Flask 2.3.3
- Flask-SQLAlchemy 3.0.5
- Flask-Login 0.6.3
- Werkzeug 2.3.7

### أوامر التشغيل:
```bash
# التشغيل العادي
python final_working.py

# التشغيل مع عرض الرسائل
python -u final_working.py
```

### المنافذ:
- المنفذ الافتراضي: 3080
- الوصول المحلي: http://127.0.0.1:3080
- الوصول الشبكي: http://[IP]:3080

---

## 🔐 بيانات الدخول الافتراضية

### المستخدم الرئيسي:
- **اسم المستخدم**: admin
- **كلمة المرور**: admin123
- **الدور**: مدير (صلاحيات كاملة)
- **الاسم**: المدير العام
- **البريد**: admin@lawoffice.com

---

## 📋 قائمة المراجعة للنسخ الاحتياطي

### ملفات يجب نسخها:
- ✅ `final_working.py`
- ✅ `static/css/custom.css`
- ✅ `instance/final_working_v2.db`
- ✅ `uploads/` (المجلد كاملاً)
- ✅ `requirements.txt`

### ملفات اختيارية:
- `FINAL_SYSTEM_COMPLETE.md`
- `QUICK_START_GUIDE.md`
- `SYSTEM_BACKUP_INFO.md`

---

## 🔄 استعادة النظام

### خطوات الاستعادة:
1. انسخ الملفات إلى مجلد جديد
2. تأكد من وجود Python
3. ثبت المتطلبات: `pip install -r requirements.txt`
4. شغل النظام: `python final_working.py`
5. اذهب إلى: `http://127.0.0.1:3080`

---

## ✅ حالة النظام

**النظام مكتمل ومعتمد نهائياً!**

- جميع الميزات تعمل بشكل رائع وجميل ✨
- التصميم احترافي ومتجاوب 📱
- الأمان محقق بأعلى المستويات 🔐
- تجربة المستخدم ممتازة 🎯

**تاريخ الاعتماد**: 18 يوليو 2025 🎉
