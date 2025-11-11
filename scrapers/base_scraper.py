#!/usr/bin/env python3
"""
Base Scraper Class with Memory-Efficient Pattern

This module provides an abstract base class for scrapers that implement
memory-efficient patterns like generator-based scraping and batching.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, AsyncIterator, Optional
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """
    Abstract base class for web scrapers with memory-efficient patterns

    Subclasses should implement scrape_page() method and optionally
    override other methods for custom behavior.
    """

    def __init__(self, base_url: str):
        """
        Initialize the base scraper

        Args:
            base_url: Base URL for scraping
        """
        self.base_url = base_url

    @abstractmethod
    async def scrape_page(self, page_number: int) -> List[Dict]:
        """
        Scrape a single page and return articles

        Args:
            page_number: Page number to scrape

        Returns:
            List of article dictionaries
        """
        pass

    async def scrape_pages_generator(
        self,
        num_pages: int = 1,
        delay: float = 2.0
    ) -> AsyncIterator[List[Dict]]:
        """
        Generator that yields articles page by page (memory-efficient)

        This method doesn't accumulate all articles in memory. Instead,
        it yields each page's articles immediately, allowing the caller
        to process/save them incrementally.

        Args:
            num_pages: Number of pages to scrape
            delay: Delay between page requests (seconds)

        Yields:
            List of articles for each page

        Example:
            >>> scraper = MyScraper()
            >>> async for articles in scraper.scrape_pages_generator(num_pages=100):
            ...     save_to_file(articles, f"page_{i}.json")
            ...     # articles for this page are processed and can be freed
        """
        import asyncio

        for page in range(1, num_pages + 1):
            logger.info(f"[GENERATOR] Scraping page {page}/{num_pages}")

            articles = await self.scrape_page(page)

            if articles:
                logger.info(f"[GENERATOR] Yielding {len(articles)} articles from page {page}")
                yield articles
            else:
                logger.warning(f"[GENERATOR] No articles found on page {page}")

            # Be polite - add delay between requests
            if page < num_pages:
                logger.debug(f"[GENERATOR] Waiting {delay} seconds before next page...")
                await asyncio.sleep(delay)

    async def scrape_pages_batched(
        self,
        num_pages: int = 1,
        batch_size: int = 10,
        delay: float = 2.0
    ) -> AsyncIterator[List[Dict]]:
        """
        Scrape pages in batches (memory-efficient with controlled batching)

        This method scrapes multiple pages and accumulates them into batches
        before yielding. Useful when you want to write batches to disk/DB
        but don't want to accumulate all pages in memory.

        Args:
            num_pages: Total number of pages to scrape
            batch_size: Number of pages per batch
            delay: Delay between page requests (seconds)

        Yields:
            List of articles for each batch

        Example:
            >>> scraper = MyScraper()
            >>> batch_num = 0
            >>> async for batch_articles in scraper.scrape_pages_batched(
            ...     num_pages=500, batch_size=50
            ... ):
            ...     save_to_file(batch_articles, f"batch_{batch_num}.json")
            ...     batch_num += 1
        """
        import asyncio

        batch_articles = []
        pages_in_current_batch = 0

        for page in range(1, num_pages + 1):
            logger.info(f"[BATCH] Scraping page {page}/{num_pages} (batch {pages_in_current_batch + 1}/{batch_size})")

            articles = await self.scrape_page(page)

            if articles:
                batch_articles.extend(articles)
                pages_in_current_batch += 1

            # Yield batch when full or at the last page
            if pages_in_current_batch >= batch_size or page == num_pages:
                if batch_articles:
                    logger.info(f"[BATCH] Yielding batch with {len(batch_articles)} articles from {pages_in_current_batch} pages")
                    yield batch_articles

                    # Clear batch to free memory
                    batch_articles = []
                    pages_in_current_batch = 0

            # Be polite - add delay between requests
            if page < num_pages:
                await asyncio.sleep(delay)

    def save_to_json_streaming(
        self,
        articles_iterator,
        filename: str,
        pretty: bool = True
    ):
        """
        Save articles to JSON using streaming (memory-efficient)

        This method writes JSON incrementally as articles come in,
        instead of loading everything into memory before writing.

        Args:
            articles_iterator: Iterator/generator of article lists or single articles
            filename: Output filename
            pretty: Whether to use pretty formatting (indent)

        Example:
            >>> async def scrape():
            ...     scraper = MyScraper()
            ...     generator = scraper.scrape_pages_generator(num_pages=100)
            ...     scraper.save_to_json_streaming_async(generator, "output.json")
        """
        try:
            indent = 2 if pretty else None

            with open(filename, 'w', encoding='utf-8') as f:
                f.write('[\n' if pretty else '[')

                first_article = True
                total_articles = 0

                for batch in articles_iterator:
                    # Handle both List[Dict] and Dict
                    if isinstance(batch, dict):
                        batch = [batch]

                    for article in batch:
                        if not first_article:
                            f.write(',\n' if pretty else ',')
                        first_article = False

                        json_str = json.dumps(article, ensure_ascii=False, indent=indent)

                        if pretty:
                            # Add indentation to each line
                            lines = json_str.split('\n')
                            indented = '\n'.join('  ' + line for line in lines)
                            f.write(indented)
                        else:
                            f.write(json_str)

                        total_articles += 1

                f.write('\n]' if pretty else ']')

            logger.info(f"[STREAMING] Saved {total_articles} articles to {filename}")

        except Exception as e:
            logger.error(f"[STREAMING] Error saving to JSON: {str(e)}")
            raise

    async def save_to_json_streaming_async(
        self,
        articles_async_iterator: AsyncIterator,
        filename: str,
        pretty: bool = True
    ):
        """
        Save articles to JSON using async streaming (memory-efficient)

        Async version of save_to_json_streaming for use with async generators.

        Args:
            articles_async_iterator: Async iterator/generator of article lists
            filename: Output filename
            pretty: Whether to use pretty formatting (indent)
        """
        try:
            indent = 2 if pretty else None

            with open(filename, 'w', encoding='utf-8') as f:
                f.write('[\n' if pretty else '[')

                first_article = True
                total_articles = 0

                async for batch in articles_async_iterator:
                    # Handle both List[Dict] and Dict
                    if isinstance(batch, dict):
                        batch = [batch]

                    for article in batch:
                        if not first_article:
                            f.write(',\n' if pretty else ',')
                        first_article = False

                        json_str = json.dumps(article, ensure_ascii=False, indent=indent)

                        if pretty:
                            # Add indentation to each line
                            lines = json_str.split('\n')
                            indented = '\n'.join('  ' + line for line in lines)
                            f.write(indented)
                        else:
                            f.write(json_str)

                        total_articles += 1

                f.write('\n]' if pretty else ']')

            logger.info(f"[STREAMING] Saved {total_articles} articles to {filename}")

        except Exception as e:
            logger.error(f"[STREAMING] Error saving to JSON: {str(e)}")
            raise

    @staticmethod
    def merge_json_files(input_files: List[str], output_file: str):
        """
        Merge multiple JSON files into one

        Useful when you've saved batches separately and want to combine them.

        Args:
            input_files: List of input JSON filenames
            output_file: Output filename for merged JSON
        """
        try:
            all_articles = []

            for input_file in input_files:
                if not Path(input_file).exists():
                    logger.warning(f"[MERGE] File not found, skipping: {input_file}")
                    continue

                with open(input_file, 'r', encoding='utf-8') as f:
                    articles = json.load(f)
                    all_articles.extend(articles)
                    logger.info(f"[MERGE] Loaded {len(articles)} articles from {input_file}")

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_articles, f, ensure_ascii=False, indent=2)

            logger.info(f"[MERGE] Merged {len(all_articles)} articles into {output_file}")

        except Exception as e:
            logger.error(f"[MERGE] Error merging JSON files: {str(e)}")
            raise
