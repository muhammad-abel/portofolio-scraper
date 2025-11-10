#!/usr/bin/env python3
"""
TradingEconomics Indicators Scraper (Crawl4AI version)
Scrapes economic indicators tables from TradingEconomics.com
"""

import asyncio
import os
import base64
import hashlib
from pathlib import Path
from crawl4ai import AsyncWebCrawler
from bs4 import BeautifulSoup
import pandas as pd
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional
import sys
import argparse

# Available tabs on TradingEconomics indicators page
TABS = [
    'overview', 'gdp', 'labour', 'prices', 'money',
    'trade', 'government', 'business', 'consumer',
    'housing', 'health'
]

# Logger will be configured in main()
logger = None


class TradingEconomicsScraper:
    """Scraper for TradingEconomics indicators tables"""

    def __init__(self, country: str = "india"):
        """
        Initialize the TradingEconomics scraper

        Args:
            country: Country name for scraping (default: india)
        """
        self.country = country.lower()
        self.base_url = f"https://tradingeconomics.com/{self.country}/indicators"

    @staticmethod
    def generate_indicator_hash(country: str, tab: str, indicator: str) -> str:
        """
        Generate unique hash from country, tab, and indicator using base64 encoding

        Args:
            country: Country name
            tab: Tab name
            indicator: Indicator name

        Returns:
            Base64 encoded hash string
        """
        # Combine country, tab, and indicator, normalize to lowercase and strip whitespace
        combined = f"{country.lower().strip()}|{tab.lower().strip()}|{indicator.lower().strip()}"

        # Create SHA256 hash
        hash_object = hashlib.sha256(combined.encode('utf-8'))

        # Convert to base64 and decode to string
        base64_hash = base64.b64encode(hash_object.digest()).decode('utf-8')

        return base64_hash

    async def scrape_tab(self, tab_name: str, crawler: AsyncWebCrawler) -> List[Dict]:
        """
        Scrape a single tab's table data

        Args:
            tab_name: Name of the tab to scrape
            crawler: AsyncWebCrawler instance

        Returns:
            List of indicator dictionaries
        """
        indicators = []

        try:
            logger.info(f"Scraping tab: {tab_name}")

            # Load the main page
            result = await crawler.arun(
                url=self.base_url,
                word_count_threshold=10,
                bypass_cache=True,
                wait_for="body",
                page_timeout=60000,
                delay_before_return_html=2.0  # Wait for tabs to load
            )

            if not result.success:
                logger.error(f"Failed to load page for tab {tab_name}: {result.error_message}")
                return []

            soup = BeautifulSoup(result.html, 'lxml')

            # Find the tab content div
            tab_div = soup.find('div', {'id': tab_name, 'role': 'tabpanel'})

            if not tab_div:
                logger.warning(f"Tab content not found for: {tab_name}")
                return []

            # Find the table within this tab
            table = tab_div.find('table', class_='table table-hover')

            if not table:
                logger.warning(f"Table not found in tab: {tab_name}")
                return []

            # Extract table headers with hardcoded mapping for empty columns
            # Column mapping based on actual structure:
            # Index 0: indicator (empty header)
            # Index 1: last (header: "Last")
            # Index 2: previous (header: "Previous")
            # Index 3: highest (header: "Highest")
            # Index 4: lowest (header: "Lowest")
            # Index 5: unit (empty header)
            # Index 6: date (empty header)
            COLUMN_MAPPING = {
                0: "indicator",
                1: "last",
                2: "previous",
                3: "highest",
                4: "lowest",
                5: "unit",
                6: "date"
            }

            thead = table.find('thead')
            if not thead:
                logger.warning(f"No thead found in table for tab: {tab_name}")
                return []

            header_row = thead.find('tr')
            if not header_row:
                logger.warning(f"No header row found in table for tab: {tab_name}")
                return []

            # Get column count
            ths = header_row.find_all('th')
            num_columns = len(ths)

            if num_columns != 7:
                logger.warning(f"Expected 7 columns but found {num_columns} in tab: {tab_name}")
                # Still proceed, will use mapping

            logger.info(f"Found {num_columns} columns in table for tab: {tab_name}")

            # Extract table rows
            tbody = table.find('tbody')
            if not tbody:
                logger.warning(f"No tbody found in table for tab: {tab_name}")
                return []

            rows = tbody.find_all('tr')
            logger.info(f"Found {len(rows)} rows in tab: {tab_name}")

            for row in rows:
                cells = row.find_all('td')
                if len(cells) != num_columns:
                    logger.debug(f"Skipping row with mismatched cell count: {len(cells)} vs {num_columns}")
                    continue

                # Create indicator dict by mapping column indices to field names
                indicator_data = {}
                for idx, cell in enumerate(cells):
                    # Get text, handle links
                    text = cell.get_text(strip=True)

                    # Use hardcoded mapping
                    if idx in COLUMN_MAPPING:
                        field_name = COLUMN_MAPPING[idx]
                        indicator_data[field_name] = text
                    else:
                        # Fallback for unexpected columns
                        indicator_data[f"column_{idx}"] = text

                # Add metadata
                indicator_data['country'] = self.country
                indicator_data['tab_name'] = tab_name
                indicator_data['scraped_at'] = datetime.now().isoformat()

                # Generate unique hash using indicator name
                indicator_name = indicator_data.get('indicator', '')
                indicator_data['hash'] = self.generate_indicator_hash(
                    self.country,
                    tab_name,
                    indicator_name
                )

                indicators.append(indicator_data)

            logger.info(f"[SUCCESS] Extracted {len(indicators)} indicators from tab: {tab_name}")

        except Exception as e:
            logger.error(f"Error scraping tab {tab_name}: {str(e)}")

        return indicators

    async def scrape_tabs(self, tabs: List[str]) -> Dict[str, List[Dict]]:
        """
        Scrape multiple tabs

        Args:
            tabs: List of tab names to scrape

        Returns:
            Dictionary mapping tab names to lists of indicators
        """
        all_data = {}

        async with AsyncWebCrawler(verbose=True) as crawler:
            for tab_name in tabs:
                indicators = await self.scrape_tab(tab_name, crawler)
                all_data[tab_name] = indicators

                # Small delay between tabs
                if tab_name != tabs[-1]:
                    await asyncio.sleep(1.0)

        return all_data

    def save_to_json(self, data: List[Dict], filename: str):
        """Save indicators to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved {len(data)} indicators to {filename}")
        except Exception as e:
            logger.error(f"Error saving to JSON: {str(e)}")

    def save_to_csv(self, data: List[Dict], filename: str):
        """Save indicators to CSV file"""
        try:
            if not data:
                logger.warning("No data to save to CSV")
                return

            df = pd.DataFrame(data)
            df.to_csv(filename, index=False, encoding='utf-8')
            logger.info(f"Saved {len(data)} indicators to {filename}")
        except Exception as e:
            logger.error(f"Error saving to CSV: {str(e)}")


async def main():
    """Main execution function"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='TradingEconomics Indicators Scraper with Crawl4AI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tradingeconomics.py --country india
  python run_tradingeconomics.py --country india --tabs gdp,labour,prices
  python run_tradingeconomics.py --country india --upload-mongo
  python run_tradingeconomics.py --country india --tabs gdp,labour --upload-mongo
        """
    )
    parser.add_argument(
        '--country',
        type=str,
        default='india',
        help='Country to scrape indicators for (default: india)'
    )
    parser.add_argument(
        '--tabs',
        type=str,
        default='',
        help='Comma-separated list of tabs to scrape (default: all tabs). Available: ' + ', '.join(TABS)
    )
    parser.add_argument(
        '--upload-mongo',
        action='store_true',
        help='Upload results to MongoDB after scraping'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='.',
        help='Output directory for JSON/CSV files (default: current directory)'
    )

    args = parser.parse_args()

    # Configure logging
    global logger
    log_dir = Path('logs/tradingeconomics')
    log_dir.mkdir(parents=True, exist_ok=True)

    log_filename = log_dir / f"scraper_{args.country}.log"

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

    # Parse tabs
    if args.tabs:
        selected_tabs = [t.strip().lower() for t in args.tabs.split(',')]
        # Validate tabs
        invalid_tabs = [t for t in selected_tabs if t not in TABS]
        if invalid_tabs:
            logger.error(f"Invalid tabs: {invalid_tabs}. Available tabs: {TABS}")
            return
        tabs_to_scrape = selected_tabs
    else:
        tabs_to_scrape = TABS

    logger.info(f"Starting TradingEconomics scraper for country '{args.country}'")
    logger.info(f"Tabs to scrape: {tabs_to_scrape}")

    # Initialize scraper
    scraper = TradingEconomicsScraper(country=args.country)

    # Scrape tabs
    all_data = await scraper.scrape_tabs(tabs_to_scrape)

    # Save data
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    total_indicators = 0

    for tab_name, indicators in all_data.items():
        if indicators:
            # Save to JSON (per tab) if not uploading to MongoDB
            if not args.upload_mongo:
                json_filename = output_dir / f"tradingeconomics_{args.country}_{tab_name}.json"
                scraper.save_to_json(indicators, str(json_filename))

            total_indicators += len(indicators)

    # Print summary
    print(f"\n{'='*60}")
    print(f"Scraping completed successfully!")
    print(f"Country: {args.country}")
    print(f"Total tabs scraped: {len(all_data)}")
    print(f"Total indicators extracted: {total_indicators}")
    print(f"{'='*60}\n")

    # Print preview
    if total_indicators > 0:
        print("Preview of first tab:\n")
        first_tab = next(iter(all_data.keys()))
        first_indicators = all_data[first_tab][:3]

        for i, indicator in enumerate(first_indicators, 1):
            print(f"{i}. Indicator: {indicator.get('indicator', 'N/A')}")
            print(f"   Country: {indicator.get('country', 'N/A')}")
            print(f"   Tab: {indicator.get('tab_name', 'N/A')}")
            print(f"   Last: {indicator.get('last', 'N/A')}")
            print(f"   Previous: {indicator.get('previous', 'N/A')}")
            print(f"   Highest: {indicator.get('highest', 'N/A')}")
            print(f"   Lowest: {indicator.get('lowest', 'N/A')}")
            print(f"   Unit: {indicator.get('unit', 'N/A')}")
            print(f"   Date: {indicator.get('date', 'N/A')}")
            print(f"   Hash: {indicator.get('hash', 'N/A')[:20]}...")
            print()

    # Upload to MongoDB if flag is set
    if args.upload_mongo:
        print(f"\n{'='*60}")
        print("Uploading to MongoDB...")
        print(f"{'='*60}\n")

        try:
            # Flatten all indicators from all tabs into one list
            all_indicators = []
            for indicators in all_data.values():
                all_indicators.extend(indicators)

            if not all_indicators:
                logger.warning("No indicators to upload")
                return

            # Import MongoDB uploader
            sys.path.insert(0, str(Path(__file__).parent.parent.parent))
            from dotenv import load_dotenv
            load_dotenv()

            from pymongo import MongoClient, UpdateOne
            from pymongo.errors import BulkWriteError

            # Get MongoDB config from environment
            MONGODB_CONNECTION_STRING = os.getenv("MONGODB_CONNECTION_STRING", "mongodb://localhost:27017/")
            DATABASE_NAME = os.getenv("MONGODB_DATABASE_NAME", "tradingeconomics_db")
            COLLECTION_NAME = "indicators"

            # Connect to MongoDB
            client = MongoClient(MONGODB_CONNECTION_STRING, serverSelectionTimeoutMS=5000)
            client.server_info()  # Test connection

            db = client[DATABASE_NAME]
            collection = db[COLLECTION_NAME]

            logger.info(f"Connected to MongoDB: {DATABASE_NAME}.{COLLECTION_NAME}")

            # Create unique index on hash
            collection.create_index("hash", unique=True)
            collection.create_index("country")
            collection.create_index("tab_name")
            logger.info("Indexes created")

            # Bulk upsert
            operations = []
            for indicator in all_indicators:
                operations.append(
                    UpdateOne(
                        {"hash": indicator["hash"]},
                        {"$set": indicator},
                        upsert=True
                    )
                )

            result = collection.bulk_write(operations, ordered=False)

            print(f"\n{'='*60}")
            print("MongoDB Upload Summary:")
            print(f"  - Inserted: {result.upserted_count}")
            print(f"  - Updated: {result.modified_count}")
            print(f"  - Total: {len(all_indicators)}")
            print(f"{'='*60}\n")

            client.close()
            logger.info("[SUCCESS] Upload completed")

        except Exception as e:
            logger.error(f"Error uploading to MongoDB: {e}")

    else:
        logger.info("Scraping completed! (No MongoDB upload)")


if __name__ == "__main__":
    asyncio.run(main())
