# Error Handling Guide - Timeouts & Rate Limiting

How the Crawl4AI scraper defends itself against a slow or hostile site, and what to change
when it still struggles.

---

## The failure this is designed around

```
ERROR - Failed to fetch details from https://www.moneycontrol.com/news/...
Page.goto: Timeout 60000ms exceeded
```

Three things cause it:

1. **Slow responses.** The page takes longer than the timeout to load - or the article is
   gone (404 / removed), or the network is bad.

2. **Too many parallel requests.** The naive version of detail fetching looks like this:

   ```python
   # PROBLEM: 20 requests at once
   detail_tasks = [fetch_details(url) for url in all_20_urls]
   await asyncio.gather(*detail_tasks)  # all fire simultaneously
   ```

   The site reads that as bot or DDoS traffic, rate-limits you, and may block your IP for
   a while.

3. **No retry.** One failure means the article is lost, even when a second attempt a
   second later would have worked.

---

## The five defenses in the code

### 1. Generous timeout

```python
result = await crawler.arun(
    url=url,
    page_timeout=120000,          # 120 seconds
    delay_before_return_html=1.0  # settle for 1s before extracting
)
```

120 seconds gives slow pages room to finish. The extra 1-second wait before extraction
makes sure the DOM has settled - Moneycontrol renders parts of the article client-side.

### 2. Concurrency cap via semaphore

```python
semaphore = asyncio.Semaphore(5)  # at most 5 in flight

async def fetch_with_semaphore(article):
    async with semaphore:
        return await fetch_article_details(article['url'])
```

With 20 articles to fetch:

```
No semaphore (bad):
[1][2][3][4][5][6][7][8][9][10][11][12][13][14][15][16][17][18][19][20]
 ^ all at once -> timeouts / rate limit

Semaphore max=5 (good):
Wave 1: [1][2][3][4][5]
Wave 2: [6][7][8][9][10]      (starts as wave 1 slots free up)
Wave 3: [11][12][13][14][15]
Wave 4: [16][17][18][19][20]
```

It is not strictly wave-by-wave - a new request starts the moment any slot frees - but the
ceiling of 5 concurrent holds.

### 3. Retry with exponential backoff

```python
for attempt in range(2):  # max 2 attempts
    try:
        result = await crawler.arun(url, page_timeout=120000)

        if not result.success:
            if attempt < 1:
                wait_time = 2 ** attempt  # 1s, then 2s
                await asyncio.sleep(wait_time)
                continue
            return {'date': '', 'author': '', 'full_content': ''}  # give up

        return extract_data(result)

    except TimeoutError:
        await asyncio.sleep(2 ** attempt)
        continue
```

So a fetch either recovers on the second try, or is abandoned with empty fields:

```
Attempt 1: TIMEOUT -> wait 1s -> Attempt 2: SUCCESS
Attempt 1: TIMEOUT -> wait 1s -> Attempt 2: TIMEOUT -> give up, skip article
```

### 4. Jittered delays

```python
await asyncio.sleep(0.5 + (hash(url) % 10) / 10)  # 0.5 - 1.5s
```

Perfectly regular request timing is one of the easiest bot signals to spot. Varying the gap
makes the traffic look less mechanical. (Note this is derived from the URL hash, not
`random` - it varies between articles but is stable for the same URL.)

### 5. Graceful degradation

```python
details = await asyncio.gather(*tasks, return_exceptions=True)

for article, detail in zip(articles, details):
    if isinstance(detail, dict):
        article['date'] = detail['date']
        article['author'] = detail['author']
    else:
        article['date'] = ''
        article['author'] = ''
        logger.warning(f"Failed: {article['url']}")
```

`return_exceptions=True` is what keeps one bad article from killing the run. If 3 of 20
articles time out, the other 17 still land. Partial success beats total failure.

---

## What to tune

Concurrency is the main dial:

```python
MoneyControlCrawl4AIScraper(max_concurrent=3)   # conservative: slower, safer
MoneyControlCrawl4AIScraper(max_concurrent=5)   # default
MoneyControlCrawl4AIScraper(max_concurrent=10)  # aggressive: faster, riskier
```

Or from the CLI: `--max-concurrent 3`.

| Situation | Setting |
|-----------|---------|
| Slow connection, frequent timeouts | `3` |
| Normal | `5` (default) |
| Fast, stable network | `8` |

The second dial is the pause between list pages - `--delay 3.0`, or:

```python
articles = await scraper.scrape_multiple_pages(num_pages=3, delay=3.0)
```

---

## Design summary

| Aspect | Naive approach | This scraper |
|--------|----------------|--------------|
| Concurrent requests | unlimited | capped at 5 (configurable) |
| Timeout | 60s | 120s |
| Retry | none | 2 attempts with backoff |
| Request spacing | none | 0.5-1.5s jitter |
| On error | crashes the run | logs it, empties the fields, continues |

---

## Reading the logs

A healthy run looks like this:

```
2025-11-07 15:40:00 - INFO - Fetching details for 20 articles (max 5 concurrent)...
2025-11-07 15:40:01 - INFO - Fetching details from: .../article-1 (attempt 1/2)
2025-11-07 15:40:01 - INFO - Fetching details from: .../article-2 (attempt 1/2)
...
2025-11-07 15:40:05 - ERROR - [TIMEOUT] Timeout fetching .../article-3 (attempt 1/2)
2025-11-07 15:40:06 - INFO - Retrying in 1 seconds...
2025-11-07 15:40:10 - ERROR - [TIMEOUT] Timeout fetching .../article-4 (attempt 2/2)
2025-11-07 15:40:10 - WARNING - Failed to fetch details for: .../article-4
2025-11-07 15:40:45 - INFO - [SUCCESS] Successfully fetched details for 19/20 articles
```

Article 3 recovered on its retry. Article 4 exhausted both attempts and was skipped with
empty fields. The run finished anyway - that last line is the one to check.

Useful commands:

```bash
# Follow a run (adjust the category in the filename)
tail -f logs/scraper_markets_crawl4ai.log

# Success vs timeout counts
grep "Successfully fetched" logs/scraper_markets_crawl4ai.log | wc -l
grep "TIMEOUT" logs/scraper_markets_crawl4ai.log | wc -l
```

---

## Tips for avoiding timeouts

1. **Do not go aggressive by default.** `max_concurrent=20` will get you rate-limited;
   5 is the sweet spot.
2. **Add delay between pages** - `--delay 3.0` if you are seeing failures.
3. **Scrape off-peak.** The site responds faster when it is less busy.
4. **Check your own network first** before blaming the scraper:
   ```bash
   ping www.moneycontrol.com
   ```
5. **Watch the logs** for patterns. Every article timing out means something systemic
   (network, block, site change); scattered timeouts are normal and already handled.
