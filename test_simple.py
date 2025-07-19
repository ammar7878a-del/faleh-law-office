#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def index():
    return '''
    <html dir="rtl">
    <head>
        <title>اختبار بسيط</title>
        <meta charset="utf-8">
    </head>
    <body style="font-family: Arial; padding: 20px;">
        <h1>🚀 اختبار البرنامج</h1>
        <p>البرنامج يعمل بشكل صحيح!</p>
        <p>الوقت الحالي: <span id="time"></span></p>
        
        <script>
            document.getElementById('time').textContent = new Date().toLocaleString('ar-SA');
        </script>
    </body>
    </html>
    '''

if __name__ == '__main__':
    print("🚀 اختبار بسيط للبرنامج")
    print("📁 http://127.0.0.1:3080/")
    print("="*50)
    
    try:
        app.run(debug=True, host='127.0.0.1', port=3080)
    except Exception as e:
        print(f"❌ خطأ: {e}")
