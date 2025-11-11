"""
Screener.in Scraper Package

Scraper for fundamental data from screener.in including:
- Stock fundamentals (P/E, P/B, ROE, ROCE, etc.)
- Shareholding patterns (Promoter, FII, DII holdings)
- Quarterly financial results
"""

from .screener_scraper import ScreenerScraper

__all__ = ['ScreenerScraper']
