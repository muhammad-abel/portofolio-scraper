# Web Scraping Guide

Background on how the scraping in this project works, and how to fix the selectors when
Moneycontrol changes its HTML (it will, eventually).

---

## How scraping works

```
   +-------------+
   |   Website   |   1. Send an HTTP request
   +------+------+
          |
          v
   +-------------+
   |  HTML Code  |   2. Receive the HTML response
   +------+------+
          |
          v
   +--------------+
   | BeautifulSoup|  3. Parse the HTML into a tree
   +------+-------+
          |
          v
   +--------------+
   | Find Elements|  4. Locate elements with selectors
   +------+-------+
          |
          v
   +--------------+
   | Extract Data |  5. Pull out text / attributes
   +------+-------+
          |
          v
   +--------------+
   |  Save Data   |  6. Write to JSON / CSV / MongoDB
   +--------------+
```

Steps 1 and 2 are where the scrapers differ. `requests_scraper` does a plain HTTP GET and
gets whatever HTML the server sends. `playwright_scraper` and the Crawl4AI scrapers drive a
real Chromium browser, so JavaScript runs and client-rendered content actually exists by the
time you parse it. Steps 3-6 are identical everywhere - BeautifulSoup with `lxml`.

---

## The selectors this project uses

If a run suddenly returns zero articles, or every `author` comes back empty, one of these
stopped matching. They live in `extract_article_data()` and `fetch_article_details()` in
`scrapers/crawl4ai_scraper.py`.

**List page** (`https://www.moneycontrol.com/news/business/markets/page-N/`):

| Data | Selector | Notes |
|------|----------|-------|
| Article container | `li.clearfix` | Falls back to `div.article`, `article`, then any `li` |
| Link + title | `a.unified-link` (or first `a`), title from the `h2` inside it | |
| Image | `img` inside the link | Tries `src`, then `data-src` (lazy loading), then `data` |
| Summary | first `p` in the container | Sibling of the `a`, not inside it |

**Detail page** (the individual article):

| Data | Selector | Fallback |
|------|----------|----------|
| Author | `div.article_author > a` | The div's own text if there is no `<a>` |
| Date | `div.article_schedule > span` | `p[class*=date]`, splitting off the time after `.` |
| Full content | `div#contentdata.content_wrapper.arti-flow`, all `p` inside | `div.video_content > p.text_3` |
| Date (video format) | - | `div.video_content > p.last_updated` |

The video fallbacks exist because some Moneycontrol articles are video posts with a
completely different layout. That is also why an empty `author` is common rather than a
bug - video articles frequently have no byline at all.

---

## Finding the data you want

### Step 1: Inspect the element

1. Open the target page in Chrome or Firefox
2. Right-click the element you want
3. Choose **Inspect**, or press `F12`
4. Read the HTML structure in DevTools

For example, right-clicking a headline might reveal:

```html
<h2 class="article-title">
  <a href="/news/123">The headline text</a>
</h2>
```

### Step 2: Identify the pattern

Look for something **consistent** across every item.

A **container** wraps each record:

```html
<div class="news-item">    <- container
  <h2>...</h2>             <- title
  <span>...</span>         <- date
  <p>...</p>               <- description
</div>
```

An **identifier** - a class or id - tells you what each piece is:

- `class="news-item"` -> the container
- `class="article-title"` -> the title
- `class="publish-date"` -> the date

Prefer semantic-looking classes over generated ones. A class like `css-1x9fj2k` is a
build artifact and will change on the site's next deploy.

### Step 3: Write the selector

```python
# By tag
soup.find('h2')                     # first <h2>
soup.find_all('p')                  # every <p>

# By class
soup.find('div', class_='news-item')
soup.find_all('span', class_='date')

# By id
soup.find('div', id='main-content')

# By attribute
soup.find('a', {'data-type': 'article'})

# CSS selectors
soup.select('div.news-item')        # tag with class
soup.select('#main h2')             # h2 anywhere inside #main
soup.select('h2 > a')               # a that is a direct child of h2
soup.select('[data-type="news"]')   # by attribute
```

---

## CSS selector cheat sheet

| Selector | Example | Matches |
|----------|---------|---------|
| `.class` | `.news-item` | Elements with `class="news-item"` |
| `#id` | `#header` | The element with `id="header"` |
| `tag` | `div` | Every `<div>` |
| `tag.class` | `div.article` | `<div>` with class `article` |
| `tag#id` | `div#main` | `<div>` with id `main` |
| `parent > child` | `div > p` | `<p>` that is a direct child of a `<div>` |
| `ancestor descendant` | `div p` | Every `<p>` anywhere inside a `<div>` |
| `[attribute]` | `[data-id]` | Elements having a `data-id` attribute |
| `[attribute="value"]` | `[type="text"]` | Elements with `type="text"` |

---

## Common patterns

### News articles

```python
from bs4 import BeautifulSoup
import requests

response = requests.get("https://example.com/news")
soup = BeautifulSoup(response.content, 'lxml')

for article in soup.find_all('div', class_='article'):
    title_elem = article.find('h2')
    title = title_elem.get_text(strip=True) if title_elem else ''

    link_elem = article.find('a')
    link = link_elem.get('href', '') if link_elem else ''

    date_elem = article.find('span', class_='date')
    date = date_elem.get_text(strip=True) if date_elem else ''

    print(f"{title} - {date}\n{link}\n")
```

### Product listings

```python
for product in soup.find_all('div', class_='product-card'):
    name = product.find('h3', class_='product-name').get_text(strip=True)
    price = product.find('span', class_='price').get_text(strip=True)

    rating_elem = product.find('div', class_='rating')
    rating = rating_elem.get('data-rating', '') if rating_elem else ''

    print(f"{name} - {price} - {rating}")
```

### Tables

```python
table = soup.find('table', class_='data-table')

data = []
for row in table.find_all('tr')[1:]:  # skip the header row
    cols = row.find_all('td')
    if len(cols) >= 3:
        data.append({
            'col1': cols[0].get_text(strip=True),
            'col2': cols[1].get_text(strip=True),
            'col3': cols[2].get_text(strip=True),
        })
```

### Pagination

```python
import time

all_data = []
for page in range(1, 6):
    response = requests.get(f"https://example.com/news/page-{page}")
    soup = BeautifulSoup(response.content, 'lxml')

    for article in soup.find_all('div', class_='article'):
        all_data.append(extract(article))

    time.sleep(2)  # be polite
```

This is exactly the shape of `scrape_multiple_pages()` - Moneycontrol paginates as
`page-1/`, `page-2/`, and so on, which is why the URL can just be built by string
formatting.

---

## Debugging

### Print the structure

```python
print(article_elem.prettify())   # the element's HTML
print(article_elem.get('class')) # its classes
print(article_elem.attrs)        # every attribute
```

### Always check before extracting

```python
# BAD - AttributeError the moment the element is missing
title = article.find('h2').get_text()

# GOOD
title_elem = article.find('h2')
title = title_elem.get_text(strip=True) if title_elem else ''
```

This is the single most common scraping bug, and it is why every extraction in this project
uses the `if elem else ''` pattern. Missing elements are normal, not exceptional.

### Test selectors in the browser console

DevTools -> Console:

```javascript
document.querySelectorAll('div.article')          // how many match?
document.querySelector('h2.title').textContent    // what is inside?
```

This is far faster than re-running the scraper to test a guess.

---

## Common errors

### `AttributeError: 'NoneType' object has no attribute 'get_text'`

The element was not found, so `find()` returned `None`. Guard it:

```python
elem = soup.find('h2')
text = elem.get_text() if elem else ''
```

### Nothing gets scraped

Either the selector is wrong or the site renders with JavaScript. Diagnose:

```python
containers = soup.find_all('div', class_='article')
print(f"Found {len(containers)} containers")
if not containers:
    print(soup.prettify()[:1000])  # what did we actually get?
```

If the HTML looks like an empty shell, the content is JavaScript-rendered - use the
Crawl4AI or Playwright scraper rather than `requests`.

### Some fields are empty

The HTML structure varies between items. Chain fallbacks:

```python
date_elem = (
    article.find('span', class_='date') or
    article.find('time') or
    article.find('span', class_='publish-date')
)
```

That `or` chain is the pattern used throughout this project's extractors.

---

## Practice

Open https://news.ycombinator.com, inspect a headline, and try to extract all of them:

```python
response = requests.get('https://news.ycombinator.com')
soup = BeautifulSoup(response.content, 'lxml')

for title in soup.select('span.titleline > a'):
    print(title.get_text())
```

Static HTML, clean markup, no JavaScript required - a good first target.

---

## Resources

- BeautifulSoup docs: https://www.crummy.com/software/BeautifulSoup/bs4/doc/
- CSS selector reference: https://www.w3schools.com/cssref/css_selectors.asp
- Regex tester (for cleaning extracted text): https://regex101.com/

---

Test against a single page before scaling up. Respect `robots.txt` and rate limits.
