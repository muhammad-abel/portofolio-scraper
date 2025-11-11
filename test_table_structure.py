#!/usr/bin/env python3
"""
Quick test to verify the new dict-by-date structure
"""

from bs4 import BeautifulSoup
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# Mock the logger for testing
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Import the scraper after setting up logger
from scrapers.screener.screener_scraper import ScreenerScraper

# Create mock HTML table
mock_table_html = """
<table>
    <thead>
        <tr>
            <th></th>
            <th>Sep 2024</th>
            <th>Jun 2024</th>
            <th>Mar 2024</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>Revenue+</td>
            <td>83,002</td>
            <td>81,546</td>
            <td>79,434</td>
        </tr>
        <tr>
            <td>Net Profit+</td>
            <td>18,627</td>
            <td>17,188</td>
            <td>18,013</td>
        </tr>
        <tr>
            <td>EPS in Rs</td>
            <td>11.68</td>
            <td>10.83</td>
            <td>11.60</td>
        </tr>
        <tr>
            <td>OPM %</td>
            <td>26.7</td>
            <td>25.0</td>
            <td>24.5</td>
        </tr>
    </tbody>
</table>
"""

def test_table_extraction():
    """Test the new dict-by-date structure"""
    print("Testing new dict-by-date structure...")
    print("=" * 70)

    # Parse HTML
    soup = BeautifulSoup(mock_table_html, 'html.parser')
    table = soup.find('table')

    # Create scraper instance
    scraper = ScreenerScraper()

    # Extract data
    result = scraper._extract_table_raw(table)

    print("\nExtracted structure:")
    print("-" * 70)

    import json
    print(json.dumps(result, indent=2, ensure_ascii=False))

    print("\n" + "=" * 70)
    print("Verification:")
    print("-" * 70)

    # Verify structure
    assert isinstance(result, dict), "Result should be a dict"
    assert "Sep 2024" in result, "Should have 'Sep 2024' key"
    assert "Jun 2024" in result, "Should have 'Jun 2024' key"
    assert "Mar 2024" in result, "Should have 'Mar 2024' key"

    # Verify data for Sep 2024
    sep_data = result["Sep 2024"]
    assert "revenue" in sep_data, "Should have 'revenue' key"
    assert "net_profit" in sep_data, "Should have 'net_profit' key"
    assert "eps_in_rs" in sep_data, "Should have 'eps_in_rs' key"
    assert "opm_percent" in sep_data, "Should have 'opm_percent' key"

    # Verify values
    assert sep_data["revenue"] == "83,002", f"Revenue should be '83,002', got '{sep_data['revenue']}'"
    assert sep_data["net_profit"] == "18,627", f"Net profit should be '18,627', got '{sep_data['net_profit']}'"
    assert sep_data["eps_in_rs"] == "11.68", f"EPS should be '11.68', got '{sep_data['eps_in_rs']}'"

    print("✅ Dict structure: PASS")
    print("✅ Keys present: PASS")
    print("✅ Values correct: PASS")

    print("\n" + "=" * 70)
    print("Example usage:")
    print("-" * 70)
    print(f"# Access data easily:")
    print(f"revenue_sep_2024 = data['Sep 2024']['revenue']  # '{result['Sep 2024']['revenue']}'")
    print(f"eps_jun_2024 = data['Jun 2024']['eps_in_rs']  # '{result['Jun 2024']['eps_in_rs']}'")

    print("\n✅ All tests passed! The new structure works correctly.")
    print("=" * 70)

if __name__ == "__main__":
    test_table_extraction()
