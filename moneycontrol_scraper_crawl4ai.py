#!/usr/bin/env python3
"""
Moneycontrol News Scraper (Crawl4AI version)
Modern async scraper using Crawl4AI - the most powerful choice!
"""

import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import LLMExtractionStrategy
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
        logging.FileHandler('scraper_crawl4ai.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class MoneyControlCrawl4AIScraper:
    """Modern async scraper using Crawl4AI"""

    def __init__(self, base_url: str = "https://www.moneycontrol.com/news/business/markets/", fetch_details: bool = True):
        """
        Initialize the Crawl4AI scraper

        Args:
            base_url: Base URL for the markets section
            fetch_details: If True, fetch date & author from detail pages
        """
        self.base_url = base_url
        self.fetch_details = fetch_details

    async def fetch_article_details(self, url: str, crawler: AsyncWebCrawler) -> Dict[str, str]:
        """
        Fetch date and author from article detail page

        Args:
            url: URL of the article
            crawler: AsyncWebCrawler instance

        Returns:
            Dictionary with date and author
        """
        try:
            logger.info(f"Fetching details from: {url}")

            result = await crawler.arun(
                url=url,
                word_count_threshold=10,
                bypass_cache=True,
                wait_for="body"
            )

            if not result.success:
                logger.error(f"Failed to fetch details from {url}")
                return {'date': '', 'author': ''}

            soup = BeautifulSoup(result.html, 'lxml')

            # Extract author from <div class="article_author"> <a>
            author = ''
            author_elem = soup.find('div', class_='article_author')
            if author_elem:
                author_link = author_elem.find('a')
                author = author_link.get_text(strip=True) if author_link else ''

            # Extract date from <div class="article_schedule"> <span>
            date = ''
            date_elem = soup.find('div', class_='article_schedule')
            if date_elem:
                date_span = date_elem.find('span')
                if date_span:
                    date_text = date_span.get_text(strip=True)
                    # Extract just the date part (before '/')
                    date = date_text.split('/')[0].strip() if '/' in date_text else date_text

            logger.debug(f"Extracted from {url}: author={author}, date={date}")
            return {'date': date, 'author': author}

        except Exception as e:
            logger.error(f"Error fetching details from {url}: {str(e)}")
            return {'date': '', 'author': ''}

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

            # Extract link first (struktur: <li> -> <a href="URL" class="unified-link">)
            link_elem = article_element.find('a', class_='unified-link') or article_element.find('a')

            if link_elem:
                # Get URL from <a href="">
                href = link_elem.get('href', '')
                article_data['url'] = href if href.startswith('http') else urljoin(self.base_url, href)

                # Get title from <h2> inside <a>
                title_elem = link_elem.find('h2')
                article_data['title'] = title_elem.get_text(strip=True) if title_elem else ''

                # Get image from <img> inside <a>
                img_elem = link_elem.find('img')
                if img_elem:
                    # Try 'src' first, then 'data-src' for lazy loading
                    article_data['image_url'] = img_elem.get('src') or img_elem.get('data-src') or img_elem.get('data', '')
                else:
                    article_data['image_url'] = ''
            else:
                # Fallback jika struktur berbeda
                article_data['url'] = ''
                article_data['title'] = ''
                article_data['image_url'] = ''

            # Extract summary from <p> (outside <a>, sibling of <a>)
            summary_elem = article_element.find('p')
            article_data['summary'] = summary_elem.get_text(strip=True) if summary_elem else ''

            # Extract date
            date_elem = article_element.find('span', class_='article-time') or \
                       article_element.find('time') or \
                       article_element.find('span', class_='date')
            article_data['date'] = date_elem.get_text(strip=True) if date_elem else ''

            # Extract author if available
            author_elem = article_element.find('span', class_='author') or \
                         article_element.find('a', class_='author')
            article_data['author'] = author_elem.get_text(strip=True) if author_elem else ''

            # Add metadata
            article_data['scraped_at'] = datetime.now().isoformat()

            # Only return if we have at least a title and URL
            if article_data.get('title') and article_data.get('url'):
                return article_data
            return None

        except Exception as e:
            logger.error(f"Error extracting article data: {str(e)}")
            return None

    async def scrape_page(self, page_number: int = 1) -> List[Dict]:
        """
        Scrape all articles from a single page using Crawl4AI

        Args:
            page_number: Page number to scrape

        Returns:
            List of article dictionaries
        """
        url = f"{self.base_url}page-{page_number}/"
        articles = []

        try:
            async with AsyncWebCrawler(verbose=True) as crawler:
                logger.info(f"Crawling page {page_number}: {url}")

                # Crawl the page
                result = await crawler.arun(
                    url=url,
                    word_count_threshold=10,
                    bypass_cache=True,
                    wait_for="body",
                    js_code=[
                        "window.scrollTo(0, document.body.scrollHeight);",
                    ],
                )

                if not result.success:
                    logger.error(f"Failed to crawl page {page_number}: {result.error_message}")
                    return []

                # Parse the HTML content
                soup = BeautifulSoup(result.html, 'lxml')

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

                # Fetch details (date & author) from each article page
                if self.fetch_details and articles:
                    logger.info(f"Fetching details for {len(articles)} articles...")

                    # Fetch details for all articles in parallel
                    detail_tasks = [
                        self.fetch_article_details(article['url'], crawler)
                        for article in articles
                    ]

                    details = await asyncio.gather(*detail_tasks)

                    # Update articles with fetched details
                    for article, detail in zip(articles, details):
                        article['date'] = detail['date']
                        article['author'] = detail['author']

                    logger.info(f"Successfully fetched details for {len(articles)} articles")

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

        for page in range(1, num_pages + 1):
            logger.info(f"Scraping page {page}/{num_pages}")
            articles = await self.scrape_page(page)
            all_articles.extend(articles)

            # Be polite - add delay between requests
            if page < num_pages:
                logger.info(f"Waiting {delay} seconds before next page...")
                await asyncio.sleep(delay)

        logger.info(f"Total articles scraped: {len(all_articles)}")
        return all_articles

    def save_to_json(self, articles: List[Dict], filename: str = "moneycontrol_news_crawl4ai.json"):
        """Save articles to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(articles, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved {len(articles)} articles to {filename}")
        except Exception as e:
            logger.error(f"Error saving to JSON: {str(e)}")

    def save_to_csv(self, articles: List[Dict], filename: str = "moneycontrol_news_crawl4ai.csv"):
        """Save articles to CSV file"""
        try:
            df = pd.DataFrame(articles)
            df.to_csv(filename, index=False, encoding='utf-8')
            logger.info(f"Saved {len(articles)} articles to {filename}")
        except Exception as e:
            logger.error(f"Error saving to CSV: {str(e)}")

    def save_to_excel(self, articles: List[Dict], filename: str = "moneycontrol_news_crawl4ai.xlsx"):
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
    scraper = MoneyControlCrawl4AIScraper()

    # Scrape first 3 pages (you can adjust this)
    num_pages = 3
    logger.info(f"Starting Crawl4AI scraper for {num_pages} pages...")

    articles = await scraper.scrape_multiple_pages(num_pages=num_pages, delay=2.0)

    if articles:
        # Save in multiple formats
        scraper.save_to_json(articles)
        scraper.save_to_csv(articles)

        # Print summary
        print(f"\n{'='*60}")
        print(f"Scraping completed successfully with Crawl4AI!")
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
