# Memory Optimization Guide

This guide explains the memory-efficient features available in the scraper and when to use them.

## Table of Contents

- [Why Memory Optimization Matters](#why-memory-optimization-matters)
- [Available Methods](#available-methods)
- [Quick Start](#quick-start)
- [Usage Examples](#usage-examples)
- [Performance Comparison](#performance-comparison)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

---

## Why Memory Optimization Matters

### The Problem

The standard `scrape_multiple_pages()` method accumulates all scraped articles in memory before saving or processing them. This works fine for small scraping jobs but can cause issues for large-scale operations:

**Memory Usage Breakdown:**
```
Standard method scraping 500 pages:
├── Article data: ~50 MB
├── BeautifulSoup objects: ~150 MB
├── Playwright browser: ~100 MB
├── Detail pages (concurrent): ~15 MB
└── Overhead: ~20 MB
───────────────────────────────────
Total: ~335 MB (and growing)
```

### When You Need Memory Optimization

✅ Use memory-efficient methods when:
- Scraping **>100 pages** at once
- Running in **limited memory environments** (containers, cloud functions)
- Scraping **continuously** or in **long-running processes**
- Processing **rich content** with large images/videos
- Running **multiple scrapers** simultaneously

❌ Standard method is fine for:
- Quick tests or prototypes
- Small scraping jobs (<50 pages)
- Systems with abundant RAM (>4 GB available)

---

## Available Methods

### 1. Standard Method (Default)

**Use case:** Small scraping jobs, quick tests

```python
# ⚠️ Accumulates all articles in memory
articles = await scraper.scrape_multiple_pages(num_pages=10)
scraper.save_to_json(articles, "output.json")
```

**Pros:**
- Simple API
- Easy to work with (all data in one list)
- Good for <100 pages

**Cons:**
- High memory usage for large jobs
- Risk of OOM (Out of Memory) errors
- Not suitable for production at scale

---

### 2. Generator Method (Recommended for Large-Scale)

**Use case:** Large scraping jobs, memory-constrained environments

```python
# ✅ Yields articles page by page (memory-efficient)
async for articles in scraper.scrape_pages_generator(num_pages=500):
    # Process each page immediately
    scraper.save_to_json(articles, f"page_{page}.json")
    # Memory is freed after each iteration
```

**Pros:**
- **Constant memory usage** regardless of total pages
- Process data incrementally
- Lowest memory footprint
- Suitable for unlimited pages

**Cons:**
- Slightly more complex API
- Need to handle multiple output files (or use streaming save)

**Memory savings:** ~60-80% compared to standard method

---

### 3. Batched Method (Balance Between Memory & Convenience)

**Use case:** Moderate scraping jobs, batch processing

```python
# ✅ Scrapes in batches of 50 pages
async for batch in scraper.scrape_pages_batched(
    num_pages=500,
    batch_size=50
):
    # Process 50 pages worth of articles at once
    scraper.save_to_json(batch, f"batch_{i}.json")
    # Batch memory is freed after each iteration
```

**Pros:**
- Predictable memory usage
- Balance between efficiency and convenience
- Good for batch processing workflows
- Easier to manage than per-page files

**Cons:**
- Still uses more memory than generator
- Need to choose appropriate batch size

**Memory savings:** ~40-60% compared to standard method

---

### 4. Streaming JSON Save

**Use case:** Saving large datasets without memory accumulation

```python
# ✅ Writes JSON incrementally as data comes in
generator = scraper.scrape_pages_generator(num_pages=500)
await scraper.save_to_json_streaming(generator, "output.json")
# Single output file, minimal memory usage
```

**Pros:**
- Single output file
- Minimal memory usage
- Works seamlessly with generators
- Perfect for large datasets

**Cons:**
- Cannot modify/filter data after writing
- File must be valid JSON (atomic writes)

---

### 5. Streaming MongoDB Upload

**Use case:** Direct database upload for large-scale scraping

```python
# ✅ Uploads in batches as data comes in
from upload_to_mongodb import MongoDBUploader

uploader = MongoDBUploader(...)
uploader.connect()

generator = scraper.scrape_pages_generator(num_pages=1000)
stats = await uploader.upload_articles_streaming_async(
    generator,
    batch_size=100
)
```

**Pros:**
- Direct upload without intermediate files
- Handles deduplication automatically
- Minimal memory usage
- Progress tracking

**Cons:**
- Requires MongoDB connection
- Less control over data flow

---

## Quick Start

### Example 1: Large-Scale Scraping with Generator

```python
#!/usr/bin/env python3
import asyncio
from scrapers.crawl4ai_scraper import MoneyControlCrawl4AIScraper

async def main():
    scraper = MoneyControlCrawl4AIScraper(
        base_url="https://www.moneycontrol.com/news/business/markets/",
        fetch_details=True,
        max_concurrent=5
    )

    # Scrape 500 pages with generator (memory-efficient)
    page_num = 1
    async for articles in scraper.scrape_pages_generator(
        num_pages=500,
        delay=2.0
    ):
        print(f"Page {page_num}: {len(articles)} articles")
        scraper.save_to_json(articles, f"output/page_{page_num}.json")
        page_num += 1

if __name__ == "__main__":
    asyncio.run(main())
```

### Example 2: Batched Scraping with Single Output

```python
#!/usr/bin/env python3
import asyncio
from scrapers.crawl4ai_scraper import MoneyControlCrawl4AIScraper

async def main():
    scraper = MoneyControlCrawl4AIScraper(
        base_url="https://www.moneycontrol.com/news/business/markets/",
        fetch_details=True,
        max_concurrent=5
    )

    # Scrape with batching + streaming save
    generator = scraper.scrape_pages_batched(
        num_pages=500,
        batch_size=50,  # 50 pages per batch
        delay=2.0
    )

    # Save everything to single file with streaming
    await scraper.save_to_json_streaming(generator, "output.json")
    print("Done! All data saved to output.json")

if __name__ == "__main__":
    asyncio.run(main())
```

### Example 3: Direct MongoDB Upload

```python
#!/usr/bin/env python3
import asyncio
from scrapers.crawl4ai_scraper import MoneyControlCrawl4AIScraper
from upload_to_mongodb import MongoDBUploader

async def main():
    # Initialize scraper
    scraper = MoneyControlCrawl4AIScraper(
        base_url="https://www.moneycontrol.com/news/business/markets/",
        fetch_details=True,
        max_concurrent=5
    )

    # Initialize uploader
    uploader = MongoDBUploader(
        connection_string="mongodb://localhost:27017/",
        database_name="moneycontrol_db",
        collection_name="news_articles"
    )

    uploader.connect()
    uploader.create_indexes()

    # Scrape and upload directly (memory-efficient)
    generator = scraper.scrape_pages_generator(
        num_pages=1000,
        delay=2.0
    )

    stats = await uploader.upload_articles_streaming_async(
        generator,
        batch_size=100  # Upload every 100 articles
    )

    print(f"Upload completed!")
    print(f"  Inserted: {stats['inserted']}")
    print(f"  Updated: {stats['updated']}")

    uploader.close()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Performance Comparison

### Memory Usage Comparison

| Method | 10 Pages | 100 Pages | 500 Pages | 1000 Pages |
|--------|----------|-----------|-----------|------------|
| **Standard** | ~50 MB | ~200 MB | ~500 MB | ~1 GB |
| **Generator** | ~50 MB | ~50 MB | ~50 MB | ~50 MB |
| **Batched (50)** | ~50 MB | ~100 MB | ~150 MB | ~150 MB |

### Speed Comparison

All methods have similar scraping speed since they use the same underlying scraping logic. The main difference is memory usage.

**Bottleneck:** Network I/O and website response time (not processing)

---

## Best Practices

### 1. Choose the Right Method

```python
# Small jobs (<50 pages): Use standard
if num_pages < 50:
    articles = await scraper.scrape_multiple_pages(num_pages)

# Medium jobs (50-200 pages): Use batched
elif num_pages < 200:
    async for batch in scraper.scrape_pages_batched(num_pages, batch_size=50):
        process_batch(batch)

# Large jobs (>200 pages): Use generator
else:
    async for articles in scraper.scrape_pages_generator(num_pages):
        process_articles(articles)
```

### 2. Monitor Memory Usage

Use the profiling tool to test before running large jobs:

```bash
# Profile your scraping job
python tools/memory_profiler.py --pages 100 --method compare

# Test with actual parameters
python tools/memory_profiler.py --pages 500 --method generator --category world
```

### 3. Adjust Batch Sizes

For batched method, tune batch size based on available memory:

```python
# Conservative (low memory)
batch_size = 10  # ~50 MB per batch

# Moderate (normal memory)
batch_size = 50  # ~150 MB per batch

# Aggressive (high memory)
batch_size = 100  # ~300 MB per batch
```

### 4. Use Streaming for Large Datasets

Always use streaming save for >100 pages:

```python
# ❌ Don't do this for large datasets
articles = await scraper.scrape_multiple_pages(num_pages=500)
scraper.save_to_json(articles, "output.json")  # Loads all into memory

# ✅ Do this instead
generator = scraper.scrape_pages_generator(num_pages=500)
await scraper.save_to_json_streaming(generator, "output.json")
```

### 5. Clean Up Explicitly (Optional)

Python's garbage collector handles this, but you can be explicit:

```python
async for articles in scraper.scrape_pages_generator(num_pages=100):
    process_articles(articles)
    del articles  # Explicitly free memory (optional)
```

---

## Troubleshooting

### Issue: Still Running Out of Memory

**Possible causes:**
1. Batch size too large
2. Too many concurrent detail requests
3. Browser accumulating memory

**Solutions:**
```python
# Reduce batch size
scraper.scrape_pages_batched(num_pages=500, batch_size=10)  # Lower

# Reduce concurrency
scraper = MoneyControlCrawl4AIScraper(max_concurrent=3)  # Lower

# Add delay
scraper.scrape_pages_generator(num_pages=500, delay=3.0)  # Higher
```

### Issue: Memory Not Being Freed

**Cause:** Python garbage collector hasn't run yet

**Solution:**
```python
import gc

async for articles in scraper.scrape_pages_generator(num_pages=100):
    process_articles(articles)
    del articles
    gc.collect()  # Force garbage collection
```

### Issue: Slow Performance

**Cause:** Delay or concurrency settings

**Solution:**
```python
# Increase concurrency (use with caution)
scraper = MoneyControlCrawl4AIScraper(max_concurrent=10)

# Reduce delay (be respectful to target site)
scraper.scrape_pages_generator(num_pages=100, delay=1.0)
```

### Issue: Incomplete Data

**Cause:** Not consuming entire generator

**Solution:**
```python
# ❌ Don't break early without processing all
async for articles in scraper.scrape_pages_generator(num_pages=100):
    if some_condition:
        break  # Generator stops, some pages not scraped

# ✅ Either consume all or track progress
pages_scraped = 0
async for articles in scraper.scrape_pages_generator(num_pages=100):
    process_articles(articles)
    pages_scraped += 1
    print(f"Progress: {pages_scraped}/100")
```

---

## Command-Line Usage

The scrapers don't have built-in CLI flags for memory-efficient methods yet, but you can use the profiler:

```bash
# Profile different methods
python tools/memory_profiler.py --pages 50 --method compare

# Test generator method
python tools/memory_profiler.py --pages 200 --method generator --no-details

# Test batched method with custom batch size
python tools/memory_profiler.py --pages 500 --method batched --batch-size 25
```

---

## Migration Guide

### Migrating from Standard to Generator

**Before:**
```python
# Old code
articles = await scraper.scrape_multiple_pages(num_pages=500)
scraper.save_to_json(articles, "output.json")
```

**After:**
```python
# New code (memory-efficient)
generator = scraper.scrape_pages_generator(num_pages=500)
await scraper.save_to_json_streaming(generator, "output.json")
```

### Migrating from Standard to Batched

**Before:**
```python
# Old code
articles = await scraper.scrape_multiple_pages(num_pages=500)
process_articles(articles)
```

**After:**
```python
# New code (memory-efficient with batching)
async for batch in scraper.scrape_pages_batched(num_pages=500, batch_size=50):
    process_articles(batch)
```

---

## Further Reading

- [SCRAPING_GUIDE.md](SCRAPING_GUIDE.md) - General scraping guide
- [ERROR_HANDLING_GUIDE.md](ERROR_HANDLING_GUIDE.md) - Error handling best practices
- [README.md](../README.md) - Main documentation

---

## Questions?

If you encounter issues or have questions:

1. Check the troubleshooting section above
2. Run the memory profiler to diagnose issues
3. Review your scraping logs for errors
4. Consider reducing concurrency/batch size

Happy scraping! 🚀
