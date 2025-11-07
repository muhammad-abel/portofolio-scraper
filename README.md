# Moneycontrol News Scraper

Web scraper untuk mengekstrak berita dari Moneycontrol.com bagian Markets (https://www.moneycontrol.com/news/business/markets/)

## Fitur

- ✅ Scraping berita dari multiple pages
- ✅ Ekstraksi data: judul, URL, tanggal, ringkasan, gambar, author
- ✅ Export ke JSON, CSV, dan Excel
- ✅ Rate limiting dan retry mechanism
- ✅ Comprehensive logging
- ✅ Dua mode: Regular (requests) dan Selenium (untuk JavaScript content)

## Instalasi

### 1. Clone repository
```bash
git clone <repository-url>
cd portofolio-scraper
```

### 2. Buat virtual environment (recommended)
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# atau
venv\Scripts\activate  # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Install Chrome/Chromium (untuk Selenium scraper)
Jika menggunakan `moneycontrol_scraper_selenium.py`, pastikan Chrome atau Chromium terinstall.

## Cara Penggunaan

### Mode 1: Regular Scraper (Recommended)

Scraper ini menggunakan `requests` dan `BeautifulSoup` - lebih cepat dan ringan:

```bash
python moneycontrol_scraper.py
```

### Mode 2: Selenium Scraper

Gunakan jika website memerlukan JavaScript rendering:

```bash
python moneycontrol_scraper_selenium.py
```

### Kustomisasi

Edit file `config.py` untuk mengubah pengaturan:

```python
NUM_PAGES = 5  # Ubah jumlah halaman yang akan di-scrape
DELAY_BETWEEN_PAGES = 2.0  # Delay antar request (detik)
OUTPUT_JSON = True  # Export ke JSON
OUTPUT_CSV = True  # Export ke CSV
OUTPUT_EXCEL = True  # Export ke Excel
```

## Output

Scraper akan menghasilkan file-file berikut:

- `moneycontrol_news.json` - Format JSON
- `moneycontrol_news.csv` - Format CSV (bisa dibuka di Excel)
- `moneycontrol_news.xlsx` - Format Excel (opsional)
- `scraper.log` - Log file untuk debugging

### Contoh Output JSON

```json
[
  {
    "title": "Stock market today: Sensex gains 500 points...",
    "url": "https://www.moneycontrol.com/news/...",
    "date": "December 15, 2024",
    "summary": "Indian stock market extended gains...",
    "image_url": "https://...",
    "author": "Author Name",
    "scraped_at": "2024-12-15T10:30:00"
  }
]
```

## Struktur Data

Setiap artikel memiliki field berikut:

| Field | Deskripsi |
|-------|-----------|
| `title` | Judul berita |
| `url` | Link ke artikel lengkap |
| `date` | Tanggal publikasi |
| `summary` | Ringkasan/excerpt artikel |
| `image_url` | URL gambar thumbnail |
| `author` | Nama penulis (jika tersedia) |
| `scraped_at` | Timestamp saat data di-scrape |

## Troubleshooting

### Error: Connection refused
- Cek koneksi internet
- Website mungkin memblokir request - coba gunakan Selenium scraper
- Tambah delay antar request di `config.py`

### Error: No articles found
- Website mungkin mengubah struktur HTML
- Periksa log file untuk detail
- Coba Selenium scraper sebagai alternatif

### Error: ChromeDriver
```bash
# Install webdriver-manager akan otomatis download ChromeDriver
pip install webdriver-manager --upgrade
```

## Best Practices

1. **Gunakan rate limiting**: Jangan scrape terlalu cepat untuk menghindari blocking
2. **Check robots.txt**: Pastikan scraping diizinkan
3. **Respect terms of service**: Gunakan data secara bertanggung jawab
4. **Add delays**: Minimal 2 detik antar request

## Development

### Menambah field baru

Edit fungsi `extract_article_data()` di scraper:

```python
# Contoh: tambah kategori
category_elem = article_element.find('span', class_='category')
article_data['category'] = category_elem.get_text(strip=True) if category_elem else ''
```

### Testing

```bash
# Test dengan 1 halaman dulu
python moneycontrol_scraper.py --pages 1
```

## Requirements

- Python 3.8+
- requests
- beautifulsoup4
- pandas
- selenium (opsional, untuk Selenium scraper)

## License

MIT License

## Disclaimer

Tool ini dibuat untuk tujuan edukasi. Pastikan mematuhi terms of service website dan gunakan secara bertanggung jawab.
