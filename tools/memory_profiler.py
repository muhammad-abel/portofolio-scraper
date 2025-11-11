#!/usr/bin/env python3
"""
Memory Profiling Utility for Web Scrapers

This script helps profile memory usage of scraping operations
to identify memory bottlenecks and validate optimization efforts.

Usage:
    python tools/memory_profiler.py --pages 10 --method standard
    python tools/memory_profiler.py --pages 100 --method generator --category world
    python tools/memory_profiler.py --pages 500 --method batched --batch-size 50
"""

import asyncio
import tracemalloc
import sys
import argparse
import time
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scrapers.crawl4ai_scraper import MoneyControlCrawl4AIScraper, CATEGORIES


def format_bytes(bytes_value: int) -> str:
    """Format bytes to human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} TB"


async def profile_standard_method(scraper, num_pages: int, delay: float):
    """Profile the standard scrape_multiple_pages method"""
    print(f"\n{'='*70}")
    print(f"Profiling STANDARD method (accumulates all in memory)")
    print(f"{'='*70}\n")

    tracemalloc.start()
    start_time = time.time()

    # Take snapshot before
    snapshot1 = tracemalloc.take_snapshot()

    # Scrape
    articles = await scraper.scrape_multiple_pages(num_pages=num_pages, delay=delay)

    # Take snapshot after
    snapshot2 = tracemalloc.take_snapshot()
    elapsed_time = time.time() - start_time

    # Calculate statistics
    current, peak = tracemalloc.get_traced_memory()
    top_stats = snapshot2.compare_to(snapshot1, 'lineno')

    print(f"\n{'='*70}")
    print(f"STANDARD METHOD RESULTS")
    print(f"{'='*70}")
    print(f"Articles scraped: {len(articles)}")
    print(f"Time elapsed: {elapsed_time:.2f} seconds")
    print(f"Current memory: {format_bytes(current)}")
    print(f"Peak memory: {format_bytes(peak)}")
    print(f"Memory per article: {format_bytes(peak / len(articles)) if articles else 'N/A'}")
    print(f"\nTop 5 memory allocations:")
    for stat in top_stats[:5]:
        print(f"  {stat}")
    print(f"{'='*70}\n")

    tracemalloc.stop()

    return {
        "method": "standard",
        "articles": len(articles),
        "time": elapsed_time,
        "current_memory": current,
        "peak_memory": peak,
        "memory_per_article": peak / len(articles) if articles else 0
    }


async def profile_generator_method(scraper, num_pages: int, delay: float):
    """Profile the generator method (memory-efficient)"""
    print(f"\n{'='*70}")
    print(f"Profiling GENERATOR method (memory-efficient)")
    print(f"{'='*70}\n")

    tracemalloc.start()
    start_time = time.time()

    # Take snapshot before
    snapshot1 = tracemalloc.take_snapshot()

    # Scrape with generator
    total_articles = 0
    async for articles in scraper.scrape_pages_generator(num_pages=num_pages, delay=delay):
        total_articles += len(articles)
        # Simulate processing (articles go out of scope)
        del articles

    # Take snapshot after
    snapshot2 = tracemalloc.take_snapshot()
    elapsed_time = time.time() - start_time

    # Calculate statistics
    current, peak = tracemalloc.get_traced_memory()
    top_stats = snapshot2.compare_to(snapshot1, 'lineno')

    print(f"\n{'='*70}")
    print(f"GENERATOR METHOD RESULTS")
    print(f"{'='*70}")
    print(f"Articles scraped: {total_articles}")
    print(f"Time elapsed: {elapsed_time:.2f} seconds")
    print(f"Current memory: {format_bytes(current)}")
    print(f"Peak memory: {format_bytes(peak)}")
    print(f"Memory per article: {format_bytes(peak / total_articles) if total_articles else 'N/A'}")
    print(f"\nTop 5 memory allocations:")
    for stat in top_stats[:5]:
        print(f"  {stat}")
    print(f"{'='*70}\n")

    tracemalloc.stop()

    return {
        "method": "generator",
        "articles": total_articles,
        "time": elapsed_time,
        "current_memory": current,
        "peak_memory": peak,
        "memory_per_article": peak / total_articles if total_articles else 0
    }


async def profile_batched_method(scraper, num_pages: int, batch_size: int, delay: float):
    """Profile the batched method (memory-efficient with batching)"""
    print(f"\n{'='*70}")
    print(f"Profiling BATCHED method (batch_size={batch_size})")
    print(f"{'='*70}\n")

    tracemalloc.start()
    start_time = time.time()

    # Take snapshot before
    snapshot1 = tracemalloc.take_snapshot()

    # Scrape with batching
    total_articles = 0
    async for batch_articles in scraper.scrape_pages_batched(
        num_pages=num_pages,
        batch_size=batch_size,
        delay=delay
    ):
        total_articles += len(batch_articles)
        # Simulate processing (batch goes out of scope)
        del batch_articles

    # Take snapshot after
    snapshot2 = tracemalloc.take_snapshot()
    elapsed_time = time.time() - start_time

    # Calculate statistics
    current, peak = tracemalloc.get_traced_memory()
    top_stats = snapshot2.compare_to(snapshot1, 'lineno')

    print(f"\n{'='*70}")
    print(f"BATCHED METHOD RESULTS")
    print(f"{'='*70}")
    print(f"Articles scraped: {total_articles}")
    print(f"Time elapsed: {elapsed_time:.2f} seconds")
    print(f"Current memory: {format_bytes(current)}")
    print(f"Peak memory: {format_bytes(peak)}")
    print(f"Memory per article: {format_bytes(peak / total_articles) if total_articles else 'N/A'}")
    print(f"\nTop 5 memory allocations:")
    for stat in top_stats[:5]:
        print(f"  {stat}")
    print(f"{'='*70}\n")

    tracemalloc.stop()

    return {
        "method": "batched",
        "batch_size": batch_size,
        "articles": total_articles,
        "time": elapsed_time,
        "current_memory": current,
        "peak_memory": peak,
        "memory_per_article": peak / total_articles if total_articles else 0
    }


async def compare_methods(num_pages: int, batch_size: int, delay: float, category: str):
    """Compare all three methods"""
    print(f"\n{'#'*70}")
    print(f"# MEMORY PROFILING COMPARISON")
    print(f"# Pages: {num_pages}, Category: {category}, Delay: {delay}s")
    print(f"# Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*70}\n")

    base_url = CATEGORIES[category]
    results = []

    # Profile standard method
    scraper = MoneyControlCrawl4AIScraper(base_url=base_url, fetch_details=False)
    result = await profile_standard_method(scraper, num_pages, delay)
    results.append(result)

    # Wait a bit between tests
    await asyncio.sleep(2)

    # Profile generator method
    scraper = MoneyControlCrawl4AIScraper(base_url=base_url, fetch_details=False)
    result = await profile_generator_method(scraper, num_pages, delay)
    results.append(result)

    # Wait a bit between tests
    await asyncio.sleep(2)

    # Profile batched method
    scraper = MoneyControlCrawl4AIScraper(base_url=base_url, fetch_details=False)
    result = await profile_batched_method(scraper, num_pages, batch_size, delay)
    results.append(result)

    # Print comparison summary
    print(f"\n{'='*70}")
    print(f"COMPARISON SUMMARY")
    print(f"{'='*70}")
    print(f"{'Method':<15} {'Articles':<12} {'Time (s)':<12} {'Peak Memory':<15} {'Memory/Article':<15}")
    print(f"{'-'*70}")

    for result in results:
        method_name = result['method'].upper()
        if result['method'] == 'batched':
            method_name += f" ({result['batch_size']})"

        print(
            f"{method_name:<15} "
            f"{result['articles']:<12} "
            f"{result['time']:<12.2f} "
            f"{format_bytes(result['peak_memory']):<15} "
            f"{format_bytes(result['memory_per_article']):<15}"
        )

    print(f"{'='*70}")

    # Calculate improvements
    standard_peak = results[0]['peak_memory']
    generator_peak = results[1]['peak_memory']
    batched_peak = results[2]['peak_memory']

    generator_improvement = ((standard_peak - generator_peak) / standard_peak * 100) if standard_peak > 0 else 0
    batched_improvement = ((standard_peak - batched_peak) / standard_peak * 100) if standard_peak > 0 else 0

    print(f"\nMemory Savings:")
    print(f"  Generator vs Standard: {generator_improvement:+.1f}%")
    print(f"  Batched vs Standard: {batched_improvement:+.1f}%")
    print(f"{'='*70}\n")


async def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(
        description='Memory profiling utility for web scrapers',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Profile standard method with 10 pages
  python tools/memory_profiler.py --pages 10 --method standard

  # Profile generator method with 50 pages
  python tools/memory_profiler.py --pages 50 --method generator

  # Profile batched method with custom batch size
  python tools/memory_profiler.py --pages 100 --method batched --batch-size 20

  # Compare all methods
  python tools/memory_profiler.py --pages 20 --method compare
        """
    )
    parser.add_argument(
        '--pages',
        type=int,
        default=10,
        help='Number of pages to scrape (default: 10)'
    )
    parser.add_argument(
        '--method',
        type=str,
        default='compare',
        choices=['standard', 'generator', 'batched', 'compare'],
        help='Method to profile (default: compare)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=10,
        help='Batch size for batched method (default: 10)'
    )
    parser.add_argument(
        '--delay',
        type=float,
        default=1.0,
        help='Delay between page requests in seconds (default: 1.0)'
    )
    parser.add_argument(
        '--category',
        type=str,
        default='markets',
        choices=list(CATEGORIES.keys()),
        help='News category to scrape (default: markets)'
    )
    parser.add_argument(
        '--no-details',
        action='store_true',
        help='Skip fetching article details (faster profiling)'
    )

    args = parser.parse_args()

    base_url = CATEGORIES[args.category]
    scraper = MoneyControlCrawl4AIScraper(
        base_url=base_url,
        fetch_details=not args.no_details,
        max_concurrent=3  # Lower concurrency for more stable profiling
    )

    if args.method == 'compare':
        await compare_methods(args.pages, args.batch_size, args.delay, args.category)
    elif args.method == 'standard':
        await profile_standard_method(scraper, args.pages, args.delay)
    elif args.method == 'generator':
        await profile_generator_method(scraper, args.pages, args.delay)
    elif args.method == 'batched':
        await profile_batched_method(scraper, args.pages, args.batch_size, args.delay)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nProfiling interrupted by user")
        sys.exit(0)
