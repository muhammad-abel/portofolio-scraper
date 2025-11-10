#!/usr/bin/env python3
"""
Quick run script for Playwright scraper
Usage: python run_playwright.py
"""

import sys
import asyncio
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Import from scrapers package
from scrapers.playwright_scraper import main

if __name__ == "__main__":
    asyncio.run(main())
