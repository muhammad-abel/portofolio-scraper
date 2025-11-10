#!/usr/bin/env python3
"""
Quick run script for Crawl4AI scraper

Usage:
  python run_crawl4ai.py
  python run_crawl4ai.py --pages 5
  python run_crawl4ai.py --pages 10 --upload-mongo
  python run_crawl4ai.py --pages 3 --max-concurrent 3 --upload-mongo

Options:
  --pages N             Number of pages to scrape (default: 3)
  --max-concurrent N    Max concurrent requests (default: 5)
  --delay SECONDS       Delay between pages (default: 2.0)
  --upload-mongo        Upload to MongoDB after scraping
  --no-details          Skip fetching full article details
"""

import sys
import asyncio
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Import from scrapers package
from scrapers.crawl4ai_scraper import main

if __name__ == "__main__":
    asyncio.run(main())
