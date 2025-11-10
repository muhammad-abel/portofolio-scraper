#!/usr/bin/env python3
"""
MongoDB Upload Script for Moneycontrol News Data

This script uploads scraped news articles from JSON file to MongoDB.
Features:
- Bulk insert with duplicate handling
- URL-based deduplication
- Progress tracking
- Error handling and logging
- Configurable connection settings

Usage:
    python upload_to_mongodb.py
"""

import json
import logging
import os
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

try:
    from pymongo import MongoClient, UpdateOne
    from pymongo.errors import BulkWriteError, ConnectionFailure, OperationFailure
except ImportError:
    print("ERROR: pymongo is not installed.")
    print("Please install it using: pip install pymongo")
    exit(1)

# ============================================================================
# CONFIGURATION
# ============================================================================
# You can either:
# 1. Edit the default values below directly, OR
# 2. Create a .env file and set environment variables (recommended)
# ============================================================================

# MongoDB connection string
# Examples:
# - Local: "mongodb://localhost:27017/"
# - Atlas: "mongodb+srv://username:password@cluster.mongodb.net/"
MONGODB_CONNECTION_STRING = os.getenv("MONGODB_CONNECTION_STRING", "mongodb://localhost:27017/")

# Database name
DATABASE_NAME = os.getenv("MONGODB_DATABASE_NAME", "moneycontrol_db")

# Collection name
COLLECTION_NAME = os.getenv("MONGODB_COLLECTION_NAME", "news_articles")

# JSON file path (relative to script location)
JSON_FILE_PATH = os.getenv("JSON_FILE_PATH", "moneycontrol_news_crawl4ai.json")

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mongodb_upload.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class MongoDBUploader:
    """Handle MongoDB upload operations for news articles"""

    def __init__(self, connection_string: str, database_name: str, collection_name: str):
        """
        Initialize MongoDB uploader

        Args:
            connection_string: MongoDB connection string
            database_name: Name of the database
            collection_name: Name of the collection
        """
        self.connection_string = connection_string
        self.database_name = database_name
        self.collection_name = collection_name
        self.client = None
        self.db = None
        self.collection = None

    def connect(self) -> bool:
        """
        Establish connection to MongoDB

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            logger.info(f"Connecting to MongoDB...")
            self.client = MongoClient(self.connection_string, serverSelectionTimeoutMS=5000)

            # Test connection
            self.client.server_info()

            self.db = self.client[self.database_name]
            self.collection = self.db[self.collection_name]

            logger.info(f"[SUCCESS] Connected to MongoDB")
            logger.info(f"Database: {self.database_name}")
            logger.info(f"Collection: {self.collection_name}")

            return True

        except ConnectionFailure as e:
            logger.error(f"[ERROR] Failed to connect to MongoDB: {e}")
            return False
        except Exception as e:
            logger.error(f"[ERROR] Unexpected error during connection: {e}")
            return False

    def load_json_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Load articles from JSON file

        Args:
            file_path: Path to JSON file

        Returns:
            List of article dictionaries
        """
        try:
            json_path = Path(file_path)

            if not json_path.exists():
                logger.error(f"[ERROR] JSON file not found: {file_path}")
                return []

            logger.info(f"Loading JSON file: {file_path}")

            with open(json_path, 'r', encoding='utf-8') as f:
                articles = json.load(f)

            logger.info(f"[SUCCESS] Loaded {len(articles)} articles from JSON")
            return articles

        except json.JSONDecodeError as e:
            logger.error(f"[ERROR] Invalid JSON format: {e}")
            return []
        except Exception as e:
            logger.error(f"[ERROR] Failed to load JSON file: {e}")
            return []

    def create_indexes(self):
        """Create indexes for better query performance"""
        try:
            logger.info("Creating indexes...")

            # Create unique index on hash to prevent duplicates
            self.collection.create_index("hash", unique=True)

            # Create index on URL for lookup
            self.collection.create_index("url")

            # Create index on date for faster date-based queries
            self.collection.create_index("date")

            # Create index on scraped_at for sorting by scrape time
            self.collection.create_index("scraped_at")

            logger.info("[SUCCESS] Indexes created")

        except Exception as e:
            logger.warning(f"[WARNING] Failed to create indexes: {e}")

    def upload_articles(self, articles: List[Dict[str, Any]], upsert: bool = True) -> Dict[str, int]:
        """
        Upload articles to MongoDB

        Args:
            articles: List of article dictionaries
            upsert: If True, update existing articles; if False, skip duplicates

        Returns:
            Dictionary with upload statistics
        """
        if not articles:
            logger.warning("[WARNING] No articles to upload")
            return {"inserted": 0, "updated": 0, "skipped": 0, "failed": 0}

        stats = {
            "inserted": 0,
            "updated": 0,
            "skipped": 0,
            "failed": 0
        }

        try:
            if upsert:
                # Use bulk upsert operations
                logger.info(f"Uploading {len(articles)} articles (upsert mode)...")

                operations = []
                for article in articles:
                    # Add upload timestamp
                    article['uploaded_at'] = datetime.now().isoformat()

                    # Create upsert operation based on hash (unique identifier)
                    # Fall back to URL if hash is not available (for backward compatibility)
                    filter_key = {"hash": article["hash"]} if "hash" in article else {"url": article["url"]}

                    operations.append(
                        UpdateOne(
                            filter_key,
                            {"$set": article},
                            upsert=True
                        )
                    )

                # Execute bulk write
                result = self.collection.bulk_write(operations, ordered=False)

                stats["inserted"] = result.upserted_count
                stats["updated"] = result.modified_count

                logger.info(f"[SUCCESS] Upload completed")
                logger.info(f"  - Inserted: {stats['inserted']}")
                logger.info(f"  - Updated: {stats['updated']}")

            else:
                # Insert only mode - skip duplicates
                logger.info(f"Uploading {len(articles)} articles (insert only mode)...")

                for article in articles:
                    try:
                        # Add upload timestamp
                        article['uploaded_at'] = datetime.now().isoformat()

                        self.collection.insert_one(article)
                        stats["inserted"] += 1

                    except Exception as e:
                        if "duplicate key error" in str(e).lower():
                            stats["skipped"] += 1
                        else:
                            stats["failed"] += 1
                            logger.warning(f"[WARNING] Failed to insert article: {article.get('url', 'unknown')}")

                logger.info(f"[SUCCESS] Upload completed")
                logger.info(f"  - Inserted: {stats['inserted']}")
                logger.info(f"  - Skipped (duplicates): {stats['skipped']}")
                logger.info(f"  - Failed: {stats['failed']}")

        except BulkWriteError as e:
            logger.error(f"[ERROR] Bulk write error: {e.details}")
            stats["failed"] = len(articles)
        except Exception as e:
            logger.error(f"[ERROR] Upload failed: {e}")
            stats["failed"] = len(articles)

        return stats

    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the collection

        Returns:
            Dictionary with collection statistics
        """
        try:
            total_docs = self.collection.count_documents({})

            # Get date range
            latest_article = self.collection.find_one(
                {"date": {"$ne": ""}},
                sort=[("scraped_at", -1)]
            )

            oldest_article = self.collection.find_one(
                {"date": {"$ne": ""}},
                sort=[("scraped_at", 1)]
            )

            stats = {
                "total_articles": total_docs,
                "latest_scrape": latest_article.get('scraped_at') if latest_article else None,
                "oldest_scrape": oldest_article.get('scraped_at') if oldest_article else None
            }

            logger.info("\n" + "="*60)
            logger.info("COLLECTION STATISTICS")
            logger.info("="*60)
            logger.info(f"Total articles in database: {stats['total_articles']}")
            logger.info(f"Latest scrape time: {stats['latest_scrape']}")
            logger.info(f"Oldest scrape time: {stats['oldest_scrape']}")
            logger.info("="*60 + "\n")

            return stats

        except Exception as e:
            logger.error(f"[ERROR] Failed to get collection stats: {e}")
            return {}

    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")


def main():
    """Main execution function"""

    logger.info("="*60)
    logger.info("MONGODB UPLOAD SCRIPT")
    logger.info("="*60)

    # Initialize uploader
    uploader = MongoDBUploader(
        connection_string=MONGODB_CONNECTION_STRING,
        database_name=DATABASE_NAME,
        collection_name=COLLECTION_NAME
    )

    try:
        # Connect to MongoDB
        if not uploader.connect():
            logger.error("Failed to connect to MongoDB. Exiting...")
            return

        # Create indexes
        uploader.create_indexes()

        # Load JSON file
        articles = uploader.load_json_file(JSON_FILE_PATH)

        if not articles:
            logger.error("No articles to upload. Exiting...")
            return

        # Upload articles
        # Set upsert=True to update existing articles
        # Set upsert=False to only insert new articles (skip duplicates)
        stats = uploader.upload_articles(articles, upsert=True)

        # Display collection statistics
        uploader.get_collection_stats()

        logger.info("[SUCCESS] Script completed successfully!")

    except Exception as e:
        logger.error(f"[ERROR] Script failed: {e}")

    finally:
        # Close connection
        uploader.close()


if __name__ == "__main__":
    main()
