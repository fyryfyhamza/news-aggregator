import requests
import os
from dotenv import load_dotenv
from db import save_articles

load_dotenv()
API_KEY = '3848c9b06caa45b0974ac9a07a179f6e' # ضع مفتاحك هنا

def fetch_news_by_category(category_name, query):
    """
    Fetches news from the API based on a specific category query.
    """
    url = 'https://newsapi.org/v2/everything'
    params = {
        'q': query,
        'sortBy': 'publishedAt',
        'language': 'ar', # جلب الأخبار بالعربية لتطابق تقريرك
        'apiKey': API_KEY
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        if data.get('status') == 'ok':
            articles = data.get('articles', [])
            # Add the category label to each article
            for article in articles:
                article['category_label'] = category_name
            return articles
        return []
    except Exception as e:
        print(f"❌ Error fetching {category_name}: {e}")
        return []

def start_agent():
    # الأقسام المأخوذة من تقريرك المرفق
    news_categories = {
        'Wars & Conflicts': 'حرب OR نزاع OR عسكري OR طهران', # [cite: 3, 4]
        'Economy & Gold': 'الدولار OR الذهب OR النفط OR ليرة', # [cite: 13, 17, 18]
        'Sports': 'ميسي OR كأس العالم OR كرة قدم', # [cite: 31, 32, 35]
        'Technology': 'أوبو OR سيجا OR هاتف' # [cite: 14, 15]
    }
    
    for cat_name, q in news_categories.items():
        print(f"🔄 Agent is searching for: {cat_name}...")
        articles = fetch_news_by_category(cat_name, q)
        if articles:
            save_articles(articles)

if __name__ == "__main__":
    start_agent()