#!/usr/bin/env python3
"""
Deployment script for Law Office Management System
"""

import os
import sys
import subprocess
import shutil
from datetime import datetime

def create_production_config():
    """Create production configuration"""
    print("📝 إنشاء إعدادات الإنتاج...")
    
    prod_env = """# Production Environment Variables
SECRET_KEY=your-super-secret-production-key-here
FLASK_APP=app.py
FLASK_ENV=production
DATABASE_URL=sqlite:///law_office_prod.db

# Mail Configuration for Production
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-production-email@gmail.com
MAIL_PASSWORD=your-production-app-password

# Security Settings
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_HTTPONLY=true
PERMANENT_SESSION_LIFETIME=3600
"""
    
    with open('.env.production', 'w', encoding='utf-8') as f:
        f.write(prod_env)
    
    print("✅ تم إنشاء ملف .env.production")

def create_wsgi_file():
    """Create WSGI file for production deployment"""
    print("📝 إنشاء ملف WSGI...")
    
    wsgi_content = """#!/usr/bin/env python3
import os
import sys

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

from app import create_app

# Create the application
application = create_app('production')

if __name__ == "__main__":
    application.run()
"""
    
    with open('wsgi.py', 'w', encoding='utf-8') as f:
        f.write(wsgi_content)
    
    print("✅ تم إنشاء ملف wsgi.py")

def create_nginx_config():
    """Create nginx configuration template"""
    print("📝 إنشاء قالب إعدادات Nginx...")
    
    nginx_config = """# Nginx configuration for Law Office Management System
server {
    listen 80;
    server_name your-domain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name your-domain.com;
    
    # SSL Configuration
    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    # Static files
    location /static {
        alias /path/to/your/app/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Upload files
    location /uploads {
        alias /path/to/your/app/uploads;
        expires 1y;
        add_header Cache-Control "private";
    }
    
    # Application
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # File upload size limit
    client_max_body_size 50M;
}
"""
    
    with open('nginx.conf.template', 'w', encoding='utf-8') as f:
        f.write(nginx_config)
    
    print("✅ تم إنشاء قالب nginx.conf.template")

def create_systemd_service():
    """Create systemd service file"""
    print("📝 إنشاء ملف خدمة systemd...")
    
    service_content = """[Unit]
Description=Law Office Management System
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/path/to/your/app
Environment=PATH=/path/to/your/venv/bin
ExecStart=/path/to/your/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:5000 wsgi:application
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
    
    with open('law-office.service', 'w', encoding='utf-8') as f:
        f.write(service_content)
    
    print("✅ تم إنشاء ملف law-office.service")

def create_backup_script():
    """Create backup script"""
    print("📝 إنشاء سكريبت النسخ الاحتياطي...")
    
    backup_script = """#!/bin/bash
# Backup script for Law Office Management System

# Configuration
APP_DIR="/path/to/your/app"
BACKUP_DIR="/path/to/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="law_office_backup_$DATE"

# Create backup directory
mkdir -p "$BACKUP_DIR/$BACKUP_NAME"

# Backup database
cp "$APP_DIR/law_office.db" "$BACKUP_DIR/$BACKUP_NAME/"

# Backup uploads
cp -r "$APP_DIR/uploads" "$BACKUP_DIR/$BACKUP_NAME/"

# Backup configuration
cp "$APP_DIR/.env" "$BACKUP_DIR/$BACKUP_NAME/"

# Create archive
cd "$BACKUP_DIR"
tar -czf "$BACKUP_NAME.tar.gz" "$BACKUP_NAME"
rm -rf "$BACKUP_NAME"

# Keep only last 30 backups
ls -t *.tar.gz | tail -n +31 | xargs -r rm

echo "Backup completed: $BACKUP_NAME.tar.gz"
"""
    
    with open('backup.sh', 'w', encoding='utf-8') as f:
        f.write(backup_script)
    
    # Make executable
    os.chmod('backup.sh', 0o755)
    
    print("✅ تم إنشاء سكريبت backup.sh")

def create_requirements_prod():
    """Create production requirements file"""
    print("📝 إنشاء متطلبات الإنتاج...")
    
    prod_requirements = """# Production requirements
Flask==2.3.3
Flask-SQLAlchemy==3.0.5
Flask-Login==0.6.3
Flask-WTF==1.1.1
Flask-Mail==0.9.1
Flask-Migrate==4.0.5
WTForms==3.0.1
Werkzeug==2.3.7
SQLAlchemy==2.0.21
python-dotenv==1.0.0
Pillow==10.0.1
reportlab==4.0.4
openpyxl==3.1.2
python-dateutil==2.8.2
email-validator==2.0.0
bcrypt==4.0.1

# Production server
gunicorn==21.2.0
psycopg2-binary==2.9.7  # For PostgreSQL
"""
    
    with open('requirements-prod.txt', 'w', encoding='utf-8') as f:
        f.write(prod_requirements)
    
    print("✅ تم إنشاء ملف requirements-prod.txt")

def create_deployment_guide():
    """Create deployment guide"""
    print("📝 إنشاء دليل النشر...")
    
    guide_content = """# دليل نشر نظام إدارة مكتب المحاماة

## متطلبات الخادم

- Ubuntu 20.04+ أو CentOS 8+
- Python 3.8+
- Nginx
- PostgreSQL (اختياري)

## خطوات النشر

### 1. إعداد الخادم
```bash
# تحديث النظام
sudo apt update && sudo apt upgrade -y

# تثبيت المتطلبات
sudo apt install python3 python3-pip python3-venv nginx postgresql postgresql-contrib
```

### 2. إعداد قاعدة البيانات (PostgreSQL)
```bash
sudo -u postgres createuser --interactive
sudo -u postgres createdb law_office
```

### 3. نشر التطبيق
```bash
# إنشاء مجلد التطبيق
sudo mkdir -p /var/www/law-office
cd /var/www/law-office

# نسخ ملفات التطبيق
# (نسخ جميع ملفات المشروع هنا)

# إنشاء البيئة الافتراضية
python3 -m venv venv
source venv/bin/activate

# تثبيت المتطلبات
pip install -r requirements-prod.txt

# إعداد قاعدة البيانات
python init_db.py
```

### 4. إعداد Nginx
```bash
# نسخ إعدادات Nginx
sudo cp nginx.conf.template /etc/nginx/sites-available/law-office
sudo ln -s /etc/nginx/sites-available/law-office /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 5. إعداد خدمة systemd
```bash
# نسخ ملف الخدمة
sudo cp law-office.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable law-office
sudo systemctl start law-office
```

### 6. إعداد النسخ الاحتياطي
```bash
# إضافة مهمة cron للنسخ الاحتياطي اليومي
echo "0 2 * * * /var/www/law-office/backup.sh" | sudo crontab -
```

## الأمان

### SSL/TLS
```bash
# تثبيت Let's Encrypt
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### جدار الحماية
```bash
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

## المراقبة

### فحص حالة الخدمة
```bash
sudo systemctl status law-office
sudo journalctl -u law-office -f
```

### فحص سجلات Nginx
```bash
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

## الصيانة

### تحديث التطبيق
```bash
cd /var/www/law-office
git pull origin main
source venv/bin/activate
pip install -r requirements-prod.txt
sudo systemctl restart law-office
```

### النسخ الاحتياطي اليدوي
```bash
./backup.sh
```

## استكشاف الأخطاء

### مشكلة: التطبيق لا يعمل
```bash
sudo systemctl status law-office
sudo journalctl -u law-office --no-pager
```

### مشكلة: خطأ في قاعدة البيانات
```bash
python test_app.py
```

### مشكلة: خطأ في Nginx
```bash
sudo nginx -t
sudo systemctl status nginx
```
"""
    
    with open('DEPLOYMENT.md', 'w', encoding='utf-8') as f:
        f.write(guide_content)
    
    print("✅ تم إنشاء دليل DEPLOYMENT.md")

def main():
    """Main deployment preparation function"""
    print("🚀 إعداد ملفات النشر...")
    print("=" * 50)
    
    try:
        create_production_config()
        create_wsgi_file()
        create_nginx_config()
        create_systemd_service()
        create_backup_script()
        create_requirements_prod()
        create_deployment_guide()
        
        print("\n✅ تم إنشاء جميع ملفات النشر بنجاح!")
        print("\nالملفات المُنشأة:")
        print("- .env.production (إعدادات الإنتاج)")
        print("- wsgi.py (ملف WSGI)")
        print("- nginx.conf.template (قالب Nginx)")
        print("- law-office.service (خدمة systemd)")
        print("- backup.sh (سكريبت النسخ الاحتياطي)")
        print("- requirements-prod.txt (متطلبات الإنتاج)")
        print("- DEPLOYMENT.md (دليل النشر)")
        
        print("\n📖 راجع ملف DEPLOYMENT.md للحصول على تعليمات النشر التفصيلية")
        
    except Exception as e:
        print(f"❌ خطأ في إعداد ملفات النشر: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
