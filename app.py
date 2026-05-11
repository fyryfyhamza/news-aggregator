from flask import Flask, render_template, request, jsonify
from db import connect_db
import pdfkit
import os
import platform
import shutil

app = Flask(__name__)

# --- إعدادات wkhtmltopdf الديناميكية ---
def get_pdf_config():
    if platform.system() == "Windows":
        path_wkhtmltopdf = r'D:\Lectuers\Semester 6\Intelligent Agent\project\books_scraper_project\programs\wkhtmltopdf\bin\wkhtmltopdf.exe'
        return pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
    else:
        # تأكد إن الأسطر اللي تحت دي مسبوقة بـ 8 مسافات بالظبط
        standard_path = '/usr/bin/wkhtmltopdf'
        if os.path.exists(standard_path):
            return pdfkit.configuration(wkhtmltopdf=standard_path)
        
        auto_path = shutil.which('wkhtmltopdf')
        if auto_path:
            return pdfkit.configuration(wkhtmltopdf=auto_path)
        
        return pdfkit.configuration(wkhtmltopdf='wkhtmltopdf')

# تشغيل الإعداد
try:
    config = get_pdf_config()
except:
    config = None

def generate_pdf_file(title, content, article_id):
    pdf_folder = os.path.join('static', 'pdfs')
    if not os.path.exists(pdf_folder):
        os.makedirs(pdf_folder)
    
    file_name = f"summary_{article_id}.pdf"
    file_path = os.path.join(pdf_folder, file_name)
    
    html_content = f"""
    <!DOCTYPE html>
    <html dir="rtl" lang="ar">
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: 'Arial', sans-serif; text-align: right; padding: 20px; }}
            h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
            p {{ font-size: 16px; line-height: 1.8; color: #34495e; }}
        </style>
    </head>
    <body>
        <h1>{title}</h1>
        <p>{content}</p>
    </body>
    </html>
    """
    
    options = {'encoding': "UTF-8", 'enable-local-file-access': None, 'quiet': ''}
    
    try:
        if config:
            pdfkit.from_string(html_content, file_path, configuration=config, options=options)
            return file_name
    except Exception as e:
        print(f"❌ PDF Error: {e}")
    return None

@app.route('/api/add_news', methods=['POST'])
def add_news_from_n8n():
    data = request.get_json()
    if not data: return jsonify({"status": "error"}), 400
    
    title = data.get('title')
    description = data.get('summary')
    category = data.get('category')
    url = data.get('link')

    db = connect_db()
    if not db: return jsonify({"status": "error"}), 500

    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT id FROM articles WHERE url = %s", (url,))
        if cursor.fetchone() is None:
            sql = "INSERT INTO articles (title, description, category, url, source_name) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(sql, (title, description, category, url, "AI Agent"))
            db.commit()
            
            article_id = cursor.lastrowid
            pdf_file = generate_pdf_file(title, description, article_id)
            
            if pdf_file:
                cursor.execute("UPDATE articles SET pdf_link = %s WHERE id = %s", (pdf_file, article_id))
                db.commit()
            return jsonify({"status": "success"}), 201
        return jsonify({"status": "exists"}), 200
    finally:
        db.close()

@app.route('/')
def index():
    db = connect_db()
    if not db: return "DB Error", 500
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM articles ORDER BY id DESC LIMIT 20")
    news = cursor.fetchall()
    db.close()
    return render_template('news_report.html', organized_news={'Latest': news})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 5000)))
