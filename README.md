# Portfolio Web Scrapers

Collection of web scrapers untuk berbagai website - Moneycontrol News, TradingEconomics Indicators & Screener.in Stock Fundamentals

## 📁 Struktur Project

```
portofolio-scraper/
├── scrapers/                       # Core scraper modules
│   ├── __init__.py
│   ├── base_scraper.py             # Base scraper with memory-efficient patterns
│   ├── crawl4ai_scraper.py         # Moneycontrol scraper (RECOMMENDED)
│   ├── playwright_scraper.py       # Moneycontrol Playwright scraper
│   ├── requests_scraper.py         # Moneycontrol Requests scraper
│   ├── auto_pages_scraper.py       # Moneycontrol auto-detect pages
│   ├── tradingeconomics/           # TradingEconomics scrapers
│   │   ├── __init__.py
│   │   └── indicators_scraper.py   # Economic indicators scraper
│   └── screener/                   # Screener.in scrapers (NEW)
│       ├── __init__.py
│       └── screener_scraper.py     # Stock fundamentals scraper
├── data/                           # Data files
│   └── nifty100_symbols.json       # Nifty 100 stock symbols
├── examples/                       # Example & template scripts
│   ├── custom_scraper.py           # Template untuk custom website
│   ├── json_output_examples.py     # Contoh berbagai format JSON output
│   ├── memory_efficient_scraping.py # Memory optimization examples
│   ├── screener_output_example.json # Example screener output (legacy)
│   └── screener_output_example_hybrid.json # Example hybrid structure (NEW)
├── docs/                           # Documentation
│   ├── SCRAPING_GUIDE.md           # Panduan lengkap web scraping
│   ├── ERROR_HANDLING_GUIDE.md     # Troubleshooting & error handling
│   └── MEMORY_OPTIMIZATION.md      # Memory optimization guide
├── tools/                          # Utility tools
│   └── memory_profiler.py          # Memory profiling tool
├── logs/                           # Log files (auto-created)
│   ├── moneycontrol/
│   ├── tradingeconomics/
│   └── screener/
├── run_crawl4ai.py                 # Moneycontrol scraper runner
├── run_playwright.py               # Moneycontrol Playwright runner
├── run_requests.py                 # Moneycontrol Requests runner
├── run_tradingeconomics.py         # TradingEconomics scraper runner
├── run_screener.py                 # Screener.in scraper runner (NEW)
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

- **`docs/MEMORY_OPTIMIZATION.md`** - Memory optimization guide (NEW!)
  - Why memory optimization matters
  - Generator vs Batched vs Standard methods
  - Memory usage comparison
  - Usage examples & best practices
  - Performance profiling tools
  - Migration guide

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

### 🧠 Memory Optimization (NEW!)

**For large-scale scraping (>100 pages), use memory-efficient methods:**

```python
# ✅ Generator method (recommended for large jobs)
# Memory usage stays constant regardless of page count
async for articles in scraper.scrape_pages_generator(num_pages=500):
    scraper.save_to_json(articles, f"page_{i}.json")
    # Memory freed after each iteration

# ✅ Batched method (balance between memory & convenience)
async for batch in scraper.scrape_pages_batched(
    num_pages=500,
    batch_size=50
):
    scraper.save_to_json(batch, f"batch_{i}.json")

# ✅ Streaming JSON save (single file, minimal memory)
generator = scraper.scrape_pages_generator(num_pages=500)
await scraper.save_to_json_streaming(generator, "output.json")

# ✅ Direct MongoDB upload (memory-efficient)
from upload_to_mongodb import MongoDBUploader
uploader = MongoDBUploader(...)
generator = scraper.scrape_pages_generator(num_pages=1000)
await uploader.upload_articles_streaming_async(generator)
```

**Memory Profiling Tool:**
```bash
# Compare memory usage of different methods
python tools/memory_profiler.py --pages 100 --method compare

# Test specific method
python tools/memory_profiler.py --pages 500 --method generator
```

**📖 Full guide:** See [docs/MEMORY_OPTIMIZATION.md](docs/MEMORY_OPTIMIZATION.md) for complete documentation.

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

# 📈 Screener.in Stock Fundamentals Scraper

Scraper untuk mengekstrak fundamental data, shareholding patterns, dan quarterly results dari Screener.in untuk Nifty 100 stocks

## 🚀 Quick Start - Screener.in

```bash
# Scrape all Nifty 100 stocks (default)
python run_screener.py

# Scrape specific stocks
python run_screener.py --symbols HDFCBANK,TCS,RELIANCE

# Use generator method (memory-efficient for all 100 stocks)
python run_screener.py --method generator

# Custom batch size and delay
python run_screener.py --batch-size 20 --delay 2.5

# Save to custom output file
python run_screener.py --output nifty100_data.json
```

## 📊 What Data is Scraped

### 1. **Stock Fundamentals** ⭐
- Current Price, 52-week High/Low
- Market Cap
- Valuation Ratios: P/E, P/B, EV/EBITDA
- Profitability: ROE, ROCE, Net Profit Margin
- Debt/Equity Ratio
- Sales & Profit Growth

### 2. **Shareholding Patterns** ⭐⭐⭐ (MOST VALUABLE!)
- Promoter Holding %
- **FII (Foreign Institutional Investors) Holding %**
- **DII (Domestic Institutional Investors) Holding %**
- Public Holding %
- **Quarter-over-Quarter Changes** (FII/DII movements!)
- Historical quarterly data (last 4 quarters)

**Why Important:** FII/DII data is UNIQUE to screener.in and directly answers:
- "What are recent FII and DII investment trends?"
- Helps explain market movements
- Indicates institutional confidence

### 3. **Quarterly Results**
- Revenue (QoQ & YoY growth)
- Net Profit (QoQ & YoY growth)
- EPS
- Sales Growth %
- Last 4 quarters data

## 💾 Data Structure - Screener.in

**Hybrid Structure**: Combines **computed summary fields** (quick access) + **raw table data** (complete for LLM analysis)

```json
{
  "symbol": "HDFCBANK",
  "name": "HDFC Bank Ltd",
  "sector": "Banking",
  "current_price": 1645.50,
  "scraped_at": "2024-11-11T...",
  "hash": "abc123...",

  // ⭐ COMPUTED FIELDS (Quick Access)
  "summary": {
    "fundamentals": {
      "market_cap": 1250000,
      "pe_ratio": 18.5,
      "pb_ratio": 2.8,
      "roe": 16.5,
      "roce": 8.2,
      "debt_to_equity": 0.5,
      "sales_growth": 18.5,
      "profit_growth": 22.3
    },
    "latest_shareholding": {
      "quarter": "Sep 2024",
      "promoter": 26.5,
      "fii": 45.2,              // ⭐ Key data!
      "dii": 18.3,              // ⭐ Key data!
      "fii_change_qoq": 1.2,    // ⭐ Very important!
      "dii_change_qoq": -0.5,
      "promoter_change_qoq": 0.0
    },
    "latest_quarter": {
      "quarter": "Sep 2024",
      "revenue": 450000000000.0,
      "profit": 120000000000.0,
      "eps": 22.5,
      "revenue_growth_yoy": 18.4,
      "profit_growth_yoy": 22.3
    },
    "shareholding_historical": [...]  // Last 4 quarters
  },

  // 🗂️ RAW DATA (Dict-by-Date Format for RAG/LLM)
  "fundamentals_raw": [
    { "metric": "Market Cap", "value": "₹12,50,000 Cr" },
    { "metric": "Stock P/E", "value": "18.5" },
    { "metric": "ROE", "value": "16.5%" },
    ...
  ],
  "shareholding_raw": {
    "Sep 2024": { "promoters": "26.5%", "fii": "45.2%", "dii": "18.3%", "public": "10.0%" },
    "Jun 2024": { "promoters": "26.5%", "fii": "44.0%", "dii": "18.8%", "public": "10.7%" },
    "Mar 2024": { "promoters": "26.5%", "fii": "43.5%", "dii": "19.2%", "public": "10.8%" },
    ...
  },
  "quarterly_results_raw": {
    "Sep 2024": { "sales": "45,000", "net_profit": "12,000", "eps_in_rs": "22.5", ... },
    "Jun 2024": { "sales": "42,000", "net_profit": "11,500", "eps_in_rs": "21.8", ... },
    "Mar 2024": { "sales": "40,000", "net_profit": "11,000", "eps_in_rs": "20.5", ... },
    ...
  },
  "profit_loss_raw": {
    "Mar 2024": { "sales": "1,80,000", "expenses": "1,30,000", ... },
    "Mar 2023": { "sales": "1,60,000", "expenses": "1,15,000", ... },
    ...
  },
  "balance_sheet_raw": {
    "Mar 2024": { "equity_capital": "534", "reserves": "2,40,000", ... },
    "Mar 2023": { "equity_capital": "534", "reserves": "2,20,000", ... },
    ...
  },
  "cash_flow_raw": {
    "Mar 2024": { "cash_from_operating_activity": "55,000", ... },
    "Mar 2023": { "cash_from_operating_activity": "50,000", ... },
    ...
  }
}
```

**Why Hybrid Approach?**
- ✅ **Computed fields**: Fast querying and filtering (e.g., "stocks with P/E < 20")
- ✅ **Dict-by-date raw tables**: RAG/LLM-friendly format with O(1) lookups
  - Easy access: `data["Sep 2024"]["revenue"]`
  - Clear context for LLMs: "Sep 2024 profit is 18,627"
  - No complex array indexing needed
- ✅ **Best of both worlds**: Quick access + maximum flexibility

## 🎯 Usage Options

### Method 1: All Nifty 100 (Batched - Recommended)
```bash
python run_screener.py --batch-size 20
# Scrapes in batches of 20 stocks
# Memory-efficient, good progress tracking
```

### Method 2: All Nifty 100 (Generator - Most Memory Efficient)
```bash
python run_screener.py --method generator
# Constant memory usage
# Single JSON output file
```

### Method 3: Specific Stocks Only
```bash
python run_screener.py --symbols HDFCBANK,TCS,RELIANCE,INFY
# Quick testing or specific stocks
```

### Method 4: Custom Symbol List
```bash
# Create your own JSON file with symbols
python run_screener.py --symbols-file data/my_stocks.json
```

## ⚙️ Configuration

**Available Options:**
```bash
--symbols-file PATH      JSON file with stock symbols (default: data/nifty100_symbols.json)
--symbols LIST           Comma-separated symbols (e.g., HDFCBANK,TCS)
--method METHOD          Scraping method: standard, generator, batched (default: batched)
--batch-size N           Batch size for batched method (default: 10)
--delay SECONDS          Delay between stocks (default: 3.0)
--output PATH            Output JSON file (default: screener_stocks.json)
```

## ⚠️ Important Notes

1. **Rate Limiting**: Screener.in has anti-bot measures
   - Default delay: 3 seconds between stocks
   - Don't set delay < 2 seconds
   - Use low concurrency

2. **Scraping Time**:
   - 100 stocks × 3 seconds = ~5 minutes
   - Plan accordingly for complete Nifty 100 scrape

3. **Data Quality**:
   - Some metrics may be null for certain stocks
   - Scraper handles missing data gracefully
   - Check logs for any failures

4. **Symbol Format**:
   - Use screener.in format (e.g., "HDFCBANK" not "HDFCBANK.NS")
   - Nifty 100 list already formatted correctly

## 🗄️ MongoDB Integration

Upload screener data to MongoDB:

```python
from upload_to_mongodb import MongoDBUploader

uploader = MongoDBUploader(
    connection_string="mongodb://localhost:27017/",
    database_name="stocks_db",
    collection_name="nifty100_fundamentals"
)

uploader.connect()
uploader.create_indexes()

# Load scraped data
with open('screener_stocks.json') as f:
    stocks = json.load(f)

# Upload
stats = uploader.upload_articles(stocks, upsert=True)
```

**Deduplication:** Uses `hash` field (symbol + scrape date)

## 📖 Example Output

See `examples/screener_output_example.json` for complete data structure example.

## 🔗 Integration with Other Scrapers

**Perfect Combination:**
1. **Moneycontrol** → News & market sentiment
2. **TradingEconomics** → Macro indicators (GDP, inflation, rates)
3. **Screener.in** → Stock fundamentals & FII/DII data

**Example RAG Query:**
> "Why is HDFC Bank down 5% today?"

**Your Bot Can Answer:**
- Check Moneycontrol: Any negative news?
- Check TradingEconomics: RBI rate hike affecting banks?
- Check Screener: FII selling? Fundamentals weakening?

**Multi-source insights = Better answers!** 🎯

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
