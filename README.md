# Moneycontrol News Scraper

Scrapes news articles from Moneycontrol.com (https://www.moneycontrol.com/news/business/)
and exports them to JSON, CSV, or MongoDB.

Four scraper implementations are included. **Use the Crawl4AI one** - it is the only one
that is fully featured (CLI flags, category selection, full article text, MongoDB upload).
The other three are simpler variants kept for reference and comparison.

---

## Project Layout

```
portofolio-scraper/
|-- scrapers/
|   |-- __init__.py
|   |-- crawl4ai_scraper.py      # Main scraper. Async, has CLI, has MongoDB upload.
|   |-- playwright_scraper.py    # Playwright variant. No CLI, no full_content.
|   |-- requests_scraper.py      # requests + BeautifulSoup. No JS support.
|   |-- auto_pages_scraper.py    # Crawl4AI + auto-detect of total page count.
|-- examples/
|   |-- custom_scraper.py        # Template for adapting this to another site
|   |-- json_output_examples.py  # Demonstrates 8 JSON output shapes
|-- docs/
|   |-- SCRAPING_GUIDE.md        # How the scraping works, selector reference
|   |-- ERROR_HANDLING_GUIDE.md  # Timeouts, rate limiting, retries
|-- run_crawl4ai.py              # Entry point -> crawl4ai_scraper.main()
|-- run_playwright.py            # Entry point -> playwright_scraper.main()
|-- run_requests.py              # Entry point -> requests_scraper.main()
|-- upload_to_mongodb.py         # Standalone: upload an existing JSON file to MongoDB
|-- config.py                    # NOT USED - see "About config.py" below
|-- requirements.txt
|-- .env.example                 # Copy to .env and fill in MongoDB settings
```

---

## Setup

Requires Python 3.8+.

```bash
# 1. Virtual environment (recommended)
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux / macOS

# 2. Dependencies
pip install -r requirements.txt

# 3. Browser binary (needed by Crawl4AI and Playwright scrapers)
playwright install chromium
```

MongoDB is optional. You only need it if you plan to use `--upload-mongo` or
`upload_to_mongodb.py`. See [MongoDB](#mongodb) below.

---

## Usage

### Crawl4AI scraper (the main one)

```bash
# Default: markets category, 3 pages, saves JSON + CSV to the project root
python run_crawl4ai.py

# Pick a category and page count
python run_crawl4ai.py --category world --pages 10

# Scrape and push straight to MongoDB (no local files are written)
python run_crawl4ai.py --category stocks --pages 5 --upload-mongo

# Gentler on the site: fewer parallel requests, longer pause between pages
python run_crawl4ai.py --category economy --pages 10 --max-concurrent 3 --delay 3.0

python run_crawl4ai.py --help
```

**Flags**

| Flag | Default | Meaning |
|------|---------|---------|
| `--category` | `markets` | One of `markets`, `world`, `stocks`, `economy` |
| `--pages` | `3` | How many list pages to walk |
| `--max-concurrent` | `5` | Cap on simultaneous article-detail fetches |
| `--delay` | `2.0` | Seconds to wait between list pages |
| `--upload-mongo` | off | Upload to MongoDB instead of writing local files |
| `--no-details` | off | Skip detail pages. Much faster, but you lose `date`, `author`, and `full_content` |

**Categories** map to these URLs:

| Category | URL |
|----------|-----|
| `markets` | `https://www.moneycontrol.com/news/business/markets/` |
| `world` | `https://www.moneycontrol.com/news/business/world/` |
| `stocks` | `https://www.moneycontrol.com/news/business/stocks/` |
| `economy` | `https://www.moneycontrol.com/news/business/economy/` |

**Output files** are named after the category:

```
moneycontrol_markets_crawl4ai.json
moneycontrol_markets_crawl4ai.csv
logs/scraper_markets_crawl4ai.log
```

Note that `--upload-mongo` **replaces** local file output rather than adding to it. With
that flag set, no JSON or CSV is written - the articles go straight from memory into
MongoDB. Drop the flag if you want files on disk.

### The other three scrapers

These have **no command-line arguments**. Settings are hardcoded in their `main()`
functions - edit the file if you want to change them.

```bash
python run_playwright.py                  # markets, 3 pages, headless Chromium
python run_requests.py                    # markets, 3 pages, no browser
python scrapers/auto_pages_scraper.py     # markets, auto-detects page count, capped at 5
```

| Scraper | Browser | JS | `full_content` | `hash` | CLI | Output file | Log file |
|---------|---------|-----|----------------|--------|-----|-------------|----------|
| `crawl4ai_scraper` | yes | yes | yes | yes | yes | `moneycontrol_<category>_crawl4ai.*` | `logs/scraper_<category>_crawl4ai.log` |
| `playwright_scraper` | yes | yes | no | no | no | `moneycontrol_news_playwright.*` | `scraper_playwright.log` |
| `requests_scraper` | no | no | no | no | no | `moneycontrol_news.*` | `scraper.log` |
| `auto_pages_scraper` | yes | yes | no | no | no | `moneycontrol_auto.*` | `scraper_crawl4ai_enhanced.log` |

`auto_pages_scraper` is the interesting one of the three: it binary-searches for the last
existing page number, so you can scrape a whole category without knowing its size. Its
`main()` currently caps at 5 pages - the uncapped call is on the line above, commented out.

---

## Output Format

```json
[
  {
    "title": "Powell says tariffs adding some pressure to inflation",
    "url": "https://www.moneycontrol.com/news/business/markets/...",
    "hash": "kH8x5yF2mQ9nL3pR7vT1wK4sJ6bN0cV8zX2dG5hM1aY=",
    "summary": "Federal Reserve Chair Jerome Powell said tariffs...",
    "image_url": "https://images.moneycontrol.com/...",
    "date": "November 07, 2025",
    "author": "Moneycontrol News",
    "full_content": "Federal Reserve Chair Jerome Powell said...\n\nThe central bank...",
    "scraped_at": "2025-11-07T08:30:00.123456"
  }
]
```

| Field | Source | Notes |
|-------|--------|-------|
| `title` | list page | |
| `url` | list page | Absolute URL |
| `summary` | list page | Short excerpt |
| `image_url` | list page | Falls back to `data-src` for lazy-loaded images |
| `date` | detail page | Empty if `--no-details` or if extraction fails |
| `author` | detail page | Often empty - many articles have no byline |
| `full_content` | detail page | All `<p>` text joined by blank lines. Crawl4AI scraper only |
| `hash` | generated | Deduplication key. Crawl4AI scraper only |
| `scraped_at` | generated | ISO 8601 timestamp of the scrape |

`sample_output.example.json` holds a small fabricated sample if you want to see the shape
without running anything.

### The `hash` field

`hash` is `base64(sha256(lower(title) + "|" + lower(date)))`. It is the deduplication key
for MongoDB, chosen over `url` because Moneycontrol URLs can change while the article stays
the same. Two consequences worth knowing:

- If `date` extraction fails, the hash is computed over an empty date. The same article
  scraped later *with* a date produces a **different hash**, so it lands as a second
  document rather than an update.
- Only the Crawl4AI scraper generates it (see [MongoDB](#mongodb)).

---

## MongoDB

### Configuration

Copy the example file and fill it in. `.env` is gitignored - it never gets committed.

```bash
cp .env.example .env
```

```bash
# .env
MONGODB_CONNECTION_STRING=mongodb://localhost:27017/
MONGODB_DATABASE_NAME=moneycontrol_db
MONGODB_COLLECTION_NAME=news_articles
JSON_FILE_PATH=moneycontrol_markets_crawl4ai.json
```

Connection string formats:

| Target | Example |
|--------|---------|
| Local | `mongodb://localhost:27017/` |
| Local with auth | `mongodb://user:pass@localhost:27017/` |
| Atlas | `mongodb+srv://user:pass@cluster.mongodb.net/` |

All four settings have defaults in `upload_to_mongodb.py`, so `.env` is optional if
localhost defaults suit you.

### Two ways to upload

**During the scrape** - articles go straight from memory to MongoDB, no files:

```bash
python run_crawl4ai.py --category markets --pages 5 --upload-mongo
```

**After the fact** - loads the JSON file named by `JSON_FILE_PATH`:

```bash
python upload_to_mongodb.py
```

> **Heads up on `JSON_FILE_PATH`:** its built-in default is
> `moneycontrol_news_crawl4ai.json`, which is an *older* naming scheme. The scraper now
> writes per-category names like `moneycontrol_markets_crawl4ai.json`. Set `JSON_FILE_PATH`
> in your `.env` to the file you actually produced, or the upload will not find it.

### How the upload behaves

- Creates a **unique index on `hash`**, plus plain indexes on `url`, `date`, and
  `scraped_at`.
- Uses `bulk_write` with `UpdateOne(..., upsert=True)` keyed on `hash`, falling back to
  `url` when a document has no `hash`. Re-scraping the same articles updates them in place
  instead of duplicating.
- Reports inserted / updated / skipped / failed counts, then prints collection stats.

> **Only feed it Crawl4AI output.** The other three scrapers do not produce a `hash` field.
> Because the collection has a unique index on `hash`, a batch of hash-less documents all
> read as `hash: null` and collide with each other - the first one inserts and the rest
> fail with a duplicate key error. If you want to upload output from those scrapers, either
> add a hash field first or drop the unique index.

---

## Tuning

There are no config files to edit - pass flags, or construct the scraper yourself:

```python
import asyncio
from scrapers import MoneyControlCrawl4AIScraper

async def run():
    scraper = MoneyControlCrawl4AIScraper(
        base_url="https://www.moneycontrol.com/news/business/markets/",
        fetch_details=True,   # False = skip detail pages (same as --no-details)
        max_concurrent=5,     # Parallel detail fetches
    )
    articles = await scraper.scrape_multiple_pages(num_pages=5, delay=2.0)
    scraper.save_to_json(articles, "my_output.json")
    scraper.save_to_csv(articles, "my_output.csv")

asyncio.run(run())
```

`save_to_excel()` also exists but needs `openpyxl`, which is not in `requirements.txt` -
`pip install openpyxl` first.

Rules of thumb:

- **Getting timeouts?** Lower `--max-concurrent` to 3 and raise `--delay` to 3.0.
- **Want speed?** Raise `--max-concurrent`, or use `--no-details` to skip detail pages
  entirely - that is the single biggest win, since detail fetching is one request per
  article.
- **Be polite.** The defaults (5 concurrent, 2s between pages, 0.5-1.5s jitter between
  detail fetches) are already reasonable. Pushing much harder risks getting your IP
  throttled.

### About `config.py`

`config.py` exists but **nothing imports it**. The values in it are dead - editing
`NUM_PAGES` or `DELAY_BETWEEN_PAGES` there has no effect on any scraper. It is a leftover
from an earlier version. Use the CLI flags or the constructor arguments shown above.

---

## Reliability Details

The Crawl4AI scraper is built to survive a flaky site:

- **Retries:** each detail page gets 2 attempts with exponential backoff.
- **Timeout:** 120 seconds per detail page.
- **Concurrency cap:** an `asyncio.Semaphore` bounds in-flight detail requests, plus a
  0.5-1.5s jitter after each one.
- **Failure isolation:** `asyncio.gather(..., return_exceptions=True)` means one bad
  article cannot kill the run - it is logged and left with empty fields.
- **Selector fallbacks:** articles come in several layouts. Author falls back from
  `<div class="article_author"><a>` to the div's own text; date falls back from
  `<div class="article_schedule">` to `<p class="date">`; video-format articles fall back to
  `<div class="video_content">`. Fields that still cannot be found end up empty rather than
  raising.

Because of those fallbacks, **empty `author` or `date` fields are normal**, not a bug. Check
the log if a whole run comes back empty.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `ModuleNotFoundError` | `pip install -r requirements.txt` |
| `playwright._impl._api_types.Error: Executable doesn't exist` | `playwright install chromium` |
| Timeouts on detail pages | `--max-concurrent 3 --delay 3.0` |
| Zero articles scraped | Moneycontrol likely changed its HTML. See `extract_article_data()` and `docs/SCRAPING_GUIDE.md` |
| MongoDB `ServerSelectionTimeoutError` | Server not running, or wrong `MONGODB_CONNECTION_STRING`. Atlas also needs your IP allowlisted |
| `upload_to_mongodb.py` says file not found | `JSON_FILE_PATH` does not match your output filename - see the note above |
| Duplicate key error on upload | Uploading non-Crawl4AI output. See the MongoDB warning above |

Logs are the first place to look. Each scraper writes its own file (see the table in
[Usage](#the-other-three-scrapers)); the MongoDB script writes `mongodb_upload.log`.

`docs/ERROR_HANDLING_GUIDE.md` goes deeper on timeouts and rate limiting.
`docs/SCRAPING_GUIDE.md` covers how to inspect the page and update selectors when the site
changes.

---

## Extending

To capture a new field, edit `extract_article_data()` in the scraper you use:

```python
def extract_article_data(self, article_element):
    # ... existing code ...
    category_elem = article_element.find('span', class_='category')
    article_data['category'] = category_elem.get_text(strip=True) if category_elem else ''
    return article_data
```

The `''` fallback matters - keep that pattern, since a missing element is normal here and
should not raise.

To add a category, add an entry to the `CATEGORIES` dict at the top of
`scrapers/crawl4ai_scraper.py`. Argparse picks up the choices automatically.

To point this at a different site entirely, start from `examples/custom_scraper.py`.

---

## Notes

- Educational project. Respect Moneycontrol's terms of service and robots.txt, keep the
  request rate modest, and do not redistribute scraped content.
- `.env` is gitignored. Keep it that way - it holds your database credentials.
- License: MIT.
