# 🏢 نظام إدارة مكتب فالح آل عيسى للمحاماة

نظام شامل لإدارة مكاتب المحاماة مع واجهة عربية حديثة وميزات متقدمة.

## ✨ الميزات الرئيسية

- 📋 **إدارة القضايا**: تتبع شامل للقضايا والمرافعات
- 👥 **إدارة العملاء**: قاعدة بيانات متكاملة للعملاء
- 📅 **نظام المواعيد**: جدولة وتذكير بالمواعيد
- 💰 **الإدارة المالية**: تتبع الأتعاب والمصروفات
- 📄 **إدارة الوثائق**: رفع وتنظيم المستندات
- 📊 **التقارير**: تقارير مالية وإحصائية شاملة
- 🔐 **نظام الأمان**: تسجيل دخول آمن وإدارة الصلاحيات
- 🌐 **واجهة عربية**: دعم كامل للغة العربية

## 🚀 النشر على Render.com

### المتطلبات الأساسية
- حساب على [Render.com](https://render.com)
- حساب GitHub لرفع الكود
- قاعدة بيانات PostgreSQL (مجانية على Render)

### خطوات النشر

#### 1. إعداد المشروع على GitHub
```bash
# إنشاء مستودع Git جديد
git init
git add .
git commit -m "Initial commit - Faleh Law Office System"

# ربط بـ GitHub (استبدل YOUR_USERNAME بمعرفك)
git remote add origin https://github.com/YOUR_USERNAME/faleh-law-office.git
git branch -M main
git push -u origin main
```

#### 2. إنشاء قاعدة البيانات على Render
1. اذهب إلى [Render Dashboard](https://dashboard.render.com)
2. انقر على "New" → "PostgreSQL"
3. املأ البيانات:
   - **Name**: `faleh-postgres`
   - **Database**: `faleh_db`
   - **User**: `faleh_user`
   - **Plan**: Free
4. انقر "Create Database"
5. احفظ رابط الاتصال (Connection String)

#### 3. إنشاء Web Service
1. في Render Dashboard، انقر "New" → "Web Service"
2. اربط مستودع GitHub الخاص بك
3. املأ الإعدادات:
   - **Name**: `faleh-law-office`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn --bind 0.0.0.0:$PORT final_working:app`

#### 4. إعداد متغيرات البيئة
في إعدادات Web Service، أضف:
```
DATABASE_URL=postgresql://faleh_user:PASSWORD@HOST:5432/faleh_db
SECRET_KEY=your-secret-key-here
FLASK_ENV=production
```

#### 5. النشر
- انقر "Create Web Service"
- انتظر اكتمال عملية البناء والنشر
- ستحصل على رابط التطبيق: `https://faleh-law-office.onrender.com`

## 🔧 التشغيل المحلي

### المتطلبات
- Python 3.8+
- pip

### خطوات التشغيل
```bash
# تثبيت المتطلبات
pip install -r requirements.txt

# تشغيل التطبيق
python final_working.py
```

التطبيق سيعمل على: http://127.0.0.1:10000

### بيانات الدخول الافتراضية
- **اسم المستخدم**: admin
- **كلمة المرور**: admin123

## 📁 هيكل المشروع

```
faleh/
├── final_working.py      # الملف الرئيسي للتطبيق
├── requirements.txt      # متطلبات Python
├── render.yaml          # إعدادات Render
├── .gitignore          # ملفات مستبعدة من Git
├── uploads/            # ملفات مرفوعة
├── backups/            # نسخ احتياطية
└── instance/           # قاعدة بيانات محلية
```

## 🔒 الأمان

- تشفير كلمات المرور
- جلسات آمنة
- حماية من CSRF
- تحديد صلاحيات المستخدمين
- نسخ احتياطية تلقائية

## 📊 قاعدة البيانات

### الجداول الرئيسية
- `user` - المستخدمين
- `client` - العملاء
- `case` - القضايا
- `appointment` - المواعيد
- `expense` - المصروفات
- `client_document` - الوثائق
- `office_settings` - إعدادات المكتب

## 🛠️ التخصيص

### تغيير اسم المكتب
1. اذهب إلى "إعدادات المكتب" في التطبيق
2. أو عدّل في `OfficeSettings` في الكود

### إضافة ميزات جديدة
- أضف النماذج في قسم Models
- أنشئ الـ Routes المطلوبة
- صمم الـ Templates

## 📞 الدعم الفني

للمساعدة والدعم:
- 📧 البريد الإلكتروني: support@falehlaw.com
- 📱 الهاتف: +966501234567

## 📄 الترخيص

هذا المشروع محمي بحقوق الطبع والنشر © 2025 مكتب فالح آل عيسى للمحاماة

---

**تم تطوير هذا النظام خصيصاً لمكاتب المحاماة العربية** 🇸🇦
