#!/usr/bin/env python3
"""
DEBUG: What is LinkedIn actually scraping?
"""

import os
from dotenv import load_dotenv
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()

from phase1_agent.advanced_scraper import LinkedInBrowserScraper

scraper = LinkedInBrowserScraper()

# Test scraping Ananya's LinkedIn
linkedin_url = "https://in.linkedin.com/in/ananya-malhotra-19a422337"

print(f"\nScribing: {linkedin_url}")
print("=" * 80)

try:
    content = scraper.scrape(linkedin_url)
    print(f"\nContent length: {len(content)} chars")
    print(f"\nFirst 600 chars:")
    print(content[:600])
    print(f"\n\nLast 200 chars:")
    print(content[-200:])
    
    # Look for person info
    print(f"\n\nSearching for key info:")
    print(f"  'Ananya' in content: {'Ananya' in content}")
    print(f"  'Malhotra' in content: {'Malhotra' in content}")
    print(f"  'DevLearn' in content: {'DevLearn' in content}")
    print(f"  'Campus' in content: {'Campus' in content}")
    print(f"  '@' (email) in content: {'@' in content}")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
