#!/usr/bin/env python3
"""
Screener.in Stock Data Scraper (Crawl4AI version)

Scrapes fundamental data, shareholding patterns, and quarterly results
for Nifty 100 stocks from screener.in

Features:
- Stock fundamentals (P/E, P/B, ROE, ROCE, etc.)
- Shareholding patterns (Promoter, FII, DII holdings)
- Quarterly results (Revenue, Profit, EPS growth)
- Memory-efficient generator pattern
- Rate limiting and error handling
"""

import asyncio
import os
import sys
import hashlib
import base64
from pathlib import Path
from crawl4ai import AsyncWebCrawler
from bs4 import BeautifulSoup
import pandas as pd
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional, AsyncIterator
import argparse
import re
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Optional MongoDB support
try:
    from pymongo import MongoClient, UpdateOne
    from pymongo.errors import BulkWriteError, ConnectionFailure
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False

# Logger will be configured in main()
logger = None


class ScreenerScraper:
    """Scraper for screener.in stock data"""

    def __init__(self, delay: float = 3.0, max_retries: int = 2):
        """
        Initialize the Screener scraper

        Args:
            delay: Delay between requests in seconds (default: 3.0)
            max_retries: Maximum retries on failure (default: 2)
        """
        self.base_url = "https://www.screener.in"
        self.delay = delay
        self.max_retries = max_retries

    @staticmethod
    def generate_stock_hash(symbol: str, date: str = "") -> str:
        """
        Generate unique hash for stock data

        Args:
            symbol: Stock symbol
            date: Optional date for time-series data

        Returns:
            Base64 encoded hash string
        """
        combined = f"{symbol.upper()}|{date}|{datetime.now().strftime('%Y-%m-%d')}"
        hash_object = hashlib.sha256(combined.encode('utf-8'))
        base64_hash = base64.b64encode(hash_object.digest()).decode('utf-8')
        return base64_hash

    def clean_number(self, value: str) -> Optional[float]:
        """
        Clean and convert string number to float

        Args:
            value: String value (e.g., "1,234.56", "12.5%", "15.2 Cr")

        Returns:
            Float value or None if invalid
        """
        if not value or value.strip() in ['', '-', 'N/A', 'NA']:
            return None

        try:
            # Remove common suffixes and special characters
            value = value.strip()
            value = value.replace(',', '')
            value = value.replace('%', '')
            value = value.replace('₹', '')

            # Handle Cr (crores), Lac, etc.
            multiplier = 1
            if 'Cr' in value or 'cr' in value:
                multiplier = 10000000  # 1 crore = 10 million
                value = value.replace('Cr', '').replace('cr', '')
            elif 'Lac' in value or 'lac' in value:
                multiplier = 100000  # 1 lac = 100,000
                value = value.replace('Lac', '').replace('lac', '')

            value = value.strip()
            return float(value) * multiplier
        except (ValueError, AttributeError):
            return None

    def _extract_table_raw(self, table_element) -> Dict:
        """
        Extract table data in dict-by-date format for RAG-friendly structure

        This method transforms financial tables into a date-keyed dictionary
        where each date maps to all metrics for that period.

        Args:
            table_element: BeautifulSoup table element

        Returns:
            Dict where keys are dates/quarters and values are metric dicts
            Example: {
                "Sep 2024": {"revenue": "83,002", "profit": "18,627"},
                "Jun 2024": {"revenue": "81,546", "profit": "17,188"}
            }
        """
        result = {}

        try:
            # Extract headers (dates/quarters)
            headers = []
            thead = table_element.find('thead')
            if thead:
                header_row = thead.find('tr')
                if header_row:
                    headers = [h.get_text(strip=True) for h in header_row.find_all(['th', 'td'])]

            # Skip first header (metric name column)
            date_headers = headers[1:] if len(headers) > 1 else []

            # Initialize dict for each date
            for date in date_headers:
                if date:  # Skip empty headers
                    result[date] = {}

            # Extract rows (metrics)
            tbody = table_element.find('tbody')
            if tbody:
                rows = tbody.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if cells and len(cells) > 0:
                        metric_label = cells[0].get_text(strip=True)

                        # Skip empty labels
                        if not metric_label:
                            continue

                        # Convert label to snake_case key
                        metric_key = metric_label.lower()
                        metric_key = metric_key.replace('+', '')
                        metric_key = metric_key.replace('%', '_percent')
                        metric_key = metric_key.replace('/', '_')
                        metric_key = re.sub(r'\s+', '_', metric_key)  # Replace spaces with underscore
                        metric_key = re.sub(r'_+', '_', metric_key)   # Remove duplicate underscores
                        metric_key = metric_key.strip('_')             # Remove leading/trailing underscores

                        # Assign values to each date
                        for i, cell in enumerate(cells[1:]):
                            if i < len(date_headers) and date_headers[i]:
                                value = cell.get_text(strip=True)
                                result[date_headers[i]][metric_key] = value

        except Exception as e:
            logger.debug(f"Error extracting raw table: {e}")

        return result

    def _extract_fundamentals_raw(self, soup: BeautifulSoup) -> List[Dict]:
        """
        Extract all fundamental metrics as-is (raw data)

        Returns:
            List of {metric, value} pairs
        """
        fundamentals_raw = []

        try:
            # Find all ratio/metric items (usually in list format)
            ratio_items = soup.find_all('li', class_='flex')

            for item in ratio_items:
                spans = item.find_all('span')
                if len(spans) >= 2:
                    metric = spans[0].get_text(strip=True)
                    value = spans[1].get_text(strip=True)

                    fundamentals_raw.append({
                        "metric": metric,
                        "value": value
                    })

            # Alternative: Extract from top section with IDs
            for metric_id in ['pe', 'pb', 'marketcap', 'roe', 'roce', 'bookvalue']:
                elem = soup.find(id=metric_id)
                if elem:
                    # Try to find label
                    parent = elem.find_parent()
                    label_elem = parent.find('span', class_='name') if parent else None
                    label = label_elem.get_text(strip=True) if label_elem else metric_id.upper()

                    value = elem.get_text(strip=True)

                    # Avoid duplicates
                    if not any(f['metric'].lower() == label.lower() for f in fundamentals_raw):
                        fundamentals_raw.append({
                            "metric": label,
                            "value": value
                        })

        except Exception as e:
            logger.debug(f"Error extracting raw fundamentals: {e}")

        return fundamentals_raw

    async def scrape_stock(self, symbol: str, crawler: AsyncWebCrawler) -> Optional[Dict]:
        """
        Scrape all data for a single stock

        Args:
            symbol: Stock symbol (e.g., "HDFCBANK")
            crawler: AsyncWebCrawler instance

        Returns:
            Dictionary with stock data or None on failure
        """
        url = f"{self.base_url}/company/{symbol}/consolidated/"

        for attempt in range(self.max_retries):
            try:
                logger.info(f"Scraping {symbol} (attempt {attempt + 1}/{self.max_retries})")

                result = await crawler.arun(
                    url=url,
                    word_count_threshold=10,
                    bypass_cache=True,
                    wait_for="body",
                    page_timeout=60000,
                    delay_before_return_html=2.0
                )

                if not result.success:
                    logger.error(f"Failed to fetch {symbol}: {result.error_message}")
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    return None

                soup = BeautifulSoup(result.html, 'lxml')

                # Check if page exists (404 check)
                if "Page not found" in result.html or not soup.find('h1'):
                    logger.warning(f"Stock page not found for {symbol}")
                    return None

                # Extract all data
                stock_data = {
                    'symbol': symbol,
                    'scraped_at': datetime.now().isoformat(),
                    'url': url,
                    'hash': self.generate_stock_hash(symbol)
                }

                # Extract basic info
                basic_info = self._extract_basic_info(soup, symbol)
                stock_data.update(basic_info)

                # ====================
                # COMPUTED FIELDS (Quick Access)
                # ====================
                stock_data['summary'] = {}

                # Computed fundamentals
                fundamentals_computed = self._extract_fundamentals(soup)
                stock_data['summary']['fundamentals'] = fundamentals_computed

                # Computed shareholding
                shareholding_computed = self._extract_shareholding(soup)
                if shareholding_computed:
                    stock_data['summary']['latest_shareholding'] = {
                        'quarter': shareholding_computed.get('latest_quarter'),
                        'promoter': shareholding_computed.get('promoter'),
                        'fii': shareholding_computed.get('fii'),
                        'dii': shareholding_computed.get('dii'),
                        'public': shareholding_computed.get('public'),
                        'fii_change_qoq': shareholding_computed.get('fii_change_qoq'),
                        'dii_change_qoq': shareholding_computed.get('dii_change_qoq'),
                        'promoter_change_qoq': shareholding_computed.get('promoter_change_qoq')
                    }

                # Computed quarterly results
                quarterly_computed = self._extract_quarterly_results(soup)
                if quarterly_computed and len(quarterly_computed) > 0:
                    latest_quarter = quarterly_computed[0]
                    stock_data['summary']['latest_quarter'] = {
                        'quarter': latest_quarter.get('quarter'),
                        'revenue': latest_quarter.get('revenue'),
                        'profit': latest_quarter.get('profit'),
                        'eps': latest_quarter.get('eps'),
                        'revenue_growth_yoy': latest_quarter.get('revenue_growth_yoy'),
                        'profit_growth_yoy': latest_quarter.get('profit_growth_yoy')
                    }

                # ====================
                # RAW DATA (Complete Tables)
                # ====================

                # Raw fundamentals
                stock_data['fundamentals_raw'] = self._extract_fundamentals_raw(soup)

                # Raw shareholding table
                shareholding_section = soup.find('section', id='shareholding')
                if shareholding_section:
                    shareholding_table = shareholding_section.find('table')
                    if shareholding_table:
                        stock_data['shareholding_raw'] = self._extract_table_raw(shareholding_table)
                        # Also keep historical data from computed version
                        if shareholding_computed and 'historical' in shareholding_computed:
                            stock_data['summary']['shareholding_historical'] = shareholding_computed['historical']

                # Raw quarterly results table
                quarters_section = soup.find('section', id='quarters')
                if quarters_section:
                    quarters_table = quarters_section.find('table')
                    if quarters_table:
                        stock_data['quarterly_results_raw'] = self._extract_table_raw(quarters_table)

                # Raw profit & loss table
                profit_loss_section = soup.find('section', id='profit-loss')
                if profit_loss_section:
                    profit_loss_table = profit_loss_section.find('table')
                    if profit_loss_table:
                        stock_data['profit_loss_raw'] = self._extract_table_raw(profit_loss_table)

                # Raw balance sheet table
                balance_sheet_section = soup.find('section', id='balance-sheet')
                if balance_sheet_section:
                    balance_sheet_table = balance_sheet_section.find('table')
                    if balance_sheet_table:
                        stock_data['balance_sheet_raw'] = self._extract_table_raw(balance_sheet_table)

                # Raw cash flow table
                cash_flow_section = soup.find('section', id='cash-flow')
                if cash_flow_section:
                    cash_flow_table = cash_flow_section.find('table')
                    if cash_flow_table:
                        stock_data['cash_flow_raw'] = self._extract_table_raw(cash_flow_table)

                logger.info(f"[SUCCESS] Scraped {symbol} with raw + computed data")
                return stock_data

            except asyncio.TimeoutError:
                logger.error(f"[TIMEOUT] Timeout scraping {symbol} (attempt {attempt + 1}/{self.max_retries})")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                return None

            except Exception as e:
                logger.error(f"[ERROR] Error scraping {symbol} (attempt {attempt + 1}/{self.max_retries}): {str(e)}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                return None

        return None

    def _extract_basic_info(self, soup: BeautifulSoup, symbol: str) -> Dict:
        """Extract basic stock information"""
        data = {}

        try:
            # Company name
            name_elem = soup.find('h1')
            if name_elem:
                data['name'] = name_elem.get_text(strip=True)

            # Current price
            price_elem = soup.find('span', class_='number')
            if price_elem:
                data['current_price'] = self.clean_number(price_elem.get_text(strip=True))

            # Sector/Industry
            # Try to find from breadcrumb or other location
            sector_elem = soup.find('a', href=re.compile('/screens/'))
            if sector_elem:
                data['sector'] = sector_elem.get_text(strip=True)

        except Exception as e:
            logger.debug(f"Error extracting basic info: {e}")

        return data

    def _extract_fundamentals(self, soup: BeautifulSoup) -> Dict:
        """Extract fundamental ratios and metrics"""
        data = {}

        try:
            # Find the ratios section - usually in top section or right sidebar
            # Screener.in uses specific structure with labels and values

            # Method 1: Try to find from list items with specific format
            ratio_items = soup.find_all('li', class_='flex')

            for item in ratio_items:
                # Each item usually has span for name and span for value
                spans = item.find_all('span')
                if len(spans) >= 2:
                    label = spans[0].get_text(strip=True).lower()
                    value_text = spans[1].get_text(strip=True)
                    value = self.clean_number(value_text)

                    # Map labels to our keys
                    if 'market cap' in label:
                        data['market_cap'] = value
                    elif 'stock p/e' in label or label == 'p/e':
                        data['pe_ratio'] = value
                    elif 'price to book' in label or 'p/b' in label:
                        data['pb_ratio'] = value
                    elif 'dividend yield' in label:
                        data['dividend_yield'] = value
                    elif 'roce' in label:
                        data['roce'] = value
                    elif 'roe' in label:
                        data['roe'] = value
                    elif 'debt to equity' in label:
                        data['debt_to_equity'] = value
                    elif 'current ratio' in label:
                        data['current_ratio'] = value
                    elif 'sales growth' in label:
                        data['sales_growth'] = value
                    elif 'profit growth' in label:
                        data['profit_growth'] = value

            # Method 2: Try from top section with IDs
            # Screener often uses specific IDs for key metrics
            for metric_id, key in [
                ('pe', 'pe_ratio'),
                ('pb', 'pb_ratio'),
                ('marketcap', 'market_cap'),
                ('roe', 'roe'),
                ('roce', 'roce')
            ]:
                elem = soup.find(id=metric_id)
                if elem:
                    value = self.clean_number(elem.get_text(strip=True))
                    if value is not None:
                        data[key] = value

        except Exception as e:
            logger.debug(f"Error extracting fundamentals: {e}")

        return data

    def _extract_shareholding(self, soup: BeautifulSoup) -> Dict:
        """
        Extract shareholding patterns (Promoter, FII, DII)

        This is the MOST IMPORTANT data from screener.in!
        """
        shareholding_data = {}

        try:
            # Find shareholding pattern section
            # Usually in a table with specific headers
            shareholding_section = soup.find('section', id='shareholding')

            if shareholding_section:
                # Find the table with shareholding data
                table = shareholding_section.find('table')

                if table:
                    # Parse table headers to find quarter columns
                    headers = []
                    header_row = table.find('thead')
                    if header_row:
                        headers = [th.get_text(strip=True) for th in header_row.find_all('th')]

                    # Parse rows
                    rows = table.find('tbody').find_all('tr') if table.find('tbody') else []

                    quarterly_data = []

                    for row in rows:
                        cells = row.find_all('td')
                        if not cells:
                            continue

                        # First cell is usually the holder type
                        holder_type = cells[0].get_text(strip=True).lower()

                        # Subsequent cells are quarterly values
                        for i, cell in enumerate(cells[1:], 1):
                            value = self.clean_number(cell.get_text(strip=True))

                            if i < len(headers):
                                quarter = headers[i]

                                # Initialize quarter data if not exists
                                if len(quarterly_data) < i:
                                    quarterly_data.append({
                                        'quarter': quarter,
                                        'promoter': None,
                                        'fii': None,
                                        'dii': None,
                                        'public': None
                                    })

                                # Map holder type to our keys
                                if 'promoter' in holder_type:
                                    quarterly_data[i-1]['promoter'] = value
                                elif 'fii' in holder_type or 'foreign' in holder_type:
                                    quarterly_data[i-1]['fii'] = value
                                elif 'dii' in holder_type or 'domestic' in holder_type or 'institution' in holder_type:
                                    quarterly_data[i-1]['dii'] = value
                                elif 'public' in holder_type:
                                    quarterly_data[i-1]['public'] = value

                    # Get latest quarter data
                    if quarterly_data:
                        latest = quarterly_data[0]
                        shareholding_data['latest_quarter'] = latest['quarter']
                        shareholding_data['promoter'] = latest['promoter']
                        shareholding_data['fii'] = latest['fii']
                        shareholding_data['dii'] = latest['dii']
                        shareholding_data['public'] = latest['public']

                        # Calculate QoQ changes if we have previous quarter
                        if len(quarterly_data) > 1:
                            prev = quarterly_data[1]
                            if latest['fii'] is not None and prev['fii'] is not None:
                                shareholding_data['fii_change_qoq'] = round(latest['fii'] - prev['fii'], 2)
                            if latest['dii'] is not None and prev['dii'] is not None:
                                shareholding_data['dii_change_qoq'] = round(latest['dii'] - prev['dii'], 2)
                            if latest['promoter'] is not None and prev['promoter'] is not None:
                                shareholding_data['promoter_change_qoq'] = round(latest['promoter'] - prev['promoter'], 2)

                        # Store historical data
                        shareholding_data['historical'] = quarterly_data

        except Exception as e:
            logger.debug(f"Error extracting shareholding: {e}")

        return shareholding_data

    def _extract_quarterly_results(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract quarterly financial results"""
        quarterly_data = []

        try:
            # Find quarterly results section
            quarters_section = soup.find('section', id='quarters')

            if quarters_section:
                # Find the table
                table = quarters_section.find('table')

                if table:
                    # Parse headers (quarters)
                    headers = []
                    header_row = table.find('thead')
                    if header_row:
                        headers = [th.get_text(strip=True) for th in header_row.find_all('th')]

                    # Parse rows (metrics)
                    rows = table.find('tbody').find_all('tr') if table.find('tbody') else []

                    # Initialize data structure for each quarter
                    for i, quarter in enumerate(headers[1:], 0):  # Skip first header (metric name)
                        quarterly_data.append({
                            'quarter': quarter,
                            'revenue': None,
                            'profit': None,
                            'eps': None,
                            'revenue_growth_yoy': None,
                            'profit_growth_yoy': None
                        })

                    # Extract data from rows
                    for row in rows:
                        cells = row.find_all('td')
                        if not cells:
                            continue

                        metric_name = cells[0].get_text(strip=True).lower()

                        # Map metric to our keys
                        metric_key = None
                        if 'sales' in metric_name or 'revenue' in metric_name:
                            metric_key = 'revenue'
                        elif 'net profit' in metric_name or 'profit' in metric_name:
                            metric_key = 'profit'
                        elif 'eps' in metric_name:
                            metric_key = 'eps'
                        elif 'sales growth' in metric_name:
                            metric_key = 'revenue_growth_yoy'
                        elif 'profit growth' in metric_name:
                            metric_key = 'profit_growth_yoy'

                        if metric_key:
                            for i, cell in enumerate(cells[1:]):
                                value = self.clean_number(cell.get_text(strip=True))
                                if i < len(quarterly_data):
                                    quarterly_data[i][metric_key] = value

        except Exception as e:
            logger.debug(f"Error extracting quarterly results: {e}")

        return quarterly_data

    async def scrape_stocks_generator(
        self,
        symbols: List[str],
        delay: Optional[float] = None
    ) -> AsyncIterator[Dict]:
        """
        Memory-efficient generator that yields stock data one by one

        Args:
            symbols: List of stock symbols
            delay: Delay between stocks (default: use self.delay)

        Yields:
            Dictionary with stock data for each symbol
        """
        delay = delay or self.delay

        async with AsyncWebCrawler(verbose=True) as crawler:
            for i, symbol in enumerate(symbols, 1):
                logger.info(f"[GENERATOR] Processing {i}/{len(symbols)}: {symbol}")

                stock_data = await self.scrape_stock(symbol, crawler)

                if stock_data:
                    yield stock_data
                else:
                    logger.warning(f"[GENERATOR] Failed to scrape {symbol}")

                # Delay between stocks
                if i < len(symbols):
                    logger.debug(f"Waiting {delay} seconds before next stock...")
                    await asyncio.sleep(delay)

        logger.info(f"[GENERATOR] Completed scraping {len(symbols)} symbols")

    async def scrape_stocks_batched(
        self,
        symbols: List[str],
        batch_size: int = 10,
        delay: Optional[float] = None
    ) -> AsyncIterator[List[Dict]]:
        """
        Memory-efficient batched scraping

        Args:
            symbols: List of stock symbols
            batch_size: Number of stocks per batch
            delay: Delay between stocks

        Yields:
            List of stock data dictionaries for each batch
        """
        delay = delay or self.delay
        batch_data = []

        async with AsyncWebCrawler(verbose=True) as crawler:
            for i, symbol in enumerate(symbols, 1):
                logger.info(f"[BATCH] Processing {i}/{len(symbols)}: {symbol}")

                stock_data = await self.scrape_stock(symbol, crawler)

                if stock_data:
                    batch_data.append(stock_data)

                # Yield batch when full or at last symbol
                if len(batch_data) >= batch_size or i == len(symbols):
                    if batch_data:
                        logger.info(f"[BATCH] Yielding batch with {len(batch_data)} stocks")
                        yield batch_data
                        batch_data = []

                # Delay between stocks
                if i < len(symbols):
                    await asyncio.sleep(delay)

        logger.info(f"[BATCH] Completed batched scraping")

    def save_to_json(self, data: List[Dict], filename: str):
        """Save stock data to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved {len(data)} stocks to {filename}")
        except Exception as e:
            logger.error(f"Error saving to JSON: {str(e)}")

    async def save_to_json_streaming(
        self,
        data_async_iterator: AsyncIterator,
        filename: str
    ):
        """Save stock data to JSON using streaming"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write('[\n')

                first = True
                total = 0

                async for stock_data in data_async_iterator:
                    if not first:
                        f.write(',\n')
                    first = False

                    json_str = json.dumps(stock_data, ensure_ascii=False, indent=2)
                    lines = json_str.split('\n')
                    indented = '\n'.join('  ' + line for line in lines)
                    f.write(indented)

                    total += 1

                f.write('\n]')

            logger.info(f"[STREAMING] Saved {total} stocks to {filename}")

        except Exception as e:
            logger.error(f"[STREAMING] Error saving to JSON: {str(e)}")
            raise


class MongoDBUploader:
    """Lightweight MongoDB uploader for streaming stock data"""

    def __init__(self, connection_string: str, database_name: str, collection_name: str):
        """
        Initialize MongoDB uploader

        Args:
            connection_string: MongoDB connection string
            database_name: Database name
            collection_name: Collection name
        """
        if not MONGODB_AVAILABLE:
            raise ImportError("pymongo is not installed. Run: pip install pymongo")

        self.connection_string = connection_string
        self.database_name = database_name
        self.collection_name = collection_name
        self.client = None
        self.db = None
        self.collection = None

    def connect(self) -> bool:
        """Connect to MongoDB"""
        try:
            logger.info(f"Connecting to MongoDB...")
            self.client = MongoClient(self.connection_string, serverSelectionTimeoutMS=5000)

            # Test connection
            self.client.server_info()

            self.db = self.client[self.database_name]
            self.collection = self.db[self.collection_name]

            logger.info(f"[SUCCESS] Connected to MongoDB: {self.database_name}.{self.collection_name}")
            return True

        except ConnectionFailure as e:
            logger.error(f"[ERROR] Failed to connect to MongoDB: {e}")
            return False
        except Exception as e:
            logger.error(f"[ERROR] Unexpected error during connection: {e}")
            return False

    def create_indexes(self):
        """Create indexes for better query performance"""
        try:
            logger.info("Creating MongoDB indexes...")

            # Unique index on hash for deduplication
            self.collection.create_index("hash", unique=True)

            # Index on symbol for quick lookups
            self.collection.create_index("symbol")

            # Index on scraped_at for sorting
            self.collection.create_index("scraped_at")

            logger.info("[SUCCESS] MongoDB indexes created")

        except Exception as e:
            logger.warning(f"[WARNING] Failed to create indexes: {e}")

    async def upload_streaming(
        self,
        data_async_iterator: AsyncIterator,
        batch_size: int = 50,
        upsert: bool = True
    ) -> Dict[str, int]:
        """
        Upload stocks to MongoDB using streaming (memory-efficient)

        Args:
            data_async_iterator: Async iterator yielding stock data
            batch_size: Number of stocks per batch
            upsert: If True, update existing records

        Returns:
            Dictionary with upload statistics
        """
        stats = {
            "inserted": 0,
            "updated": 0,
            "failed": 0
        }

        operations = []
        total_processed = 0

        try:
            logger.info(f"[MONGODB] Starting streaming upload (batch_size={batch_size})...")

            async for stock_data in data_async_iterator:
                # Create upsert operation based on hash
                filter_key = {"hash": stock_data["hash"]}

                operations.append(
                    UpdateOne(
                        filter_key,
                        {"$set": stock_data},
                        upsert=upsert
                    )
                )

                # Flush batch when full
                if len(operations) >= batch_size:
                    result = self.collection.bulk_write(operations, ordered=False)
                    stats["inserted"] += result.upserted_count
                    stats["updated"] += result.modified_count
                    total_processed += len(operations)

                    logger.info(f"[MONGODB] Uploaded batch: {len(operations)} operations (total: {total_processed})")
                    operations = []

            # Flush remaining operations
            if operations:
                result = self.collection.bulk_write(operations, ordered=False)
                stats["inserted"] += result.upserted_count
                stats["updated"] += result.modified_count
                total_processed += len(operations)

                logger.info(f"[MONGODB] Uploaded final batch: {len(operations)} operations")

            logger.info(f"[MONGODB] Completed: {total_processed} total stocks")
            logger.info(f"  - Inserted: {stats['inserted']}")
            logger.info(f"  - Updated: {stats['updated']}")

        except BulkWriteError as e:
            logger.error(f"[ERROR] Bulk write error: {e.details}")
            stats["failed"] = len(operations)
        except Exception as e:
            logger.error(f"[ERROR] MongoDB upload failed: {e}")
            stats["failed"] = len(operations)

        return stats

    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")


async def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(
        description='Screener.in Stock Data Scraper',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape to JSON file
  python scrapers/screener/screener_scraper.py --symbols-file data/nifty100_symbols.json

  # Scrape specific symbols
  python scrapers/screener/screener_scraper.py --symbols HDFCBANK,TCS,RELIANCE

  # Scrape with custom batch size
  python scrapers/screener/screener_scraper.py --symbols-file data/nifty100_symbols.json --batch-size 20

  # Scrape and upload to MongoDB (streaming)
  python scrapers/screener/screener_scraper.py --symbols-file data/nifty100_symbols.json --upload-mongodb

  # Scrape to MongoDB with custom settings
  python scrapers/screener/screener_scraper.py --symbols HDFCBANK,TCS,RELIANCE \
    --upload-mongodb --mongodb-uri mongodb://localhost:27017/ \
    --mongodb-db my_stocks_db --mongodb-collection nifty100
        """
    )
    parser.add_argument(
        '--symbols-file',
        type=str,
        help='JSON file with list of stock symbols'
    )
    parser.add_argument(
        '--symbols',
        type=str,
        help='Comma-separated stock symbols (e.g., HDFCBANK,TCS,RELIANCE)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=10,
        help='Batch size for batched scraping (default: 10)'
    )
    parser.add_argument(
        '--delay',
        type=float,
        default=3.0,
        help='Delay between stocks in seconds (default: 3.0)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='screener_stocks.json',
        help='Output JSON filename (default: screener_stocks.json)'
    )
    parser.add_argument(
        '--method',
        type=str,
        default='batched',
        choices=['standard', 'generator', 'batched'],
        help='Scraping method (default: batched)'
    )

    # MongoDB upload options
    parser.add_argument(
        '--upload-mongodb',
        action='store_true',
        help='Upload data to MongoDB in real-time (streaming)'
    )
    parser.add_argument(
        '--mongodb-uri',
        type=str,
        default=os.getenv('MONGODB_URI', 'mongodb://localhost:27017/'),
        help='MongoDB connection URI (default: mongodb://localhost:27017/)'
    )
    parser.add_argument(
        '--mongodb-db',
        type=str,
        default=os.getenv('MONGODB_DB', 'screener_db'),
        help='MongoDB database name (default: screener_db)'
    )
    parser.add_argument(
        '--mongodb-collection',
        type=str,
        default=os.getenv('MONGODB_COLLECTION', 'stocks'),
        help='MongoDB collection name (default: stocks)'
    )
    parser.add_argument(
        '--mongodb-batch-size',
        type=int,
        default=50,
        help='MongoDB batch size for bulk operations (default: 50)'
    )

    args = parser.parse_args()

    # Configure logging
    global logger
    log_dir = Path('logs/screener')
    log_dir.mkdir(parents=True, exist_ok=True)

    log_filename = log_dir / f"scraper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename),
            logging.StreamHandler(sys.stdout)
        ],
        force=True
    )
    logger = logging.getLogger(__name__)

    # Load symbols
    symbols = []
    if args.symbols_file:
        try:
            with open(args.symbols_file, 'r') as f:
                symbols = json.load(f)
            logger.info(f"Loaded {len(symbols)} symbols from {args.symbols_file}")
        except Exception as e:
            logger.error(f"Error loading symbols file: {e}")
            return
    elif args.symbols:
        symbols = [s.strip().upper() for s in args.symbols.split(',')]
        logger.info(f"Using {len(symbols)} symbols from command line")
    else:
        logger.error("Please provide --symbols-file or --symbols")
        return

    if not symbols:
        logger.error("No symbols to scrape")
        return

    # Initialize scraper
    scraper = ScreenerScraper(delay=args.delay)

    logger.info(f"Starting Screener.in scraper for {len(symbols)} stocks")
    logger.info(f"Method: {args.method}, Delay: {args.delay}s")
    if args.upload_mongodb:
        logger.info(f"MongoDB upload: ENABLED")

    # Initialize MongoDB uploader if needed
    mongo_uploader = None
    if args.upload_mongodb:
        if not MONGODB_AVAILABLE:
            logger.error("MongoDB upload requested but pymongo is not installed!")
            logger.error("Install it with: pip install pymongo")
            return

        mongo_uploader = MongoDBUploader(
            connection_string=args.mongodb_uri,
            database_name=args.mongodb_db,
            collection_name=args.mongodb_collection
        )

        if not mongo_uploader.connect():
            logger.error("Failed to connect to MongoDB. Exiting...")
            return

        mongo_uploader.create_indexes()

    try:
        # Scrape based on method
        if args.upload_mongodb:
            # Use generator method for streaming upload to MongoDB + JSON
            logger.info("Using generator method for MongoDB streaming upload...")

            # Create async generator wrapper for dual output
            async def dual_output_processor():
                """Process each stock data to both MongoDB and JSON"""
                stats = {
                    "inserted": 0,
                    "updated": 0,
                    "failed": 0
                }
                operations = []

                # Open JSON file for streaming write
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write('[\n')
                    first = True
                    total = 0

                    async for stock_data in scraper.scrape_stocks_generator(symbols, delay=args.delay):
                        # Write to JSON
                        if not first:
                            f.write(',\n')
                        first = False

                        json_str = json.dumps(stock_data, ensure_ascii=False, indent=2)
                        lines = json_str.split('\n')
                        indented = '\n'.join('  ' + line for line in lines)
                        f.write(indented)
                        total += 1

                        # Add to MongoDB batch
                        filter_key = {"hash": stock_data["hash"]}
                        operations.append(
                            UpdateOne(
                                filter_key,
                                {"$set": stock_data},
                                upsert=True
                            )
                        )

                        # Flush MongoDB batch when full
                        if len(operations) >= args.mongodb_batch_size:
                            try:
                                result = mongo_uploader.collection.bulk_write(operations, ordered=False)
                                stats["inserted"] += result.upserted_count
                                stats["updated"] += result.modified_count
                                logger.info(f"[MONGODB] Uploaded batch: {len(operations)} operations")
                                operations = []
                            except BulkWriteError as e:
                                logger.error(f"[ERROR] Bulk write error: {e.details}")
                                stats["failed"] += len(operations)
                                operations = []

                    # Flush remaining MongoDB operations
                    if operations:
                        try:
                            result = mongo_uploader.collection.bulk_write(operations, ordered=False)
                            stats["inserted"] += result.upserted_count
                            stats["updated"] += result.modified_count
                            logger.info(f"[MONGODB] Uploaded final batch: {len(operations)} operations")
                        except BulkWriteError as e:
                            logger.error(f"[ERROR] Bulk write error: {e.details}")
                            stats["failed"] += len(operations)

                    # Close JSON array
                    f.write('\n]')
                    logger.info(f"[STREAMING] Saved {total} stocks to {args.output}")

                return stats

            # Execute dual output
            mongo_stats = await dual_output_processor()

            logger.info(f"\n[MONGODB STATS]")
            logger.info(f"  - Inserted: {mongo_stats['inserted']}")
            logger.info(f"  - Updated: {mongo_stats['updated']}")
            logger.info(f"  - Failed: {mongo_stats['failed']}")

        elif args.method == 'generator':
            # Generator method - streaming save to JSON only
            generator = scraper.scrape_stocks_generator(symbols, delay=args.delay)
            await scraper.save_to_json_streaming(generator, args.output)

        elif args.method == 'batched':
            # Batched method - load all in memory
            all_stocks = []
            async for batch in scraper.scrape_stocks_batched(
                symbols,
                batch_size=args.batch_size,
                delay=args.delay
            ):
                all_stocks.extend(batch)
                logger.info(f"Progress: {len(all_stocks)}/{len(symbols)} stocks scraped")

            scraper.save_to_json(all_stocks, args.output)

        else:
            # Standard method (not recommended for large lists)
            logger.warning("Standard method loads all data in memory - use generator or batched for large lists")
            all_stocks = []
            async with AsyncWebCrawler(verbose=True) as crawler:
                for symbol in symbols:
                    stock_data = await scraper.scrape_stock(symbol, crawler)
                    if stock_data:
                        all_stocks.append(stock_data)
                    await asyncio.sleep(args.delay)

            scraper.save_to_json(all_stocks, args.output)

        print(f"\n{'='*70}")
        print(f"Scraping completed!")
        print(f"Output: {args.output}")
        if args.upload_mongodb:
            print(f"MongoDB: {args.mongodb_db}.{args.mongodb_collection}")
        print(f"{'='*70}\n")

    finally:
        # Close MongoDB connection
        if mongo_uploader:
            mongo_uploader.close()


if __name__ == "__main__":
    asyncio.run(main())
