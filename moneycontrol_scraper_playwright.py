#!/usr/bin/env python3
"""
Moneycontrol News Scraper (Playwright version)
Async scraper using Playwright directly for maximum control
"""

import asyncio
from playwright.async_api import async_playwright, Page, Browser
from bs4 import BeautifulSoup
import pandas as pd
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional
import sys
from urllib.parse import urljoin

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper_playwright.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class MoneyControlPlaywrightScraper:
    """Async scraper using Playwright"""

    def __init__(self, base_url: str = "https://www.moneycontrol.com/news/business/markets/", headless: bool = True):
        """
        Initialize the Playwright scraper

        Args:
            base_url: Base URL for the markets section
            headless: Run browser in headless mode
        """
        self.base_url = base_url
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.playwright = None

    async def initialize(self):
        """Initialize Playwright browser"""
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                ]
            )
            logger.info("Playwright browser initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Playwright: {str(e)}")
            raise

    async def close(self):
        """Close Playwright browser"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("Playwright browser closed")

    def extract_article_data(self, article_element) -> Optional[Dict]:
        """
        Extract data from a single article element

        Args:
            article_element: BeautifulSoup element containing article data

        Returns:
            Dictionary with article data or None
        """
        try:
            article_data = {}

            # Extract title and link
            title_elem = article_element.find('h2') or article_element.find('a')
            if title_elem:
                link_elem = title_elem.find('a') if title_elem.name != 'a' else title_elem
                if link_elem:
                    article_data['title'] = link_elem.get_text(strip=True)
                    article_data['url'] = urljoin(self.base_url, link_elem.get('href', ''))
                else:
                    article_data['title'] = title_elem.get_text(strip=True)
                    article_data['url'] = ''

            # Extract date
            date_elem = article_element.find('span', class_='article-time') or \
                       article_element.find('time') or \
                       article_element.find('span', class_='date')
            article_data['date'] = date_elem.get_text(strip=True) if date_elem else ''

            # Extract summary/description
            summary_elem = article_element.find('p') or article_element.find('div', class_='article-desc')
            article_data['summary'] = summary_elem.get_text(strip=True) if summary_elem else ''

            # Extract image
            img_elem = article_element.find('img')
            article_data['image_url'] = img_elem.get('src', '') if img_elem else ''

            # Extract author if available
            author_elem = article_element.find('span', class_='author') or \
                         article_element.find('a', class_='author')
            article_data['author'] = author_elem.get_text(strip=True) if author_elem else ''

            # Add metadata
            article_data['scraped_at'] = datetime.now().isoformat()

            # Only return if we have at least a title
            if article_data.get('title'):
                return article_data
            return None

        except Exception as e:
            logger.error(f"Error extracting article data: {str(e)}")
            return None

    async def scrape_page(self, page_number: int = 1) -> List[Dict]:
        """
        Scrape all articles from a single page using Playwright

        Args:
            page_number: Page number to scrape

        Returns:
            List of article dictionaries
        """
        if not self.browser:
            await self.initialize()

        url = f"{self.base_url}page-{page_number}/"
        articles = []

        try:
            # Create a new page
            page = await self.browser.new_page()

            # Set extra headers
            await page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
            })

            logger.info(f"Loading page {page_number}: {url}")

            # Navigate to the page
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)

            # Wait for content to load
            await page.wait_for_selector('body', timeout=10000)

            # Scroll to load lazy content
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(2)

            # Get page content
            content = await page.content()

            # Parse with BeautifulSoup
            soup = BeautifulSoup(content, 'lxml')

            # Find article elements
            article_containers = (
                soup.find_all('li', class_='clearfix') or
                soup.find_all('div', class_='article') or
                soup.find_all('article') or
                soup.find_all('li', recursive=True)
            )

            logger.info(f"Found {len(article_containers)} potential article elements on page {page_number}")

            for idx, article_elem in enumerate(article_containers, 1):
                article_data = self.extract_article_data(article_elem)
                if article_data:
                    articles.append(article_data)
                    logger.debug(f"Extracted article {idx}: {article_data.get('title', 'No title')[:50]}")

            logger.info(f"Successfully extracted {len(articles)} articles from page {page_number}")

            # Close the page
            await page.close()

        except Exception as e:
            logger.error(f"Error scraping page {page_number}: {str(e)}")

        return articles

    async def scrape_multiple_pages(self, num_pages: int = 1, delay: float = 2.0) -> List[Dict]:
        """
        Scrape multiple pages asynchronously

        Args:
            num_pages: Number of pages to scrape
            delay: Delay between page requests (seconds)

        Returns:
            List of all article dictionaries
        """
        all_articles = []

        try:
            for page in range(1, num_pages + 1):
                logger.info(f"Scraping page {page}/{num_pages}")
                articles = await self.scrape_page(page)
                all_articles.extend(articles)

                # Be polite - add delay between requests
                if page < num_pages:
                    logger.info(f"Waiting {delay} seconds before next page...")
                    await asyncio.sleep(delay)

            logger.info(f"Total articles scraped: {len(all_articles)}")

        finally:
            await self.close()

        return all_articles

    def save_to_json(self, articles: List[Dict], filename: str = "moneycontrol_news_playwright.json"):
        """Save articles to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(articles, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved {len(articles)} articles to {filename}")
        except Exception as e:
            logger.error(f"Error saving to JSON: {str(e)}")

    def save_to_csv(self, articles: List[Dict], filename: str = "moneycontrol_news_playwright.csv"):
        """Save articles to CSV file"""
        try:
            df = pd.DataFrame(articles)
            df.to_csv(filename, index=False, encoding='utf-8')
            logger.info(f"Saved {len(articles)} articles to {filename}")
        except Exception as e:
            logger.error(f"Error saving to CSV: {str(e)}")

    def save_to_excel(self, articles: List[Dict], filename: str = "moneycontrol_news_playwright.xlsx"):
        """Save articles to Excel file"""
        try:
            df = pd.DataFrame(articles)
            df.to_excel(filename, index=False, engine='openpyxl')
            logger.info(f"Saved {len(articles)} articles to {filename}")
        except Exception as e:
            logger.error(f"Error saving to Excel: {str(e)}")


async def main():
    """Main execution function"""
    # Initialize scraper
    scraper = MoneyControlPlaywrightScraper(headless=True)

    # Scrape first 3 pages (you can adjust this)
    num_pages = 3
    logger.info(f"Starting Playwright scraper for {num_pages} pages...")

    articles = await scraper.scrape_multiple_pages(num_pages=num_pages, delay=2.0)

    if articles:
        # Save in multiple formats
        scraper.save_to_json(articles)
        scraper.save_to_csv(articles)

        # Print summary
        print(f"\n{'='*60}")
        print(f"Scraping completed successfully with Playwright!")
        print(f"Total articles scraped: {len(articles)}")
        print(f"{'='*60}\n")

        # Print first few articles as preview
        print("Preview of first 3 articles:\n")
        for i, article in enumerate(articles[:3], 1):
            print(f"{i}. {article.get('title', 'No title')}")
            print(f"   URL: {article.get('url', 'No URL')}")
            print(f"   Date: {article.get('date', 'No date')}")
            print(f"   Summary: {article.get('summary', 'No summary')[:100]}...")
            print()
    else:
        logger.warning("No articles were scraped!")


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
