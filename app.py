from flask import Flask, render_template, request, jsonify
from db import connect_db
import pdfkit
import os
import platform

app = Flask(__name__)

# --- إعدادات wkhtmltopdf الديناميكية ---
if platform.system() == "Windows":
    # المسار الخاص بجهازك أثناء التطوير
    path_wkhtmltopdf = r'D:\Lectuers\Semester 6\Intelligent Agent\project\books_scraper_project\programs\wkhtmltopdf\bin\wkhtmltopdf.exe'
    config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
else:
    # يجب أن يكون هناك 4 مسافات (أو Tab) قبل السطر التالي
    config = pdfkit.configuration()
def generate_pdf_file(title, content, article_id):
    pdf_folder = os.path.join('static', 'pdfs')
    if not os.path.exists(pdf_folder):
        os.makedirs(pdf_folder)
    
    file_name = f"summary_{article_id}.pdf"
    file_path = os.path.join(pdf_folder, file_name)
    
    # تحسين التنسيق ليدعم العربية بشكل أفضل في السيرفرات
    html_content = f"""
    <!DOCTYPE html>
    <html dir="rtl" lang="ar">
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: 'Arial', sans-serif; text-align: right; padding: 20px; }}
            h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; pb: 10px; }}
            p {{ font-size: 16px; line-height: 1.8; color: #34495e; }}
            .footer {{ color: #7f8c8d; font-size: 12px; margin-top: 50px; border-top: 1px solid #eee; pt: 10px; }}
        </style>
    </head>
    <body>
        <h1>{title}</h1>
        <p>{content}</p>
        <div class="footer">مصدر الخبر: Intelligence OS Ecosystem</div>
    </body>
    </html>
    """
    
    options = {
        'encoding': "UTF-8",
        'enable-local-file-access': None,
        'quiet': '',
        'margin-top': '0.75in',
        'margin-right': '0.75in',
        'margin-bottom': '0.75in',
        'margin-left': '0.75in',
    }
    
    try:
        pdfkit.from_string(html_content, file_path, configuration=config, options=options)
        return file_name
    except Exception as e:
        print(f"Error generating PDF: {e}")
        return None

def get_news_by_categories(search_query=None):
    db = connect_db()
    cursor = db.cursor(dictionary=True)
    categories = ['Wars & Conflicts', 'Economy & Gold', 'Sports', 'Technology']
    organized_news = {}

    try:
        for cat in categories:
            if search_query:
                query = """
                    SELECT * FROM articles 
                    WHERE category = %s AND (title LIKE %s OR description LIKE %s) 
                    ORDER BY id DESC
                """
                search_param = f"%{search_query}%"
                cursor.execute(query, (cat, search_param, search_param))
            else:
                query = "SELECT * FROM articles WHERE category = %s ORDER BY id DESC LIMIT 6"
                cursor.execute(query, (cat,))
            
            organized_news[cat] = cursor.fetchall()
    finally:
        cursor.close()
        db.close()
    return organized_news

@app.route('/api/add_news', methods=['POST'])
def add_news_from_n8n():
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "No data received"}), 400
    
    title = data.get('title')
    description = data.get('summary')
    category = data.get('category')
    url = data.get('link')
    source = "AI News Agent"

    db = None
    try:
        db = connect_db()
        cursor = db.cursor()
        
        # التأكد من عدم تكرار الرابط
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
        if db:
            db.close()

@app.route('/')
def index():
    search_query = request.args.get('search', '')
    news_data = get_news_by_categories(search_query)
    return render_template('news_report.html', organized_news=news_data, search_query=search_query)

# إضافة Route لصفحة الأتمتة للربط مع n8n
@app.route('/automation')
def automation():
    # استبدل هذا بالـ URL الخاص بـ n8n على السيرفر
    n8n_url = "https://hamzayassen.app.n8n.cloud/" 
    return render_template('automation.html', n8n_url=n8n_url)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
