#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, send_file
import os

app = Flask(__name__)

@app.route('/')
def index():
    # قائمة الملفات الموجودة فعلياً
    upload_folder = 'uploads'
    available_files = []

    if os.path.exists(upload_folder):
        for filename in os.listdir(upload_folder):
            if os.path.isfile(os.path.join(upload_folder, filename)):
                available_files.append(filename)

    links_html = ""
    for filename in available_files:
        links_html += f'<p><a href="/test_download/{filename}">📁 تحميل {filename}</a></p>'

    return f'''
    <html dir="rtl">
    <head>
        <title>اختبار التحميل</title>
        <meta charset="utf-8">
    </head>
    <body style="font-family: Arial; padding: 20px;">
        <h1>🔽 اختبار التحميل</h1>
        <h3>الملفات المتاحة:</h3>
        {links_html if links_html else '<p>❌ لا توجد ملفات في مجلد uploads</p>'}

        <hr>
        <h3>إنشاء ملفات اختبار:</h3>
        <p><a href="/create_test_files">🔧 إنشاء ملفات اختبار</a></p>
    </body>
    </html>
    '''

@app.route('/test_download/<filename>')
def test_download(filename):
    """تحميل اختبار مباشر"""
    try:
        upload_folder = 'uploads'
        file_path = os.path.join(upload_folder, filename)
        
        if not os.path.exists(file_path):
            return f"File not found: {filename}", 404
        
        return send_file(file_path, as_attachment=True, download_name=f"test_{filename}")
        
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/create_test_files')
def create_test_files():
    """إنشاء ملفات اختبار"""
    try:
        upload_folder = 'uploads'
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)

        # إنشاء ملف PNG اختبار
        png_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc\xf8\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00IEND\xaeB`\x82'
        with open(os.path.join(upload_folder, '20250717_175817_png'), 'wb') as f:
            f.write(png_content)

        # إنشاء ملف PDF اختبار
        pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n174\n%%EOF'
        with open(os.path.join(upload_folder, '20250717_175942_pdf'), 'wb') as f:
            f.write(pdf_content)

        return '''
        <html dir="rtl">
        <head>
            <title>تم إنشاء الملفات</title>
            <meta charset="utf-8">
        </head>
        <body style="font-family: Arial; padding: 20px;">
            <h1>✅ تم إنشاء ملفات الاختبار بنجاح</h1>
            <p><a href="/">🔙 العودة للصفحة الرئيسية</a></p>
        </body>
        </html>
        '''

    except Exception as e:
        return f"خطأ في إنشاء الملفات: {str(e)}", 500

if __name__ == '__main__':
    print("🚀 خادم اختبار التحميل")
    print("📁 http://127.0.0.1:3080/")
    app.run(debug=True, host='127.0.0.1', port=3080)
