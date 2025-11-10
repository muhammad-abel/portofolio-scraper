#!/usr/bin/env python3
"""
Quick run script for Requests scraper
Usage: python run_requests.py
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Import from scrapers package
from scrapers.requests_scraper import main

if __name__ == "__main__":
    main()
