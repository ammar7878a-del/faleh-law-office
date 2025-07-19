#!/usr/bin/env python3
"""
اختبار مشكلة الملفات العربية
"""

from flask import Flask, url_for, send_from_directory
import os
import urllib.parse

app = Flask(__name__)
app.config['SECRET_KEY'] = 'test-key'

# إعدادات الملفات
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    return '''
    <html dir="rtl">
    <head><title>اختبار الملفات العربية</title></head>
    <body style="font-family: Arial; padding: 20px;">
        <h2>اختبار مشكلة الملفات العربية</h2>
        <p><a href="/test_problematic_url">اختبار الرابط المشكل</a></p>
        <p><a href="/list_files">قائمة الملفات</a></p>
    </body>
    </html>
    '''

@app.route('/test_problematic_url')
def test_problematic_url():
    """اختبار الرابط المشكل من الـ logs"""
    
    # الرابط المشكل من الـ logs
    problematic_filename = "20250719_170506_%D8%A7%D9%82%D8%A7%D9%85%D8%A9_%D8%AF%D8%B9%D9%88%D9%89_%D8%B9%D9%84%D9%89_%D8%B9%D9%85%D9%8A%D9%84_client/2"
    
    # فك الترميز
    try:
        decoded = urllib.parse.unquote(problematic_filename, encoding='utf-8')
    except:
        decoded = "فشل في فك الترميز"
    
    # إنشاء رابط اختبار
    test_url = url_for('serve_file', filename=problematic_filename)
    
    return f'''
    <html dir="rtl">
    <head><title>اختبار الرابط المشكل</title></head>
    <body style="font-family: Arial; padding: 20px;">
        <h2>تحليل الرابط المشكل</h2>
        <p><strong>الرابط الأصلي:</strong> {problematic_filename}</p>
        <p><strong>بعد فك الترميز:</strong> {decoded}</p>
        <p><strong>رابط الاختبار:</strong> <a href="{test_url}" target="_blank">{test_url}</a></p>
        
        <hr>
        <h3>تحليل المشكلة:</h3>
        <p>المشكلة واضحة: الرابط يحتوي على "client/2" في النهاية</p>
        <p>هذا يعني أن هناك خطأ في إنشاء الرابط في التطبيق الأصلي</p>
        
        <p><a href="/">العودة</a></p>
    </body>
    </html>
    '''

@app.route('/uploads/<path:filename>')
def serve_file(filename):
    """عرض الملفات"""
    try:
        print(f"🔍 طلب ملف: {filename}")
        
        # فك ترميز اسم الملف
        try:
            decoded_filename = urllib.parse.unquote(filename, encoding='utf-8')
            print(f"📝 بعد فك الترميز: {decoded_filename}")
        except Exception as e:
            print(f"❌ خطأ في فك الترميز: {e}")
            decoded_filename = filename
        
        # التحقق من وجود "client/" في الرابط
        if "client/" in filename:
            print(f"⚠️ تم اكتشاف 'client/' في الرابط: {filename}")
            # محاولة إزالة الجزء الخاطئ
            clean_filename = filename.split("client/")[0].rstrip("_")
            print(f"🧹 اسم الملف بعد التنظيف: {clean_filename}")
            filename = clean_filename
        
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
    print("🚀 بدء تشغيل اختبار الملفات العربية...")
    print(f"📁 مجلد الرفع: {UPLOAD_FOLDER}")
    print(f"📁 موجود: {os.path.exists(UPLOAD_FOLDER)}")
    
    print("✅ التطبيق جاهز على http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
