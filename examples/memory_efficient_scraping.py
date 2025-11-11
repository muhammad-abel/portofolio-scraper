#!/usr/bin/env python3
"""
Memory-Efficient Scraping Examples

This script demonstrates how to use memory-efficient scraping methods
for large-scale data collection without running out of memory.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scrapers.crawl4ai_scraper import MoneyControlCrawl4AIScraper
from upload_to_mongodb import MongoDBUploader


async def example_1_generator_method():
    """
    Example 1: Using generator method to scrape many pages

    Memory usage: Constant (~50 MB regardless of page count)
    Use case: Very large scraping jobs (500+ pages)
    """
    print("\n" + "="*70)
    print("Example 1: Generator Method (Memory-Efficient)")
    print("="*70 + "\n")

    scraper = MoneyControlCrawl4AIScraper(
        base_url="https://www.moneycontrol.com/news/business/markets/",
        fetch_details=True,
        max_concurrent=5
    )

    page_num = 1
    total_articles = 0

    # Generator yields articles page by page
    async for articles in scraper.scrape_pages_generator(
        num_pages=10,  # Try with 100+ for real test
        delay=2.0
    ):
        print(f"Page {page_num}: Scraped {len(articles)} articles")

        # Process immediately (e.g., save to individual files)
        scraper.save_to_json(articles, f"output/page_{page_num}.json")

        total_articles += len(articles)
        page_num += 1

        # Memory for this page is freed after this iteration

    print(f"\nTotal: {total_articles} articles scraped")
    print("Memory usage: Constant throughout scraping ✅")


async def example_2_batched_method():
    """
    Example 2: Using batched method for balanced approach

    Memory usage: Moderate (~150 MB for batch of 50 pages)
    Use case: Medium-large jobs where you want batch processing
    """
    print("\n" + "="*70)
    print("Example 2: Batched Method (Balanced)")
    print("="*70 + "\n")

    scraper = MoneyControlCrawl4AIScraper(
        base_url="https://www.moneycontrol.com/news/business/markets/",
        fetch_details=True,
        max_concurrent=5
    )

    batch_num = 0
    total_articles = 0

    # Scrape in batches of 10 pages each
    async for batch_articles in scraper.scrape_pages_batched(
        num_pages=20,  # Try with 200+ for real test
        batch_size=10,  # Adjust based on available memory
        delay=2.0
    ):
        print(f"Batch {batch_num}: Scraped {len(batch_articles)} articles")

        # Process batch (e.g., save to batch files)
        scraper.save_to_json(batch_articles, f"output/batch_{batch_num}.json")

        total_articles += len(batch_articles)
        batch_num += 1

        # Memory for this batch is freed after this iteration

    print(f"\nTotal: {total_articles} articles across {batch_num} batches")
    print("Memory usage: Moderate, proportional to batch size ✅")


async def example_3_streaming_json_save():
    """
    Example 3: Using streaming JSON save with generator

    Memory usage: Minimal (writes incrementally)
    Use case: Single large output file without memory accumulation
    """
    print("\n" + "="*70)
    print("Example 3: Streaming JSON Save (Single File)")
    print("="*70 + "\n")

    scraper = MoneyControlCrawl4AIScraper(
        base_url="https://www.moneycontrol.com/news/business/markets/",
        fetch_details=True,
        max_concurrent=5
    )

    # Create generator
    generator = scraper.scrape_pages_generator(
        num_pages=10,  # Try with 100+ for real test
        delay=2.0
    )

    # Save to single file with streaming (memory-efficient)
    output_file = "output/streaming_output.json"
    print(f"Saving to {output_file} with streaming...")

    await scraper.save_to_json_streaming(generator, output_file)

    print(f"\n✅ Done! All data saved to {output_file}")
    print("Memory usage: Minimal (incremental writes) ✅")


async def example_4_streaming_mongodb_upload():
    """
    Example 4: Direct streaming upload to MongoDB

    Memory usage: Minimal (uploads in batches)
    Use case: Direct database upload for large datasets
    """
    print("\n" + "="*70)
    print("Example 4: Streaming MongoDB Upload")
    print("="*70 + "\n")

    # Initialize scraper
    scraper = MoneyControlCrawl4AIScraper(
        base_url="https://www.moneycontrol.com/news/business/markets/",
        fetch_details=True,
        max_concurrent=5
    )

    # Initialize MongoDB uploader
    uploader = MongoDBUploader(
        connection_string="mongodb://localhost:27017/",
        database_name="moneycontrol_db",
        collection_name="news_articles"
    )

    try:
        # Connect to MongoDB
        if not uploader.connect():
            print("❌ Failed to connect to MongoDB")
            print("Make sure MongoDB is running or skip this example")
            return

        uploader.create_indexes()

        # Create generator
        generator = scraper.scrape_pages_generator(
            num_pages=10,  # Try with 100+ for real test
            delay=2.0
        )

        # Upload directly from generator (memory-efficient)
        print("Uploading to MongoDB with streaming...")
        stats = await uploader.upload_articles_streaming_async(
            generator,
            batch_size=50  # Upload every 50 articles
        )

        print(f"\n✅ Upload completed!")
        print(f"  - Inserted: {stats['inserted']}")
        print(f"  - Updated: {stats['updated']}")
        print(f"  - Skipped: {stats['skipped']}")
        print(f"  - Failed: {stats['failed']}")
        print("Memory usage: Minimal (batched uploads) ✅")

        # Show collection stats
        uploader.get_collection_stats()

    except Exception as e:
        print(f"❌ Error: {e}")
        print("Skipping MongoDB example (MongoDB might not be running)")

    finally:
        uploader.close()


async def example_5_comparison():
    """
    Example 5: Comparing standard vs generator method

    Demonstrates the memory difference between methods
    """
    print("\n" + "="*70)
    print("Example 5: Memory Comparison (Standard vs Generator)")
    print("="*70 + "\n")

    print("For detailed memory profiling, use:")
    print("  python tools/memory_profiler.py --pages 50 --method compare")
    print("\nThis will show actual memory usage for each method.")


async def main():
    """Main function to run all examples"""
    print("\n" + "#"*70)
    print("# Memory-Efficient Scraping Examples")
    print("#"*70)

    # Create output directory
    Path("output").mkdir(exist_ok=True)

    # Run examples
    # Uncomment the examples you want to run

    # Example 1: Generator method
    await example_1_generator_method()

    # Example 2: Batched method
    # await example_2_batched_method()

    # Example 3: Streaming JSON save
    # await example_3_streaming_json_save()

    # Example 4: MongoDB streaming upload (requires MongoDB)
    # await example_4_streaming_mongodb_upload()

    # Example 5: Memory comparison info
    # await example_5_comparison()

    print("\n" + "="*70)
    print("Examples completed!")
    print("="*70)
    print("\nTips:")
    print("  1. Uncomment other examples in main() to try them")
    print("  2. Increase num_pages to see real memory savings")
    print("  3. Use tools/memory_profiler.py for detailed analysis")
    print("  4. See docs/MEMORY_OPTIMIZATION.md for full guide")
    print("\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nExecution interrupted by user")
        sys.exit(0)
