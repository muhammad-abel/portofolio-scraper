#!/usr/bin/env python3
"""
Moneycontrol News Scraper (Selenium version)
Use this if the regular scraper doesn't work due to JavaScript rendering
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import json
import time
import logging
from datetime import datetime
from typing import List, Dict
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper_selenium.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class MoneyControlSeleniumScraper:
    """Selenium-based scraper for Moneycontrol news"""

    def __init__(self, base_url: str = "https://www.moneycontrol.com/news/business/markets/", headless: bool = True):
        """
        Initialize the Selenium scraper

        Args:
            base_url: Base URL for the markets section
            headless: Run browser in headless mode
        """
        self.base_url = base_url
        self.headless = headless
        self.driver = None

    def initialize_driver(self):
        """Initialize Chrome WebDriver"""
        try:
            chrome_options = Options()

            if self.headless:
                chrome_options.add_argument('--headless')
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-dev-shm-usage')

            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')

            # Use webdriver-manager to automatically download chromedriver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info("Chrome WebDriver initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing WebDriver: {str(e)}")
            raise

    def close_driver(self):
        """Close the WebDriver"""
        if self.driver:
            self.driver.quit()
            logger.info("WebDriver closed")

    def scrape_page(self, page_number: int = 1) -> List[Dict]:
        """
        Scrape articles from a single page using Selenium

        Args:
            page_number: Page number to scrape

        Returns:
            List of article dictionaries
        """
        if not self.driver:
            self.initialize_driver()

        url = f"{self.base_url}page-{page_number}/"
        articles = []

        try:
            logger.info(f"Loading page {page_number}: {url}")
            self.driver.get(url)

            # Wait for articles to load
            wait = WebDriverWait(self.driver, 10)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

            # Scroll to load lazy content
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

            # Get page source and parse with BeautifulSoup
            soup = BeautifulSoup(self.driver.page_source, 'lxml')

            # Find article elements - adjust selectors based on actual page structure
            article_elements = (
                soup.find_all('li', class_='clearfix') or
                soup.find_all('div', class_='article') or
                soup.find_all('article')
            )

            logger.info(f"Found {len(article_elements)} article elements on page {page_number}")

            for article_elem in article_elements:
                article_data = self.extract_article_data(article_elem)
                if article_data:
                    articles.append(article_data)

            logger.info(f"Successfully extracted {len(articles)} articles from page {page_number}")

        except Exception as e:
            logger.error(f"Error scraping page {page_number}: {str(e)}")

        return articles

    def extract_article_data(self, article_element) -> Dict:
        """
        Extract data from article element

        Args:
            article_element: BeautifulSoup element

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
                    article_data['url'] = link_elem.get('href', '')
                else:
                    article_data['title'] = title_elem.get_text(strip=True)
                    article_data['url'] = ''

            # Extract date
            date_elem = article_element.find('span', class_='article-time') or \
                       article_element.find('time') or \
                       article_element.find('span', class_='date')
            article_data['date'] = date_elem.get_text(strip=True) if date_elem else ''

            # Extract summary
            summary_elem = article_element.find('p')
            article_data['summary'] = summary_elem.get_text(strip=True) if summary_elem else ''

            # Extract image
            img_elem = article_element.find('img')
            article_data['image_url'] = img_elem.get('src', '') if img_elem else ''

            # Extract author
            author_elem = article_element.find('span', class_='author')
            article_data['author'] = author_elem.get_text(strip=True) if author_elem else ''

            # Metadata
            article_data['scraped_at'] = datetime.now().isoformat()

            if article_data.get('title'):
                return article_data
            return None

        except Exception as e:
            logger.error(f"Error extracting article: {str(e)}")
            return None

    def scrape_multiple_pages(self, num_pages: int = 1, delay: float = 2.0) -> List[Dict]:
        """
        Scrape multiple pages

        Args:
            num_pages: Number of pages to scrape
            delay: Delay between pages

        Returns:
            List of all articles
        """
        all_articles = []

        try:
            for page in range(1, num_pages + 1):
                logger.info(f"Scraping page {page}/{num_pages}")
                articles = self.scrape_page(page)
                all_articles.extend(articles)

                if page < num_pages:
                    logger.info(f"Waiting {delay} seconds...")
                    time.sleep(delay)

            logger.info(f"Total articles scraped: {len(all_articles)}")

        finally:
            self.close_driver()

        return all_articles

    def save_to_json(self, articles: List[Dict], filename: str = "moneycontrol_news_selenium.json"):
        """Save to JSON"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved to {filename}")

    def save_to_csv(self, articles: List[Dict], filename: str = "moneycontrol_news_selenium.csv"):
        """Save to CSV"""
        df = pd.DataFrame(articles)
        df.to_csv(filename, index=False, encoding='utf-8')
        logger.info(f"Saved to {filename}")


def main():
    """Main execution"""
    scraper = MoneyControlSeleniumScraper(headless=True)

    num_pages = 3
    logger.info(f"Starting Selenium scraper for {num_pages} pages...")

    articles = scraper.scrape_multiple_pages(num_pages=num_pages, delay=2.0)

    if articles:
        scraper.save_to_json(articles)
        scraper.save_to_csv(articles)

        print(f"\n{'='*60}")
        print(f"Scraping completed!")
        print(f"Total articles: {len(articles)}")
        print(f"{'='*60}\n")

        for i, article in enumerate(articles[:3], 1):
            print(f"{i}. {article.get('title', 'No title')}")
            print(f"   URL: {article.get('url', 'No URL')}")
            print()
    else:
        logger.warning("No articles scraped!")


if __name__ == "__main__":
    main()
