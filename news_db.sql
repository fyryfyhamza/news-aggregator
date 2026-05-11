CREATE DATABASE IF NOT EXISTS news_aggregator_db;
USE news_aggregator_db;

CREATE TABLE IF NOT EXISTS articles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(500),
    source_name VARCHAR(100),
    description LONGTEXT, -- تم استبدال TEXT بـ LONGTEXT لضمان استيعاب ملخصات AI الطويلة
    category VARCHAR(100), -- عمود ضروري لعملية الفرز داخل الموقع
    url VARCHAR(750) UNIQUE,
    pdf_link VARCHAR(500), -- العمود الجديد لتخزين اسم ملف الـ PDF المولد
    published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);