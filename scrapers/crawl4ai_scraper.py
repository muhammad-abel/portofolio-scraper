#!/usr/bin/env python3
"""
Moneycontrol News Scraper (Crawl4AI version)
Modern async scraper using Crawl4AI - the most powerful choice!
"""

import asyncio
import os
import base64
import hashlib
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from bs4 import BeautifulSoup
import pandas as pd
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional
import sys
import argparse
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

    def __init__(self, base_url: str = "https://www.moneycontrol.com/news/business/markets/", fetch_details: bool = True, max_concurrent: int = 5):
        """
        Initialize the Crawl4AI scraper

        Args:
            base_url: Base URL for the markets section
            fetch_details: If True, fetch date & author from detail pages
            max_concurrent: Maximum concurrent detail page requests (default: 5)
        """
        self.base_url = base_url
        self.fetch_details = fetch_details
        self.max_concurrent = max_concurrent  # Limit concurrent requests

    @staticmethod
    def generate_article_hash(title: str, date: str) -> str:
        """
        Generate unique hash from title and date using base64 encoding

        Args:
            title: Article title
            date: Article date

        Returns:
            Base64 encoded hash string
        """
        # Combine title and date, normalize to lowercase and strip whitespace
        combined = f"{title.lower().strip()}|{date.lower().strip()}"

        # Create SHA256 hash
        hash_object = hashlib.sha256(combined.encode('utf-8'))

        # Convert to base64 and decode to string
        base64_hash = base64.b64encode(hash_object.digest()).decode('utf-8')

        return base64_hash

    async def fetch_article_details(self, url: str, crawler: AsyncWebCrawler, retries: int = 2) -> Dict[str, str]:
        """
        Fetch date, author, and full content from article detail page with retry

        Args:
            url: URL of the article
            crawler: AsyncWebCrawler instance
            retries: Number of retries on failure

        Returns:
            Dictionary with date, author, and full_content
        """
        for attempt in range(retries):
            try:
                logger.info(f"Fetching details from: {url} (attempt {attempt + 1}/{retries})")

                result = await crawler.arun(
                    url=url,
                    word_count_threshold=10,
                    bypass_cache=True,
                    wait_for="body",
                    page_timeout=120000,  # Increase timeout to 120 seconds
                    delay_before_return_html=1.0  # Wait 1s before extracting
                )

                if not result.success:
                    logger.error(f"Failed to fetch details from {url}: {result.error_message}")
                    if attempt < retries - 1:
                        wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                        logger.info(f"Retrying in {wait_time} seconds...")
                        await asyncio.sleep(wait_time)
                        continue
                    return {'date': '', 'author': '', 'full_content': ''}

                soup = BeautifulSoup(result.html, 'lxml')

                # Extract author from <div class="article_author"> <a>
                author = ''
                author_elem = soup.find('div', class_='article_author')
                if author_elem:
                    author_link = author_elem.find('a')
                    if author_link:
                        # Primary: extract from <a> tag
                        author = author_link.get_text(strip=True)
                    else:
                        # Fallback: extract directly from div if no <a> tag
                        author = author_elem.get_text(strip=True)

                # Extract date from <div class="article_schedule"> <span>
                date = ''
                date_elem = soup.find('div', class_='article_schedule')
                if date_elem:
                    date_span = date_elem.find('span')
                    if date_span:
                        date_text = date_span.get_text(strip=True)
                        # Extract just the date part (before '/')
                        date = date_text.split('/')[0].strip() if '/' in date_text else date_text

                # Fallback for date: Try <p class="... date">
                if not date:
                    date_p = soup.find('p', class_=lambda x: x and 'date' in x)
                    if date_p:
                        # Get text directly from <p>, excluding text from child elements
                        date_text = date_p.get_text(strip=True)
                        # Remove time portion if present (e.g., "· 10:51 IST")
                        if '·' in date_text:
                            date = date_text.split('·')[0].strip()
                        else:
                            date = date_text

                # Extract full content from <div class="content_wrapper arti-flow" id="contentdata">
                full_content = ''
                content_wrapper = soup.find('div', {'class': 'content_wrapper arti-flow', 'id': 'contentdata'})
                if content_wrapper:
                    # Get all <p> tags inside content_wrapper
                    paragraphs = content_wrapper.find_all('p')
                    # Join all paragraph texts with newlines
                    full_content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])

                # FALLBACK: Try alternative format if any field is missing
                # Some articles use video_content format
                if not author or not date or not full_content:
                    logger.debug(f"Trying fallback extraction for {url}")

                    video_content = soup.find('div', class_='video_content')
                    if video_content:
                        # Try to extract date from <p class="last_updated">
                        if not date:
                            last_updated = video_content.find('p', class_='last_updated')
                            if last_updated:
                                date_text = last_updated.get_text(strip=True)
                                # Extract date after "first published:" or similar text
                                if 'first published:' in date_text.lower():
                                    date = date_text.split(':', 1)[1].strip() if ':' in date_text else date_text
                                else:
                                    date = date_text

                        # Try to extract full content from <p class="text_3">
                        if not full_content:
                            text_3 = video_content.find('p', class_='text_3')
                            if text_3:
                                full_content = text_3.get_text(strip=True)

                        # Author might not be available in video format, keep empty if not found
                        logger.debug(f"[FALLBACK] Used video_content format for {url}")

                if full_content:
                    logger.debug(f"[SUCCESS] Extracted from {url}: author={author}, date={date}, content_length={len(full_content)}")
                else:
                    logger.debug(f"[SUCCESS] Extracted from {url}: author={author}, date={date} (no full_content found)")

                return {'date': date, 'author': author, 'full_content': full_content}

            except asyncio.TimeoutError:
                logger.error(f"[TIMEOUT] Timeout fetching {url} (attempt {attempt + 1}/{retries})")
                if attempt < retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                return {'date': '', 'author': '', 'full_content': ''}

            except Exception as e:
                logger.error(f"[ERROR] Error fetching details from {url} (attempt {attempt + 1}/{retries}): {str(e)}")
                if attempt < retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                return {'date': '', 'author': '', 'full_content': ''}

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
                    logger.info(f"Fetching details for {len(articles)} articles (max {self.max_concurrent} concurrent)...")

                    # Fetch details with concurrency limit using semaphore
                    semaphore = asyncio.Semaphore(self.max_concurrent)

                    async def fetch_with_semaphore(article):
                        async with semaphore:
                            detail = await self.fetch_article_details(article['url'], crawler)
                            # Small random delay to avoid detection
                            await asyncio.sleep(0.5 + (hash(article['url']) % 10) / 10)  # 0.5-1.5s
                            return detail

                    # Fetch details for all articles with limited concurrency
                    detail_tasks = [fetch_with_semaphore(article) for article in articles]
                    details = await asyncio.gather(*detail_tasks, return_exceptions=True)

                    # Update articles with fetched details
                    success_count = 0
                    for article, detail in zip(articles, details):
                        if isinstance(detail, dict):
                            article['date'] = detail.get('date', '')
                            article['author'] = detail.get('author', '')
                            article['full_content'] = detail.get('full_content', '')

                            # Generate unique hash from title and date
                            article['hash'] = self.generate_article_hash(
                                article.get('title', ''),
                                article.get('date', '')
                            )

                            if detail.get('date') or detail.get('author') or detail.get('full_content'):
                                success_count += 1
                        else:
                            # Exception occurred
                            article['date'] = ''
                            article['author'] = ''
                            article['full_content'] = ''
                            article['hash'] = self.generate_article_hash(
                                article.get('title', ''),
                                ''
                            )
                            logger.warning(f"Failed to fetch details for: {article['url']}")

                    logger.info(f"[SUCCESS] Successfully fetched details for {success_count}/{len(articles)} articles")

                else:
                    # If not fetching details, generate hash from title only (or with empty date)
                    for article in articles:
                        article['hash'] = self.generate_article_hash(
                            article.get('title', ''),
                            article.get('date', '')  # Will use date from list page if available
                        )

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
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Moneycontrol News Scraper with Crawl4AI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scrapers/crawl4ai_scraper.py --pages 5
  python scrapers/crawl4ai_scraper.py --pages 10 --upload-mongo
  python scrapers/crawl4ai_scraper.py --pages 3 --max-concurrent 3 --upload-mongo
        """
    )
    parser.add_argument(
        '--pages',
        type=int,
        default=3,
        help='Number of pages to scrape (default: 3)'
    )
    parser.add_argument(
        '--max-concurrent',
        type=int,
        default=5,
        help='Maximum concurrent requests for detail pages (default: 5)'
    )
    parser.add_argument(
        '--delay',
        type=float,
        default=2.0,
        help='Delay between page requests in seconds (default: 2.0)'
    )
    parser.add_argument(
        '--upload-mongo',
        action='store_true',
        help='Upload results to MongoDB after scraping'
    )
    parser.add_argument(
        '--no-details',
        action='store_true',
        help='Skip fetching article details (date, author, full_content)'
    )

    args = parser.parse_args()

    # Initialize scraper with concurrency limit
    scraper = MoneyControlCrawl4AIScraper(
        fetch_details=not args.no_details,
        max_concurrent=args.max_concurrent
    )

    logger.info(f"Starting Crawl4AI scraper for {args.pages} pages with max {scraper.max_concurrent} concurrent requests...")

    articles = await scraper.scrape_multiple_pages(num_pages=args.pages, delay=args.delay)

    if articles:
        # Save to local files only if NOT uploading to MongoDB
        if not args.upload_mongo:
            json_filename = "moneycontrol_news_crawl4ai.json"
            scraper.save_to_json(articles, json_filename)
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
            print(f"   Hash: {article.get('hash', 'No hash')}")
            print(f"   Date: {article.get('date', 'No date')}")
            print(f"   Author: {article.get('author', 'No author')}")
            print(f"   Summary: {article.get('summary', 'No summary')[:100]}...")
            if article.get('full_content'):
                print(f"   Full Content: {article.get('full_content', '')[:100]}...")
            print()

        # Upload to MongoDB if flag is set
        if args.upload_mongo:
            print(f"\n{'='*60}")
            print("Uploading to MongoDB...")
            print(f"{'='*60}\n")

            try:
                # Import MongoDB uploader
                sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                from upload_to_mongodb import MongoDBUploader, MONGODB_CONNECTION_STRING, DATABASE_NAME, COLLECTION_NAME

                # Initialize uploader
                uploader = MongoDBUploader(
                    connection_string=MONGODB_CONNECTION_STRING,
                    database_name=DATABASE_NAME,
                    collection_name=COLLECTION_NAME
                )

                # Connect to MongoDB
                if uploader.connect():
                    # Create indexes
                    uploader.create_indexes()

                    # Upload articles
                    stats = uploader.upload_articles(articles, upsert=True)

                    # Display statistics
                    uploader.get_collection_stats()

                    print(f"\n{'='*60}")
                    print("MongoDB Upload Summary:")
                    print(f"  - Inserted: {stats['inserted']}")
                    print(f"  - Updated: {stats['updated']}")
                    print(f"  - Skipped: {stats['skipped']}")
                    print(f"  - Failed: {stats['failed']}")
                    print(f"{'='*60}\n")

                    # Close connection
                    uploader.close()
                else:
                    logger.error("Failed to connect to MongoDB. Please check your configuration.")

            except ImportError as e:
                logger.error(f"Failed to import MongoDB uploader: {e}")
                logger.error("Make sure pymongo is installed: pip install pymongo")
            except Exception as e:
                logger.error(f"Error uploading to MongoDB: {e}")

    else:
        logger.warning("No articles were scraped!")


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
