# 📖 Panduan Lengkap Web Scraping

## 🎯 Konsep Dasar

### 1. Cara Kerja Web Scraping (Simplified)

```
┌─────────────┐
│   Website   │  ← 1. Kirim HTTP Request
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  HTML Code  │  ← 2. Terima HTML Response
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ BeautifulSoup│ ← 3. Parse HTML menjadi Tree
└──────┬──────┘
       │
       ▼
┌─────────────┐
│Find Elements│  ← 4. Cari element dengan selector
└──────┬──────┘
       │
       ▼
┌─────────────┐
│Extract Data │  ← 5. Ambil text/attribute
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Save Data  │  ← 6. Simpan ke JSON/CSV
└─────────────┘
```

## 🔍 Cara Menemukan Data yang Anda Mau

### Step 1: Inspect Element di Browser

1. **Buka website** target di Chrome/Firefox
2. **Klik kanan** pada elemen yang mau di-scrape
3. **Pilih "Inspect"** atau tekan `F12`
4. **Lihat HTML structure** di Developer Tools

**Contoh:**
```
Klik kanan pada judul berita → Inspect

Anda akan lihat:
<h2 class="article-title">
  <a href="/news/123">Judul Berita Disini</a>
</h2>
```

### Step 2: Identifikasi Pattern

Cari pola yang **konsisten** di semua item:

✅ **Container** - Element yang membungkus data
```html
<div class="news-item">     ← Container
  <h2>...</h2>               ← Judul
  <span>...</span>           ← Tanggal
  <p>...</p>                 ← Deskripsi
</div>
```

✅ **Identifier** - Class/ID yang unique
- `class="news-item"` → untuk container
- `class="article-title"` → untuk judul
- `class="publish-date"` → untuk tanggal

### Step 3: Tulis Selector

**BeautifulSoup Methods:**

```python
# 1. Find by TAG
soup.find('h2')                    # Cari tag <h2> pertama
soup.find_all('p')                 # Cari semua tag <p>

# 2. Find by CLASS
soup.find('div', class_='news-item')
soup.find_all('span', class_='date')

# 3. Find by ID
soup.find('div', id='main-content')

# 4. Find by ATTRIBUTE
soup.find('a', {'data-type': 'article'})
soup.find('img', {'alt': 'news'})

# 5. CSS Selector (Powerful!)
soup.select('div.news-item')       # Tag dengan class
soup.select('#main h2')            # h2 dalam element dengan ID main
soup.select('h2 > a')              # a yang direct child dari h2
soup.select('[data-type="news"]')  # Element dengan attribute
```

## 📝 CSS Selector Cheat Sheet

| Selector | Contoh | Deskripsi |
|----------|--------|-----------|
| `.class` | `.news-item` | Element dengan class="news-item" |
| `#id` | `#header` | Element dengan id="header" |
| `tag` | `div` | Semua tag `<div>` |
| `tag.class` | `div.article` | Tag div dengan class article |
| `tag#id` | `div#main` | Tag div dengan id main |
| `parent > child` | `div > p` | `<p>` yang direct child dari `<div>` |
| `ancestor descendant` | `div p` | Semua `<p>` dalam `<div>` |
| `[attribute]` | `[data-id]` | Element dengan attribute data-id |
| `[attribute="value"]` | `[type="text"]` | Element dengan type="text" |

## 🛠️ Template Code untuk Berbagai Kasus

### Kasus 1: Scrape News Articles

```python
from bs4 import BeautifulSoup
import requests

url = "https://example.com/news"
response = requests.get(url)
soup = BeautifulSoup(response.content, 'lxml')

# Cari semua artikel
articles = soup.find_all('div', class_='article')  # Sesuaikan class

for article in articles:
    # Extract judul
    title_elem = article.find('h2')  # atau h1, h3
    title = title_elem.get_text(strip=True) if title_elem else ''

    # Extract link
    link_elem = article.find('a')
    link = link_elem.get('href', '') if link_elem else ''

    # Extract tanggal
    date_elem = article.find('span', class_='date')  # Sesuaikan class
    date = date_elem.get_text(strip=True) if date_elem else ''

    # Extract deskripsi
    desc_elem = article.find('p')
    desc = desc_elem.get_text(strip=True) if desc_elem else ''

    print(f"{title} - {date}")
    print(f"Link: {link}")
    print(f"Desc: {desc[:100]}...\n")
```

### Kasus 2: Scrape Product Listings (E-commerce)

```python
products = soup.find_all('div', class_='product-card')

for product in products:
    # Nama produk
    name = product.find('h3', class_='product-name').get_text(strip=True)

    # Harga
    price = product.find('span', class_='price').get_text(strip=True)

    # Rating
    rating_elem = product.find('div', class_='rating')
    rating = rating_elem.get('data-rating', '') if rating_elem else ''

    # Gambar
    img = product.find('img')
    img_url = img.get('src', '') if img else ''

    print(f"{name} - {price} - Rating: {rating}")
```

### Kasus 3: Scrape Table Data

```python
table = soup.find('table', class_='data-table')
rows = table.find_all('tr')

data = []
for row in rows[1:]:  # Skip header row
    cols = row.find_all('td')
    if len(cols) >= 3:
        data.append({
            'col1': cols[0].get_text(strip=True),
            'col2': cols[1].get_text(strip=True),
            'col3': cols[2].get_text(strip=True),
        })

print(data)
```

### Kasus 4: Scrape dengan Pagination

```python
base_url = "https://example.com/news"
all_data = []

for page in range(1, 6):  # Scrape 5 halaman
    url = f"{base_url}/page-{page}"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'lxml')

    articles = soup.find_all('div', class_='article')
    for article in articles:
        # Extract data...
        all_data.append(data)

    # Delay untuk menghindari blocking
    import time
    time.sleep(2)
```

## 🐛 Debugging Tips

### 1. Print HTML untuk Lihat Struktur

```python
# Print HTML dari element
print(article_elem.prettify())

# Print semua class yang ada
print(article_elem.get('class'))

# Print semua attribute
print(article_elem.attrs)
```

### 2. Check Apakah Element Ada

```python
# ❌ BAD - akan error jika None
title = article.find('h2').get_text()

# ✅ GOOD - aman dari error
title_elem = article.find('h2')
if title_elem:
    title = title_elem.get_text(strip=True)
else:
    print("Title element not found!")
    title = ''
```

### 3. Test Selector di Browser Console

Di Developer Tools → Console, test selector:

```javascript
// Test CSS selector
document.querySelectorAll('div.article')

// Lihat isi element
document.querySelector('h2.title').textContent
```

## 🎓 Latihan Praktis

### Latihan 1: Inspect dan Tulis Selector

1. Buka https://news.ycombinator.com
2. Inspect judul berita
3. Tulis kode untuk extract semua judul

**Jawaban:**
```python
response = requests.get('https://news.ycombinator.com')
soup = BeautifulSoup(response.content, 'lxml')

titles = soup.select('span.titleline > a')
for title in titles:
    print(title.get_text())
```

### Latihan 2: Handle Missing Data

Website kadang punya element yang tidak lengkap. Handle dengan proper!

```python
def safe_extract(element, selector, attr=None):
    """Safely extract data with fallback"""
    found = element.find(selector) if isinstance(selector, str) else selector
    if not found:
        return ''
    if attr:
        return found.get(attr, '')
    return found.get_text(strip=True)

# Gunakan:
title = safe_extract(article, 'h2')
link = safe_extract(article.find('a'), None, 'href')
```

## ⚠️ Common Errors & Solutions

### Error 1: AttributeError: 'NoneType' object has no attribute 'get_text'

**Penyebab:** Element tidak ditemukan (None)

**Solusi:**
```python
# Selalu check sebelum extract
elem = soup.find('h2')
if elem:
    text = elem.get_text()
else:
    text = ''
```

### Error 2: Tidak Ada Data yang Ke-scrape

**Penyebab:**
- Selector salah
- Website pakai JavaScript rendering

**Solusi:**
```python
# 1. Print untuk debug
containers = soup.find_all('div', class_='article')
print(f"Found {len(containers)} containers")
if len(containers) == 0:
    print("Selector mungkin salah!")
    print(soup.prettify()[:1000])  # Print HTML

# 2. Gunakan Playwright/Crawl4AI untuk JavaScript site
```

### Error 3: Data Tidak Lengkap

**Penyebab:** Struktur HTML berbeda antar item

**Solusi:** Gunakan multiple fallback selector
```python
# Try multiple selectors
date_elem = (
    article.find('span', class_='date') or
    article.find('time') or
    article.find('span', class_='publish-date')
)
```

## 🚀 Next Steps

1. **Praktek** dengan website sederhana dulu
2. **Inspect** struktur HTML dengan baik
3. **Test** selector di Python console/Jupyter notebook
4. **Handle** error dengan proper checking
5. **Respect** robots.txt dan rate limiting

## 📚 Resources

- BeautifulSoup Docs: https://www.crummy.com/software/BeautifulSoup/bs4/doc/
- CSS Selector Reference: https://www.w3schools.com/cssref/css_selectors.asp
- Regex for cleaning: https://regex101.com/

---

**Pro Tip:** Selalu test scraper Anda dengan 1 halaman dulu sebelum scale up!
