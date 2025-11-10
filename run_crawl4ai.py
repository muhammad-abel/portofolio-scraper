#!/usr/bin/env python3
"""
Quick run script for Crawl4AI scraper
Usage: python run_crawl4ai.py
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
