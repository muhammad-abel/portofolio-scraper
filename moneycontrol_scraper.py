#!/usr/bin/env python3
"""
Moneycontrol News Scraper
Scrapes news articles from Moneycontrol markets section
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import time
import logging
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import urljoin
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class MoneyControlScraper:
    """Scraper for Moneycontrol news articles"""

    def __init__(self, base_url: str = "https://www.moneycontrol.com/news/business/markets/"):
        """
        Initialize the scraper

        Args:
            base_url: Base URL for the markets section
        """
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })

    def fetch_page(self, page_number: int = 1, retries: int = 3) -> Optional[BeautifulSoup]:
        """
        Fetch a page from Moneycontrol

        Args:
            page_number: Page number to fetch
            retries: Number of retries on failure

        Returns:
            BeautifulSoup object or None on failure
        """
        url = f"{self.base_url}page-{page_number}/"

        for attempt in range(retries):
            try:
                logger.info(f"Fetching page {page_number} (attempt {attempt + 1}/{retries})")
                response = self.session.get(url, timeout=30)
                response.raise_for_status()

                soup = BeautifulSoup(response.content, 'lxml')
                logger.info(f"Successfully fetched page {page_number}")
                return soup

            except requests.RequestException as e:
                logger.error(f"Error fetching page {page_number}: {str(e)}")
                if attempt < retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.info(f"Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Failed to fetch page {page_number} after {retries} attempts")
                    return None

    def extract_article_data(self, article_element) -> Optional[Dict]:
        """
        Extract data from a single article element

        Args:
            article_element: BeautifulSoup element containing article data

        Returns:
            Dictionary with article data or None
        """
        try:
            # Try different selectors based on common Moneycontrol structures
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

    def scrape_page(self, page_number: int = 1) -> List[Dict]:
        """
        Scrape all articles from a single page

        Args:
            page_number: Page number to scrape

        Returns:
            List of article dictionaries
        """
        soup = self.fetch_page(page_number)
        if not soup:
            return []

        articles = []

        # Try multiple selectors to find article containers
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
        return articles

    def scrape_multiple_pages(self, num_pages: int = 1, delay: float = 2.0) -> List[Dict]:
        """
        Scrape multiple pages

        Args:
            num_pages: Number of pages to scrape
            delay: Delay between page requests (seconds)

        Returns:
            List of all article dictionaries
        """
        all_articles = []

        for page in range(1, num_pages + 1):
            logger.info(f"Scraping page {page}/{num_pages}")
            articles = self.scrape_page(page)
            all_articles.extend(articles)

            # Be polite - add delay between requests
            if page < num_pages:
                logger.info(f"Waiting {delay} seconds before next page...")
                time.sleep(delay)

        logger.info(f"Total articles scraped: {len(all_articles)}")
        return all_articles

    def save_to_json(self, articles: List[Dict], filename: str = "moneycontrol_news.json"):
        """Save articles to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(articles, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved {len(articles)} articles to {filename}")
        except Exception as e:
            logger.error(f"Error saving to JSON: {str(e)}")

    def save_to_csv(self, articles: List[Dict], filename: str = "moneycontrol_news.csv"):
        """Save articles to CSV file"""
        try:
            df = pd.DataFrame(articles)
            df.to_csv(filename, index=False, encoding='utf-8')
            logger.info(f"Saved {len(articles)} articles to {filename}")
        except Exception as e:
            logger.error(f"Error saving to CSV: {str(e)}")

    def save_to_excel(self, articles: List[Dict], filename: str = "moneycontrol_news.xlsx"):
        """Save articles to Excel file"""
        try:
            df = pd.DataFrame(articles)
            df.to_excel(filename, index=False, engine='openpyxl')
            logger.info(f"Saved {len(articles)} articles to {filename}")
        except Exception as e:
            logger.error(f"Error saving to Excel: {str(e)}")


def main():
    """Main execution function"""
    # Initialize scraper
    scraper = MoneyControlScraper()

    # Scrape first 3 pages (you can adjust this)
    num_pages = 3
    logger.info(f"Starting scraper for {num_pages} pages...")

    articles = scraper.scrape_multiple_pages(num_pages=num_pages, delay=2.0)

    if articles:
        # Save in multiple formats
        scraper.save_to_json(articles)
        scraper.save_to_csv(articles)

        # Print summary
        print(f"\n{'='*60}")
        print(f"Scraping completed successfully!")
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
    main()
