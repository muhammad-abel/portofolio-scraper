#!/usr/bin/env python3
"""
Quick run script for Screener.in scraper

Usage:
  # Scrape all Nifty 100 stocks
  python run_screener.py

  # Scrape specific stocks
  python run_screener.py --symbols HDFCBANK,TCS,RELIANCE

  # Use generator method (memory-efficient)
  python run_screener.py --method generator

  # Custom batch size
  python run_screener.py --batch-size 20 --delay 2.5

Options:
  --symbols-file PATH      JSON file with stock symbols (default: data/nifty100_symbols.json)
  --symbols LIST           Comma-separated symbols
  --method METHOD          Scraping method: standard, generator, batched (default: batched)
  --batch-size N           Batch size for batched method (default: 10)
  --delay SECONDS          Delay between stocks (default: 3.0)
  --output PATH            Output JSON file (default: screener_stocks.json)
"""

import sys
import asyncio
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Import from scrapers package
from scrapers.screener.screener_scraper import main

if __name__ == "__main__":
    asyncio.run(main())
