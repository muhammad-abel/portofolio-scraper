#!/usr/bin/env python3
"""
Enhanced Crawl4AI Scraper with Auto Page Detection
Automatically detects total available pages
"""

import asyncio
from crawl4ai import AsyncWebCrawler
from bs4 import BeautifulSoup
import pandas as pd
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional
import sys
from urllib.parse import urljoin
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper_crawl4ai_enhanced.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class EnhancedMoneyControlScraper:
    """Enhanced scraper with auto page detection"""

    def __init__(self, base_url: str = "https://www.moneycontrol.com/news/business/markets/", fetch_details: bool = True):
        self.base_url = base_url
        self.fetch_details = fetch_details
        self.total_pages = None  # Will be auto-detected

    async def detect_total_pages(self, crawler: AsyncWebCrawler, max_pages: int = 100) -> int:
        """
        Auto-detect total number of pages available

        Args:
            crawler: AsyncWebCrawler instance
            max_pages: Maximum pages to check (safety limit)

        Returns:
            Total number of pages
        """
        try:
            logger.info("Auto-detecting total pages...")

            # Method 1: Check pagination on first page
            result = await crawler.arun(
                url=f"{self.base_url}page-1/",
                word_count_threshold=10,
                bypass_cache=True,
                wait_for="body"
            )

            if not result.success:
                logger.warning("Failed to detect pages, defaulting to 1")
                return 1

            soup = BeautifulSoup(result.html, 'lxml')

            # Try to find pagination elements
            # Common patterns on Moneycontrol:
            # 1. <a> tags with page numbers
            # 2. <span> or <div> with class containing 'page' or 'pagination'

            page_links = []

            # Pattern 1: Find all links in pagination
            pagination_div = soup.find('div', class_=re.compile(r'pagination|paging', re.I))
            if pagination_div:
                page_links = pagination_div.find_all('a', href=re.compile(r'page-\d+'))

            # Pattern 2: Find all page-X links
            if not page_links:
                page_links = soup.find_all('a', href=re.compile(r'page-\d+'))

            # Extract page numbers
            page_numbers = []
            for link in page_links:
                href = link.get('href', '')
                match = re.search(r'page-(\d+)', href)
                if match:
                    page_numbers.append(int(match.group(1)))

            if page_numbers:
                total = max(page_numbers)
                logger.info(f"Detected {total} total pages from pagination")
                return min(total, max_pages)

            # Method 2: Binary search for last valid page
            logger.info("Pagination not found, using binary search...")
            total = await self._binary_search_last_page(crawler, max_pages)
            logger.info(f"Detected {total} pages via binary search")
            return total

        except Exception as e:
            logger.error(f"Error detecting pages: {str(e)}")
            return 1

    async def _binary_search_last_page(self, crawler: AsyncWebCrawler, max_pages: int) -> int:
        """
        Use binary search to find last valid page

        Args:
            crawler: AsyncWebCrawler instance
            max_pages: Maximum pages to search

        Returns:
            Last valid page number
        """
        left, right = 1, max_pages
        last_valid = 1

        while left <= right:
            mid = (left + right) // 2

            # Check if page exists
            result = await crawler.arun(
                url=f"{self.base_url}page-{mid}/",
                word_count_threshold=10,
                bypass_cache=True,
                wait_for="body"
            )

            if result.success:
                soup = BeautifulSoup(result.html, 'lxml')
                articles = soup.find_all('li', class_='clearfix')

                if articles:
                    # Page exists and has content
                    last_valid = mid
                    left = mid + 1  # Search higher
                    logger.debug(f"Page {mid} exists, searching higher...")
                else:
                    # Page exists but no content (end of pages)
                    right = mid - 1
                    logger.debug(f"Page {mid} empty, searching lower...")
            else:
                # Page doesn't exist
                right = mid - 1
                logger.debug(f"Page {mid} not found, searching lower...")

        return last_valid

    async def scrape_all_pages(self, delay: float = 2.0, max_pages: Optional[int] = None) -> List[Dict]:
        """
        Scrape ALL available pages automatically

        Args:
            delay: Delay between pages
            max_pages: Optional limit on maximum pages to scrape

        Returns:
            All articles from all pages
        """
        all_articles = []

        async with AsyncWebCrawler(verbose=True) as crawler:
            # Auto-detect total pages
            if max_pages:
                total = max_pages
                logger.info(f"Using manual limit: {total} pages")
            else:
                total = await self.detect_total_pages(crawler, max_pages=100)
                logger.info(f"Will scrape {total} pages")

            # Scrape all pages
            for page in range(1, total + 1):
                logger.info(f"Scraping page {page}/{total}")
                articles = await self.scrape_page(page, crawler)
                all_articles.extend(articles)

                if page < total:
                    await asyncio.sleep(delay)

            logger.info(f"Total articles scraped from {total} pages: {len(all_articles)}")

        return all_articles

    async def scrape_page(self, page_number: int, crawler: AsyncWebCrawler) -> List[Dict]:
        """Scrape single page (simplified version)"""
        url = f"{self.base_url}page-{page_number}/"
        articles = []

        try:
            result = await crawler.arun(
                url=url,
                word_count_threshold=10,
                bypass_cache=True,
                wait_for="body"
            )

            if not result.success:
                return []

            soup = BeautifulSoup(result.html, 'lxml')
            article_containers = soup.find_all('li', class_='clearfix')

            logger.info(f"Found {len(article_containers)} articles on page {page_number}")

            for article_elem in article_containers:
                article_data = self.extract_article_data(article_elem)
                if article_data:
                    articles.append(article_data)

            # Fetch details if enabled
            if self.fetch_details and articles:
                detail_tasks = [
                    self.fetch_article_details(article['url'], crawler)
                    for article in articles
                ]
                details = await asyncio.gather(*detail_tasks)

                for article, detail in zip(articles, details):
                    article['date'] = detail['date']
                    article['author'] = detail['author']

        except Exception as e:
            logger.error(f"Error scraping page {page_number}: {str(e)}")

        return articles

    async def fetch_article_details(self, url: str, crawler: AsyncWebCrawler) -> Dict[str, str]:
        """Fetch details from article page"""
        try:
            result = await crawler.arun(url=url, word_count_threshold=10, bypass_cache=True)
            if not result.success:
                return {'date': '', 'author': ''}

            soup = BeautifulSoup(result.html, 'lxml')

            author = ''
            author_elem = soup.find('div', class_='article_author')
            if author_elem:
                author_link = author_elem.find('a')
                author = author_link.get_text(strip=True) if author_link else ''

            date = ''
            date_elem = soup.find('div', class_='article_schedule')
            if date_elem:
                date_span = date_elem.find('span')
                if date_span:
                    date_text = date_span.get_text(strip=True)
                    date = date_text.split('/')[0].strip() if '/' in date_text else date_text

            return {'date': date, 'author': author}

        except Exception as e:
            logger.error(f"Error fetching details from {url}: {str(e)}")
            return {'date': '', 'author': ''}

    def extract_article_data(self, article_element) -> Optional[Dict]:
        """Extract article data from element"""
        try:
            article_data = {}

            link_elem = article_element.find('a', class_='unified-link') or article_element.find('a')
            if link_elem:
                href = link_elem.get('href', '')
                article_data['url'] = href if href.startswith('http') else urljoin(self.base_url, href)

                title_elem = link_elem.find('h2')
                article_data['title'] = title_elem.get_text(strip=True) if title_elem else ''

                img_elem = link_elem.find('img')
                if img_elem:
                    article_data['image_url'] = img_elem.get('src') or img_elem.get('data-src') or img_elem.get('data', '')
                else:
                    article_data['image_url'] = ''
            else:
                return None

            summary_elem = article_element.find('p')
            article_data['summary'] = summary_elem.get_text(strip=True) if summary_elem else ''
            article_data['date'] = ''
            article_data['author'] = ''
            article_data['scraped_at'] = datetime.now().isoformat()

            if article_data.get('title') and article_data.get('url'):
                return article_data
            return None

        except Exception as e:
            logger.error(f"Error extracting article: {str(e)}")
            return None

    def save_to_json(self, articles: List[Dict], filename: str = "moneycontrol_auto.json"):
        """Save to JSON"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(articles)} articles to {filename}")

    def save_to_csv(self, articles: List[Dict], filename: str = "moneycontrol_auto.csv"):
        """Save to CSV"""
        df = pd.DataFrame(articles)
        df.to_csv(filename, index=False, encoding='utf-8')
        logger.info(f"Saved {len(articles)} articles to {filename}")


async def main():
    """Main execution"""
    scraper = EnhancedMoneyControlScraper(fetch_details=True)

    print("="*60)
    print("Enhanced Scraper with Auto Page Detection")
    print("="*60)

    # Option 1: Scrape ALL pages automatically
    print("\n[Option 1] Scraping ALL available pages (auto-detect)...")
    # articles = await scraper.scrape_all_pages(delay=2.0)

    # Option 2: Scrape with limit
    print("\n[Option 2] Scraping with 5 page limit...")
    articles = await scraper.scrape_all_pages(delay=2.0, max_pages=5)

    if articles:
        scraper.save_to_json(articles)
        scraper.save_to_csv(articles)

        print(f"\n{'='*60}")
        print(f"Scraping completed!")
        print(f"Total articles: {len(articles)}")
        print(f"{'='*60}\n")

        print("First 3 articles:")
        for i, article in enumerate(articles[:3], 1):
            print(f"\n{i}. {article.get('title', 'No title')[:60]}...")
            print(f"   Date: {article.get('date')}")
            print(f"   Author: {article.get('author')}")


if __name__ == "__main__":
    asyncio.run(main())
