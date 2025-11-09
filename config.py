"""
Configuration file for Moneycontrol scraper
"""

# Scraper settings
BASE_URL = "https://www.moneycontrol.com/news/business/markets/"
NUM_PAGES = 3  # Number of pages to scrape
DELAY_BETWEEN_PAGES = 2.0  # Delay in seconds between page requests

# Output settings
OUTPUT_JSON = True
OUTPUT_CSV = True
OUTPUT_EXCEL = False  # Set to True if you want Excel output

# Output filenames
JSON_FILENAME = "moneycontrol_news.json"
CSV_FILENAME = "moneycontrol_news.csv"
EXCEL_FILENAME = "moneycontrol_news.xlsx"

# Request settings
REQUEST_TIMEOUT = 30  # Timeout for HTTP requests in seconds
MAX_RETRIES = 3  # Maximum number of retries on failure

# User agent
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

# Selenium settings (for selenium scraper)
SELENIUM_HEADLESS = True  # Run browser in headless mode
SELENIUM_IMPLICIT_WAIT = 10  # Implicit wait in seconds

# Logging
LOG_LEVEL = "INFO"  # Options: DEBUG, INFO, WARNING, ERROR
LOG_FILE = "scraper.log"
