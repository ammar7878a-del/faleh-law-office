#!/usr/bin/env python3
"""
اختبار سريع لمشكلة الملفات
"""

from flask import Flask, url_for, send_from_directory
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'test-key'

# إعدادات الملفات
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    return '''
    <html dir="rtl">
    <head><title>اختبار الملفات</title></head>
    <body style="font-family: Arial; padding: 20px;">
        <h2>اختبار مشكلة الملفات</h2>
        <p><a href="/list_files">قائمة الملفات</a></p>
    </body>
    </html>
    '''

@app.route('/uploads/<path:filename>')
def serve_file(filename):
    """عرض الملفات"""
    try:
        print(f"🔍 طلب ملف: {filename}")
        upload_folder = app.config['UPLOAD_FOLDER']
        file_path = os.path.join(upload_folder, filename)
        
        if not os.path.exists(file_path):
            print(f"❌ الملف غير موجود: {file_path}")
            return f"الملف غير موجود: {filename}", 404
        
        print(f"✅ الملف موجود: {file_path}")
        return send_from_directory(upload_folder, filename)
        
    except Exception as e:
        print(f"❌ خطأ: {str(e)}")
        return f"خطأ: {str(e)}", 500

@app.route('/list_files')
def list_files():
    """قائمة بجميع الملفات"""
    try:
        upload_folder = app.config['UPLOAD_FOLDER']
        
        html = f'''
        <html dir="rtl">
        <head><title>قائمة الملفات</title></head>
        <body style="font-family: Arial; padding: 20px;">
            <h2>مجلد الرفع: {upload_folder}</h2>
            <p><strong>موجود:</strong> {'نعم' if os.path.exists(upload_folder) else 'لا'}</p>
        '''
        
        if os.path.exists(upload_folder):
            html += '<h3>الملفات:</h3><ul>'
            for item in os.listdir(upload_folder):
                item_path = os.path.join(upload_folder, item)
                if os.path.isfile(item_path):
                    size = os.path.getsize(item_path)
                    test_url = url_for('serve_file', filename=item)
                    html += f'<li><a href="{test_url}" target="_blank">{item}</a> ({size} bytes)</li>'
                else:
                    html += f'<li>{item}/ (مجلد)</li>'
            html += '</ul>'
        
        html += '''
            <p><a href="/">العودة</a></p>
        </body>
        </html>
        '''
        
        return html
        
    except Exception as e:
        return f"خطأ: {str(e)}"

if __name__ == '__main__':
    print("🚀 بدء تشغيل اختبار الملفات...")
    print(f"📁 مجلد الرفع: {UPLOAD_FOLDER}")
    print(f"📁 موجود: {os.path.exists(UPLOAD_FOLDER)}")
    
    if os.path.exists(UPLOAD_FOLDER):
        files = [f for f in os.listdir(UPLOAD_FOLDER) if os.path.isfile(os.path.join(UPLOAD_FOLDER, f))]
        print(f"📄 عدد الملفات: {len(files)}")
        if files:
            print("📄 أول 5 ملفات:")
            for f in files[:5]:
                print(f"   - {f}")
    
    print("✅ التطبيق جاهز على http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
