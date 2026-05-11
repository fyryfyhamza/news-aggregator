from flask import Flask, render_template, request, jsonify
from db import connect_db
import pdfkit
import os
import platform
import shutil

app = Flask(__name__)

# --- إعدادات wkhtmltopdf الديناميكية الذكية ---
if platform.system() == "Windows":
    # المسار الخاص بجهازك أثناء التطوير
    path_wkhtmltopdf = r'D:\Lectuers\Semester 6\Intelligent Agent\project\books_scraper_project\programs\wkhtmltopdf\bin\wkhtmltopdf.exe'
    config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
else:
    # البحث عن المسار تلقائياً في سيرفر Railway (Linux)
    path_to_wkhtmltopdf = shutil.which('wkhtmltopdf')
    if path_to_wkhtmltopdf:
        config = pdfkit.configuration(wkhtmltopdf=path_to_wkhtmltopdf)
    else:
        config = pdfkit.configuration()

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
            .footer {{ color: #7f8c8d; font-size: 12px; margin-top: 50px; border-top: 1px solid #eee; padding-top: 10px; }}
        </style>
    </head>
    <body>
        <h1>{title}</h1>
        <p>{content}</p>
        <div class="footer">مصدر الخبر: Intelligence OS Ecosystem</div>
    </body>
    </html>
    """
    
    options = {'encoding': "UTF-8", 'enable-local-file-access': None, 'quiet': ''}
    
    try:
        pdfkit.from_string(html_content, file_path, configuration=config, options=options)
        return file_name
    except Exception as e:
        print(f"❌ PDF Generation Error: {e}")
        return None

@app.route('/api/add_news', methods=['POST'])
def add_news_from_n8n():
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "No data received"}), 400
    
    title = data.get('title')
    description = data.get('summary')
    category = data.get('category')
    url = data.get('link') # الرابط الأصلي للخبر (Bonus)
    source = "AI News Agent"

    db = connect_db()
    if not db:
        return jsonify({"status": "error", "message": "Database connection failed"}), 500

    try:
        cursor = db.cursor(dictionary=True)
        # التأكد من عدم تكرار الخبر
        cursor.execute("SELECT id FROM articles WHERE url = %s", (url,))
        if cursor.fetchone() is None:
            sql = "INSERT INTO articles (title, description, category, url, source_name) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(sql, (title, description, category, url, source))
            db.commit()
            
            article_id = cursor.lastrowid
            pdf_file = generate_pdf_file(title, description, article_id)
            
            if pdf_file:
                cursor.execute("UPDATE articles SET pdf_link = %s WHERE id = %s", (pdf_file, article_id))
                db.commit()
            
            return jsonify({"status": "success", "id": article_id}), 201
        
        return jsonify({"status": "exists"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        db.close()

@app.route('/')
def index():
    search_query = request.args.get('search', '')
    db = connect_db()
    cursor = db.cursor(dictionary=True)
    categories = ['Wars & Conflicts', 'Economy & Gold', 'Sports', 'Technology']
    organized_news = {}

    try:
        for cat in categories:
            if search_query:
                query = "SELECT * FROM articles WHERE category = %s AND (title LIKE %s OR description LIKE %s) ORDER BY id DESC"
                param = f"%{search_query}%"
                cursor.execute(query, (cat, param, param))
            else:
                query = "SELECT * FROM articles WHERE category = %s ORDER BY id DESC LIMIT 6"
                cursor.execute(query, (cat,))
            organized_news[cat] = cursor.fetchall()
    finally:
        db.close()
    
    return render_template('news_report.html', organized_news=organized_news, search_query=search_query)

@app.route('/automation')
def automation():
    n8n_url = "https://hamzayassen.app.n8n.cloud/" 
    return render_template('automation.html', n8n_url=n8n_url)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.getenv("PORT", 5000)))
