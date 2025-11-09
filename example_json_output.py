#!/usr/bin/env python3
"""
Contoh Custom JSON Output
Menunjukkan berbagai format JSON yang bisa dibuat
"""

import json
from datetime import datetime

# Contoh data yang sudah di-scrape
scraped_data = [
    {
        "title": "Stock market today: Sensex gains 500 points, Nifty above 19,800",
        "url": "https://www.moneycontrol.com/news/business/markets/stock-market-today-123",
        "date": "December 15, 2024",
        "summary": "Indian stock market extended gains on Friday...",
        "image_url": "https://images.moneycontrol.com/static-mcnews/2024/12/stocks.jpg",
        "author": "MC Research",
        "scraped_at": "2024-12-15T10:30:00.123456"
    },
    {
        "title": "FII buying pushes markets higher; Nifty IT up 2%",
        "url": "https://www.moneycontrol.com/news/business/markets/fii-buying-124",
        "date": "December 15, 2024",
        "summary": "Foreign institutional investors continued their buying...",
        "image_url": "https://images.moneycontrol.com/static-mcnews/2024/12/market.jpg",
        "author": "Kshitij Anand",
        "scraped_at": "2024-12-15T10:30:01.234567"
    },
    {
        "title": "Top 10 stocks to watch on December 15, 2024",
        "url": "https://www.moneycontrol.com/news/business/markets/top-stocks-125",
        "date": "December 15, 2024",
        "summary": "Here are the top stocks that are likely to be in focus...",
        "image_url": "https://images.moneycontrol.com/static-mcnews/2024/12/focus.jpg",
        "author": "Sunil Shankar Matkar",
        "scraped_at": "2024-12-15T10:30:02.345678"
    }
]


# ============================================================
# FORMAT 1: JSON Standar (Default)
# ============================================================
def save_json_standard(data, filename='output_standard.json'):
    """Format JSON standar dengan pretty print"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ Saved standard JSON to {filename}")


# ============================================================
# FORMAT 2: JSON Compact (Tanpa Indentasi)
# ============================================================
def save_json_compact(data, filename='output_compact.json'):
    """Format JSON compact untuk menghemat space"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
    print(f"✅ Saved compact JSON to {filename}")


# ============================================================
# FORMAT 3: JSON dengan Metadata
# ============================================================
def save_json_with_metadata(data, filename='output_with_metadata.json'):
    """Format JSON dengan metadata tambahan"""
    output = {
        "metadata": {
            "source": "Moneycontrol Markets",
            "scraped_at": datetime.now().isoformat(),
            "total_articles": len(data),
            "scraper_version": "1.0.0"
        },
        "articles": data
    }
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"✅ Saved JSON with metadata to {filename}")


# ============================================================
# FORMAT 4: JSON Grouped by Date
# ============================================================
def save_json_grouped_by_date(data, filename='output_grouped.json'):
    """Group articles by date"""
    grouped = {}
    for article in data:
        date = article.get('date', 'Unknown')
        if date not in grouped:
            grouped[date] = []
        grouped[date].append(article)

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(grouped, f, ensure_ascii=False, indent=2)
    print(f"✅ Saved grouped JSON to {filename}")


# ============================================================
# FORMAT 5: JSONL (JSON Lines) - Satu JSON per baris
# ============================================================
def save_jsonl(data, filename='output.jsonl'):
    """Format JSONL - berguna untuk big data processing"""
    with open(filename, 'w', encoding='utf-8') as f:
        for item in data:
            json.dump(item, f, ensure_ascii=False)
            f.write('\n')
    print(f"✅ Saved JSONL to {filename}")


# ============================================================
# FORMAT 6: JSON dengan Custom Fields
# ============================================================
def save_json_custom_fields(data, filename='output_custom.json'):
    """Extract hanya field tertentu"""
    # Hanya ambil field yang diinginkan
    simplified = [
        {
            "title": article["title"],
            "link": article["url"],
            "published": article["date"]
        }
        for article in data
    ]

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(simplified, f, ensure_ascii=False, indent=2)
    print(f"✅ Saved custom fields JSON to {filename}")


# ============================================================
# FORMAT 7: Pretty Print ke Console
# ============================================================
def print_json_pretty(data, limit=2):
    """Print JSON ke console dengan format rapi"""
    print("\n" + "="*60)
    print(f"Preview {limit} articles:")
    print("="*60)
    print(json.dumps(data[:limit], ensure_ascii=False, indent=2))


# ============================================================
# FORMAT 8: JSON untuk API Response Format
# ============================================================
def save_json_api_format(data, filename='output_api_format.json'):
    """Format seperti API response"""
    output = {
        "status": "success",
        "count": len(data),
        "data": data,
        "timestamp": datetime.now().isoformat()
    }
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"✅ Saved API format JSON to {filename}")


# ============================================================
# Jalankan semua contoh
# ============================================================
if __name__ == "__main__":
    print("\n🎯 Demonstrasi Berbagai Format JSON Output\n")

    # 1. Standard JSON
    save_json_standard(scraped_data)

    # 2. Compact JSON
    save_json_compact(scraped_data)

    # 3. JSON with Metadata
    save_json_with_metadata(scraped_data)

    # 4. Grouped JSON
    save_json_grouped_by_date(scraped_data)

    # 5. JSONL
    save_jsonl(scraped_data)

    # 6. Custom Fields
    save_json_custom_fields(scraped_data)

    # 7. Print to Console
    print_json_pretty(scraped_data, limit=1)

    # 8. API Format
    save_json_api_format(scraped_data)

    print("\n" + "="*60)
    print("✅ Semua format JSON berhasil dibuat!")
    print("="*60)
    print("\nFile yang dibuat:")
    print("  - output_standard.json (default format)")
    print("  - output_compact.json (hemat space)")
    print("  - output_with_metadata.json (dengan info tambahan)")
    print("  - output_grouped.json (grouped by date)")
    print("  - output.jsonl (JSON Lines format)")
    print("  - output_custom.json (custom fields)")
    print("  - output_api_format.json (API response format)")
    print()
