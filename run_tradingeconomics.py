#!/usr/bin/env python3
"""
Quick run script for TradingEconomics scraper

Usage:
  python run_tradingeconomics.py --country india
  python run_tradingeconomics.py --country india --tabs gdp,labour,prices
  python run_tradingeconomics.py --country india --upload-mongo
  python run_tradingeconomics.py --country india --tabs gdp,labour --upload-mongo

Options:
  --country NAME        Country to scrape (default: india)
  --tabs TAB1,TAB2      Comma-separated tabs to scrape (default: all)
  --upload-mongo        Upload to MongoDB after scraping
  --output-dir DIR      Output directory (default: current directory)

Available tabs:
  overview, gdp, labour, prices, money, trade, government,
  business, consumer, housing, health
"""

import sys
import asyncio
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Import from scrapers package
from scrapers.tradingeconomics.indicators_scraper import main

if __name__ == "__main__":
    asyncio.run(main())
