# Moneycontrol News Scraper

Web scraper untuk mengekstrak berita dari Moneycontrol.com bagian Markets (https://www.moneycontrol.com/news/business/markets/)

## 📁 Struktur Project

```
portofolio-scraper/
├── scrapers/                    # Core scraper modules
│   ├── __init__.py
│   ├── crawl4ai_scraper.py      # Scraper dengan Crawl4AI (RECOMMENDED)
│   ├── playwright_scraper.py    # Scraper dengan Playwright
│   ├── requests_scraper.py      # Scraper dengan Requests (basic)
│   └── auto_pages_scraper.py    # Enhanced scraper dengan auto-detect pages
├── examples/                    # Example & template scripts
│   ├── custom_scraper.py        # Template untuk custom website
│   └── json_output_examples.py  # Contoh berbagai format JSON output
├── docs/                        # Documentation
│   ├── SCRAPING_GUIDE.md        # Panduan lengkap web scraping
│   └── ERROR_HANDLING_GUIDE.md  # Troubleshooting & error handling
├── run_crawl4ai.py             # Quick run script (Crawl4AI)
├── run_playwright.py           # Quick run script (Playwright)
├── run_requests.py             # Quick run script (Requests)
├── upload_to_mongodb.py        # Upload JSON data ke MongoDB
├── config.py                   # Konfigurasi settings
├── requirements.txt            # Dependencies
├── .env.example                # Contoh konfigurasi environment variables
├── README.md                   # Dokumentasi utama
└── .gitignore                  # Git ignore rules
```

## ✨ Fitur

- ✅ **3 Mode Scraper**: Crawl4AI (powerful), Playwright (reliable), Requests (simple)
- ✅ **Auto Page Detection**: Otomatis detect total pages yang tersedia
- ✅ **Detail Extraction**: Fetch date & author dari detail page
- ✅ **Concurrency Control**: Limit concurrent requests untuk stabilitas
- ✅ **Error Handling**: Retry mechanism dengan exponential backoff
- ✅ **Multiple Export**: JSON, CSV, dan Excel
- ✅ **MongoDB Integration**: Upload otomatis ke MongoDB dengan deduplication
- ✅ **Comprehensive Logging**: Track semua aktivitas scraping

## 🚀 Quick Start

### 1. Clone & Setup

```bash
git clone <repository-url>
cd portofolio-scraper
```

### 2. Install Dependencies

```bash
# Buat virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# atau
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers (untuk Crawl4AI & Playwright)
playwright install chromium
```

### 3. Run Scraper

**Option 1: Crawl4AI (RECOMMENDED 🚀)**
```bash
python run_crawl4ai.py
```

**Option 2: Playwright**
```bash
python run_playwright.py
```

**Option 3: Requests (Simple)**
```bash
python run_requests.py
```

## 📊 Output

Scraper akan menghasilkan:
```
moneycontrol_news_crawl4ai.json    # Data dalam format JSON
moneycontrol_news_crawl4ai.csv     # Data dalam format CSV
scraper_crawl4ai.log               # Log file untuk debugging
```

### Contoh Output JSON

```json
[
  {
    "title": "Powell says tariffs adding some pressure to inflation...",
    "url": "https://www.moneycontrol.com/news/business/markets/...",
    "summary": "Federal Reserve Chair Jerome Powell said tariffs...",
    "image_url": "https://images.moneycontrol.com/...",
    "date": "November 07, 2025",
    "author": "Moneycontrol News",
    "scraped_at": "2025-11-07T08:30:00.123456"
  }
]
```

## 💾 Upload ke MongoDB

Upload hasil scraping ke MongoDB dengan mudah:

### Setup

```bash
# Install pymongo (sudah ada di requirements.txt)
pip install pymongo

# Copy .env.example ke .env
cp .env.example .env

# Edit .env dan isi dengan MongoDB credentials Anda
nano .env  # atau text editor lainnya
```

### Konfigurasi

Edit `.env` file:

```bash
MONGODB_CONNECTION_STRING=mongodb://localhost:27017/
MONGODB_DATABASE_NAME=moneycontrol_db
MONGODB_COLLECTION_NAME=news_articles
```

Atau edit langsung di `upload_to_mongodb.py`:

```python
MONGODB_CONNECTION_STRING = "mongodb://localhost:27017/"
DATABASE_NAME = "moneycontrol_db"
COLLECTION_NAME = "news_articles"
```

### Upload Data

```bash
python upload_to_mongodb.py
```

**Fitur Upload:**
- Auto-deduplication berdasarkan URL
- Upsert mode (update existing + insert new)
- Bulk operations untuk performa tinggi
- Progress tracking & logging
- Error handling yang robust
- Auto-indexing untuk query performance

## 🎛️ Konfigurasi

Edit `config.py` untuk customize:

```python
NUM_PAGES = 3              # Jumlah halaman yang akan di-scrape
DELAY_BETWEEN_PAGES = 2.0  # Delay antar page (detik)
OUTPUT_JSON = True         # Export ke JSON
OUTPUT_CSV = True          # Export ke CSV
```

Atau configure di code:

```python
from scrapers import MoneyControlCrawl4AIScraper

# Custom configuration
scraper = MoneyControlCrawl4AIScraper(
    fetch_details=True,      # Fetch date & author dari detail page
    max_concurrent=5         # Max 5 concurrent requests (adjust sesuai network)
)

# Scrape dengan custom settings
articles = await scraper.scrape_multiple_pages(
    num_pages=5,            # Scrape 5 pages
    delay=2.0               # 2 detik delay antar page
)
```

## 📚 Mode Scraper

### 🚀 **Crawl4AI Scraper** (RECOMMENDED)

**Keunggulan:**
- Built khusus untuk AI/LLM extraction
- Otomatis handle JavaScript
- Async untuk performa tinggi
- Smart content extraction
- **Concurrency control** untuk stabilitas

**Penggunaan:**
```bash
python run_crawl4ai.py
```

**Konfigurasi:**
```python
scraper = MoneyControlCrawl4AIScraper(
    fetch_details=True,     # Fetch dari detail page
    max_concurrent=5        # Limit concurrent requests
)
```

---

### 🎭 **Playwright Scraper**

**Keunggulan:**
- Full browser automation
- Reliable dan stabil
- Async/await support
- Debugging yang mudah

**Penggunaan:**
```bash
python run_playwright.py
```

---

### 📡 **Requests Scraper** (Basic)

**Keunggulan:**
- Paling ringan dan cepat
- Tidak perlu browser
- Cocok untuk static content

**Penggunaan:**
```bash
python run_requests.py
```

---

## 🔧 Troubleshooting

### Error: Timeout

Jika sering terjadi timeout:

```python
# Kurangi concurrent requests
scraper = MoneyControlCrawl4AIScraper(max_concurrent=3)

# Tambah delay antar page
articles = await scraper.scrape_multiple_pages(num_pages=3, delay=3.0)
```

Baca: `docs/ERROR_HANDLING_GUIDE.md`

### Error: UnicodeEncodeError (Windows)

Sudah diperbaiki! Emoji diganti dengan text labels.

### Error: Playwright browser tidak tersedia

```bash
playwright install chromium
```

### Error: Module not found

```bash
pip install -r requirements.txt --upgrade
```

---

## 📖 Dokumentasi Lengkap

- **`docs/SCRAPING_GUIDE.md`** - Panduan lengkap web scraping
  - Konsep dasar & flow
  - Cara inspect element
  - CSS selector cheat sheet
  - Template code berbagai use case
  - Debugging tips

- **`docs/ERROR_HANDLING_GUIDE.md`** - Troubleshooting guide
  - Root cause analysis
  - Concurrency limiting
  - Retry mechanism
  - Configuration options

## 🎓 Examples

### Custom Scraper untuk Website Lain

```bash
python examples/custom_scraper.py
```

Template yang bisa di-customize untuk scrape website apapun.

### Berbagai Format JSON Output

```bash
python examples/json_output_examples.py
```

Generate 8 format JSON berbeda:
- Standard (default)
- Compact (space-efficient)
- With metadata
- Grouped by date
- JSONL (JSON Lines)
- Custom fields
- API format

---

## 🛠️ Development

### Struktur Data

Setiap artikel memiliki field:

| Field | Deskripsi | Source |
|-------|-----------|--------|
| `title` | Judul berita | List page |
| `url` | Link artikel lengkap | List page |
| `summary` | Ringkasan/excerpt | List page |
| `image_url` | URL gambar thumbnail | List page |
| `date` | Tanggal publikasi | Detail page |
| `author` | Nama penulis | Detail page |
| `scraped_at` | Timestamp scraping | Generated |

### Import Sebagai Module

```python
from scrapers import MoneyControlCrawl4AIScraper

# Initialize
scraper = MoneyControlCrawl4AIScraper(
    fetch_details=True,
    max_concurrent=5
)

# Scrape
articles = await scraper.scrape_multiple_pages(num_pages=3)

# Save
scraper.save_to_json(articles, 'my_output.json')
scraper.save_to_csv(articles, 'my_output.csv')
```

### Menambah Field Baru

Edit fungsi `extract_article_data()` di scraper:

```python
def extract_article_data(self, article_element):
    # ... existing code ...

    # Tambah field baru
    category_elem = article_element.find('span', class_='category')
    article_data['category'] = category_elem.get_text(strip=True) if category_elem else ''

    return article_data
```

---

## ⚙️ Best Practices

1. **Rate Limiting**: Gunakan delay minimal 2 detik antar request
2. **Concurrency**: Set `max_concurrent=3-5` untuk stabilitas
3. **Error Handling**: Check logs untuk troubleshooting
4. **Respect ToS**: Gunakan data secara bertanggung jawab
5. **Off-Peak Hours**: Scrape di jam sepi untuk performa lebih baik

---

## 📈 Performance Tips

### Untuk Speed:
```python
# Increase concurrent (hati-hati!)
scraper = MoneyControlCrawl4AIScraper(max_concurrent=8)
```

### Untuk Stability:
```python
# Decrease concurrent & add delay
scraper = MoneyControlCrawl4AIScraper(max_concurrent=3)
articles = await scraper.scrape_multiple_pages(num_pages=5, delay=3.0)
```

### Auto-Detect All Pages:
```python
from scrapers import EnhancedMoneyControlScraper

scraper = EnhancedMoneyControlScraper()
articles = await scraper.scrape_all_pages()  # Otomatis detect & scrape semua
```

---

## 🔐 Requirements

- Python 3.8+
- requests
- beautifulsoup4
- pandas
- crawl4ai (untuk Crawl4AI scraper - RECOMMENDED)
- playwright (untuk Playwright dan Crawl4AI scraper)

---

## 📝 License

MIT License

---

## ⚠️ Disclaimer

Tool ini dibuat untuk tujuan edukasi. Pastikan mematuhi terms of service website dan gunakan secara bertanggung jawab.

---

## 🤝 Contributing

Contributions welcome! Silakan buat issue atau pull request.

---

## 📞 Support

Jika ada pertanyaan atau issue:
1. Check `docs/` folder untuk dokumentasi
2. Review logs untuk debugging
3. Adjust configuration sesuai kebutuhan

---

**Happy Scraping! 🚀**
