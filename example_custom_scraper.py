#!/usr/bin/env python3
"""
Contoh Custom Scraper - Template untuk scrape website lain
Ganti URL dan selector sesuai kebutuhan Anda
"""

import requests
from bs4 import BeautifulSoup
import json
from typing import List, Dict

class CustomScraper:
    """Template scraper yang bisa di-customize"""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def fetch_page(self, url: str) -> BeautifulSoup:
        """Fetch dan parse halaman"""
        response = self.session.get(url)
        response.raise_for_status()
        return BeautifulSoup(response.content, 'lxml')

    def extract_data(self, container_element) -> Dict:
        """
        CUSTOMIZE FUNGSI INI!
        Ubah selector sesuai struktur HTML website target
        """
        data = {}

        # ========================================
        # CONTOH 1: Extract dari Moneycontrol News
        # Struktur: <li> -> <a class="unified-link" href="URL"> -> <h2>Title</h2>
        # ========================================

        # Cari link element dulu (biasanya membungkus konten)
        link_elem = container_element.find('a', class_='unified-link') or container_element.find('a')

        if link_elem:
            # Get URL dari <a href="">
            href = link_elem.get('href', '')
            data['url'] = href if href.startswith('http') else f"https://example.com{href}"

            # Get title dari <h2> di DALAM <a>
            title_elem = link_elem.find('h2')  # atau h1, h3 sesuai website
            data['title'] = title_elem.get_text(strip=True) if title_elem else ''

            # Get image dari <img> di DALAM <a>
            img_elem = link_elem.find('img')
            if img_elem:
                data['image'] = img_elem.get('src') or img_elem.get('data-src', '')
            else:
                data['image'] = ''
        else:
            data['url'] = ''
            data['title'] = ''
            data['image'] = ''

        # Cari tanggal - biasanya di luar <a>
        date_elem = container_element.find('span', class_='date')  # atau time, div, dll
        data['date'] = date_elem.get_text(strip=True) if date_elem else ''

        # Cari deskripsi/ringkasan - biasanya di luar <a>
        desc_elem = container_element.find('p')  # atau dengan class tertentu
        data['description'] = desc_elem.get_text(strip=True) if desc_elem else ''

        # ========================================
        # CONTOH 2: Extract dari Product Listing
        # ========================================
        # Uncomment jika scrape e-commerce
        # product_name = container_element.find('h3', class_='product-name')
        # data['product'] = product_name.get_text(strip=True) if product_name else ''
        #
        # price = container_element.find('span', class_='price')
        # data['price'] = price.get_text(strip=True) if price else ''
        #
        # rating = container_element.find('div', class_='rating')
        # data['rating'] = rating.get('data-rating', '') if rating else ''

        # ========================================
        # CONTOH 3: Extract dari Table
        # ========================================
        # Uncomment jika data dalam bentuk tabel
        # cells = container_element.find_all('td')
        # if len(cells) >= 3:
        #     data['column1'] = cells[0].get_text(strip=True)
        #     data['column2'] = cells[1].get_text(strip=True)
        #     data['column3'] = cells[2].get_text(strip=True)

        return data

    def scrape(self, url: str, container_selector: str,
               container_tag: str = 'div', container_class: str = None) -> List[Dict]:
        """
        Scrape halaman dengan selector custom

        Args:
            url: URL halaman yang mau di-scrape
            container_selector: CSS selector untuk container (gunakan ini atau tag+class)
            container_tag: Tag HTML container (default: 'div')
            container_class: Class CSS container

        Returns:
            List of dictionaries dengan data hasil scraping
        """
        soup = self.fetch_page(url)

        # Cari semua container
        if container_selector:
            # Gunakan CSS selector (lebih flexible)
            containers = soup.select(container_selector)
        else:
            # Gunakan find_all dengan tag dan class
            if container_class:
                containers = soup.find_all(container_tag, class_=container_class)
            else:
                containers = soup.find_all(container_tag)

        print(f"Found {len(containers)} items")

        # Extract data dari setiap container
        results = []
        for container in containers:
            data = self.extract_data(container)
            if data.get('title'):  # Hanya simpan jika ada title
                results.append(data)

        return results

    def save_json(self, data: List[Dict], filename: str = 'output.json'):
        """Save hasil ke JSON"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Saved {len(data)} items to {filename}")


# ============================================================
# CARA PENGGUNAAN
# ============================================================

if __name__ == "__main__":

    # CONTOH 1: Scrape Moneycontrol
    print("=" * 60)
    print("CONTOH 1: Scrape Moneycontrol News")
    print("=" * 60)

    scraper = CustomScraper(
        base_url="https://www.moneycontrol.com/news/business/markets/"
    )

    # Method 1: Gunakan CSS selector
    results = scraper.scrape(
        url="https://www.moneycontrol.com/news/business/markets/page-1/",
        container_selector="li.clearfix"  # CSS selector
    )

    # Method 2: Atau gunakan tag + class
    # results = scraper.scrape(
    #     url="https://www.moneycontrol.com/news/business/markets/page-1/",
    #     container_selector=None,
    #     container_tag="li",
    #     container_class="clearfix"
    # )

    if results:
        print(f"\nBerhasil scrape {len(results)} articles")
        print("\nPreview 3 artikel pertama:")
        for i, item in enumerate(results[:3], 1):
            print(f"\n{i}. {item.get('title', 'No title')}")
            print(f"   URL: {item.get('url', 'No URL')}")

        scraper.save_json(results, 'moneycontrol_custom.json')

    # ============================================================
    # CONTOH 2: Scrape Website Lain (Template)
    # ============================================================
    # Uncomment dan customize untuk website lain

    # print("\n" + "=" * 60)
    # print("CONTOH 2: Scrape Website Custom Anda")
    # print("=" * 60)
    #
    # custom_scraper = CustomScraper(
    #     base_url="https://example.com"  # Ganti dengan URL target
    # )
    #
    # results = custom_scraper.scrape(
    #     url="https://example.com/page-1",
    #     container_selector="div.article-card"  # Ganti dengan selector yang sesuai
    # )
    #
    # custom_scraper.save_json(results, 'custom_output.json')


# ============================================================
# TIPS MENEMUKAN SELECTOR:
# ============================================================
"""
1. Buka website di browser
2. Klik kanan pada elemen → Inspect
3. Lihat struktur HTML-nya
4. Identifikasi:
   - Container yang membungkus setiap item (article, product, dll)
   - Tag dan class/id dari container
   - Tag dan class/id dari data yang mau diambil

Contoh struktur umum:

<div class="article-card">        ← CONTAINER (selector: "div.article-card")
  <h2>                             ← JUDUL
    <a href="/article">Title</a>   ← LINK
  </h2>
  <span class="date">Dec 15</span> ← TANGGAL
  <p class="summary">...</p>       ← RINGKASAN
  <img src="...">                  ← GAMBAR
</div>

CSS Selector Reference:
- "div.article-card"           → <div class="article-card">
- "h2 > a"                     → <a> yang direct child dari <h2>
- "span.date"                  → <span class="date">
- "#main-content .article"     → class="article" dalam id="main-content"
- "article[data-type='news']"  → <article> dengan attribute data-type="news"
"""
