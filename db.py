import mysql.connector

def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="news_aggregator_db"
    )

def save_articles(articles):
    db = connect_db()
    cursor = db.cursor()
    
    query = """
    INSERT IGNORE INTO articles (title, source_name, description, url, category, published_at)
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    
    count = 0
    for article in articles:
        data = (
            article.get('title'),
            article.get('source', {}).get('name'),
            article.get('description'),
            article.get('url'),
            article.get('category_label'), # تخزين القسم هنا
            article.get('publishedAt')
        )
        cursor.execute(query, data)
        if cursor.rowcount > 0:
            count += 1
            
    db.commit()
    cursor.close()
    db.close()
    print(f"✅ Saved {count} articles in this category.")
