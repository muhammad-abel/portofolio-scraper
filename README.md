# Portfolio Web Scrapers

Collection of web scrapers untuk berbagai website - Moneycontrol News & TradingEconomics Indicators

## 📁 Struktur Project

```
portofolio-scraper/
├── scrapers/                       # Core scraper modules
│   ├── __init__.py
│   ├── crawl4ai_scraper.py         # Moneycontrol scraper (RECOMMENDED)
│   ├── playwright_scraper.py       # Moneycontrol Playwright scraper
│   ├── requests_scraper.py         # Moneycontrol Requests scraper
│   ├── auto_pages_scraper.py       # Moneycontrol auto-detect pages
│   └── tradingeconomics/           # TradingEconomics scrapers
│       ├── __init__.py
│       └── indicators_scraper.py   # Economic indicators scraper
├── examples/                       # Example & template scripts
│   ├── custom_scraper.py           # Template untuk custom website
│   └── json_output_examples.py     # Contoh berbagai format JSON output
├── docs/                           # Documentation
│   ├── SCRAPING_GUIDE.md           # Panduan lengkap web scraping
│   └── ERROR_HANDLING_GUIDE.md     # Troubleshooting & error handling
├── logs/                           # Log files (auto-created)
│   ├── moneycontrol/
│   └── tradingeconomics/
├── run_crawl4ai.py                 # Moneycontrol scraper runner
├── run_playwright.py               # Moneycontrol Playwright runner
├── run_requests.py                 # Moneycontrol Requests runner
├── run_tradingeconomics.py         # TradingEconomics scraper runner (NEW)
├── upload_to_mongodb.py            # Upload JSON data ke MongoDB
├── config.py                       # Konfigurasi settings
├── requirements.txt                # Dependencies
├── .env.example                    # Contoh konfigurasi environment variables
├── README.md                       # Dokumentasi utama
└── .gitignore                      # Git ignore rules
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
# Basic usage - markets category (default, scrapes 3 pages)
python run_crawl4ai.py

# Scrape world news
python run_crawl4ai.py --category world --pages 10

# Scrape stocks news and upload to MongoDB
python run_crawl4ai.py --category stocks --pages 5 --upload-mongo

# Scrape economy news with custom settings
python run_crawl4ai.py --category economy --pages 10 --max-concurrent 3 --upload-mongo

# View all options
python run_crawl4ai.py --help
```

**Available Categories:**
- `markets` - Business/Markets news (default)
- `world` - World news
- `stocks` - Stock market news
- `economy` - Economy news

**Available Options:**
- `--category NAME`: Category to scrape (default: markets)
- `--pages N`: Number of pages to scrape (default: 3)
- `--max-concurrent N`: Max concurrent detail page requests (default: 5)
- `--delay SECONDS`: Delay between page requests (default: 2.0)
- `--upload-mongo`: Upload directly to MongoDB (skip local file saving)
- `--no-details`: Skip fetching article details (faster, but no date/author/full_content)

**Output Files by Category:**
```
moneycontrol_markets_crawl4ai.json    # Markets
moneycontrol_world_crawl4ai.json      # World
moneycontrol_stocks_crawl4ai.json     # Stocks
moneycontrol_economy_crawl4ai.json    # Economy
```

**Log Files (in logs/ directory):**
```
logs/scraper_markets_crawl4ai.log
logs/scraper_world_crawl4ai.log
logs/scraper_stocks_crawl4ai.log
logs/scraper_economy_crawl4ai.log
```

**Note:** Ketika menggunakan `--upload-mongo`, file JSON dan CSV **tidak akan disimpan** secara lokal. Data langsung di-upload ke MongoDB saja.

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
    "hash": "kH8x5yF2mQ9nL3pR7vT1wK4sJ6bN0cV8zX2dG5hM1aY=",
    "summary": "Federal Reserve Chair Jerome Powell said tariffs...",
    "image_url": "https://images.moneycontrol.com/...",
    "date": "November 07, 2025",
    "author": "Moneycontrol News",
    "full_content": "Federal Reserve Chair Jerome Powell said...\n\nThe central bank has been monitoring...\n\nPowell emphasized that...",
    "scraped_at": "2025-11-07T08:30:00.123456"
  }
]
```

**Field Descriptions:**
- `title`: Judul artikel
- `url`: URL lengkap artikel
- `hash`: **Unique identifier** (SHA256 hash dari title+date, encoded base64) - untuk mencegah duplikasi
- `summary`: Ringkasan/excerpt dari list page
- `image_url`: URL gambar thumbnail
- `date`: Tanggal publikasi (dari detail page)
- `author`: Nama penulis (dari detail page)
- `full_content`: Konten artikel lengkap (semua paragraf dari detail page)
- `scraped_at`: Timestamp scraping

## 💾 Upload ke MongoDB

Upload hasil scraping ke MongoDB dengan 2 cara:

### **Cara 1: Auto-Upload Saat Scraping (RECOMMENDED)**

Gunakan flag `--upload-mongo` untuk langsung upload setelah scraping:

```bash
# Setup: Edit .env atau upload_to_mongodb.py dengan MongoDB credentials
cp .env.example .env
nano .env  # Isi MONGODB_CONNECTION_STRING, DATABASE_NAME, dll

# Scrape dan upload langsung
python run_crawl4ai.py --pages 5 --upload-mongo
```

### **Cara 2: Upload Manual dari File JSON**

Upload file JSON yang sudah ada:

```bash
python upload_to_mongodb.py
```

### Setup MongoDB

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

**Fitur Upload:**
- Auto-deduplication berdasarkan **hash** (SHA256 dari title+date)
- Upsert mode (update existing + insert new)
- Bulk operations untuk performa tinggi
- Progress tracking & logging
- Error handling yang robust
- Auto-indexing untuk query performance

**Catatan Deduplication:**
- Scraper menggunakan hash SHA256 (base64) dari kombinasi `title + date` sebagai unique identifier
- Hash lebih reliable daripada URL karena URL bisa berubah tapi konten tetap sama
- MongoDB akan otomatis skip artikel duplikat berdasarkan hash
- Jika ada artikel dengan judul dan tanggal yang sama, hanya versi terbaru yang tersimpan

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
| `hash` | **Unique identifier** (SHA256 dari title+date, base64 encoded) | Generated |
| `summary` | Ringkasan/excerpt | List page |
| `image_url` | URL gambar thumbnail | List page |
| `date` | Tanggal publikasi | Detail page |
| `author` | Nama penulis | Detail page |
| `full_content` | Konten artikel lengkap (semua paragraf) | Detail page |
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

---

# 📊 TradingEconomics Indicators Scraper

Scraper untuk mengekstrak data economic indicators dari TradingEconomics.com

## 🚀 Quick Start - TradingEconomics

```bash
# Scrape all tabs for India
python run_tradingeconomics.py --country india

# Scrape specific tabs
python run_tradingeconomics.py --country india --tabs gdp,labour,prices

# Scrape and upload to MongoDB
python run_tradingeconomics.py --country india --upload-mongo

# Scrape specific tabs with MongoDB upload
python run_tradingeconomics.py --country india --tabs gdp,labour --upload-mongo
```

## 📋 Available Tabs

11 tabs tersedia untuk scraping:
- `overview` - Overview indicators
- `gdp` - GDP indicators
- `labour` - Labour market indicators
- `prices` - Price indicators (inflation, CPI, etc.)
- `money` - Monetary indicators
- `trade` - Trade indicators
- `government` - Government indicators
- `business` - Business indicators
- `consumer` - Consumer indicators
- `housing` - Housing indicators
- `health` - Health indicators

## 📊 Output Files

**JSON per tab:**
```
tradingeconomics_india_overview.json
tradingeconomics_india_gdp.json
tradingeconomics_india_labour.json
tradingeconomics_india_prices.json
...
```

**Log files:**
```
logs/tradingeconomics/scraper_india.log
```

## 💾 Data Structure - TradingEconomics

```json
{
  "country": "india",
  "tab_name": "gdp",
  "indicator": "GDP Growth Rate",
  "last": "6.5",
  "previous": "7.2",
  "highest": "8.9",
  "lowest": "3.1",
  "unit": "%",
  "reference": "Q2 2025",
  "hash": "abc123...",
  "scraped_at": "2025-11-10T..."
}
```

## 🗄️ MongoDB - TradingEconomics

**Collection:** `indicators` (dalam database yang dikonfigurasi di `.env`)

**Index:**
- Unique index: `hash` (SHA256 dari country + tab + indicator)
- Index: `country`, `tab_name`

**Configuration:**
Edit `.env` file:
```bash
MONGODB_CONNECTION_STRING=mongodb://localhost:27017/
MONGODB_DATABASE_NAME=tradingeconomics_db
```

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
