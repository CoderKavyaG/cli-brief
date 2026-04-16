#!/usr/bin/env python3
"""
Direct test: Check if email is being extracted from content
"""

import json
from dotenv import load_dotenv
load_dotenv()

from phase1_agent.advanced_scraper import DeepProfileExtractor, LinkedInBrowserScraper
from phase1_agent.tools import TavilySearch

# Sample test content that SHOULD contain emails
test_contents = {
    "personal_site": """
        Ishan Kumar - CMO at InTheBox
        
        Contact me:
        Email: ishan@inthebox.co
        Email: ishan.kumar@chitkara.ac.in
        Phone: +91-9876543210
        
        Twitter: @ishankumax
        GitHub: github.com/ishankumax
        Instagram: @ishankumax
        """,
    "linkedin": """
        Ishan Kumar
        CMO at InTheBox
        
        Email on file: ishan.kumar@inthebox.co
        Chitkara University
        Contact: ishan@company.com
        """,
}

extractor = DeepProfileExtractor()

print("\n" + "=" * 80)
print("TESTING CONTACT EXTRACTION FROM SAMPLE CONTENT")
print("=" * 80)

for source_type, content in test_contents.items():
    print(f"\n[{source_type.upper()}]")
    result = extractor.extract_contact_info(content)
    
    print(f"  Emails found: {result.get('emails', [])}")
    print(f"  Phones found: {result.get('phones', [])}")
    print(f"  Social handles: {result.get('social_handles', {})}")


# Now test with ACTUAL scraped content
print("\n" + "=" * 80)
print("TESTING WITH ACTUAL SCRAPE (Ishan Kumar)")
print("=" * 80)

search = TavilySearch(api_key="tvly-" + "" or "test")  # dummy key just for search

# Search for Ishan Kumar's personal site
print("\n[SEARCHING] For personal site...")
results = search.search('"ishankumax" portfolio', count=3)

if results:
    print(f"Found {len(results)} results")
    for i, r in enumerate(results[:1], 1):
        print(f"  [{i}] {r['url'][:60]}")
        print(f"      Content length: {len(r['content'])} chars")
        
        # Extract from this
        contact_info = extractor.extract_contact_info(r['content'])
        print(f"      Emails: {contact_info.get('emails', [])}")
        print(f"      Socials: {contact_info.get('social_handles', {})}")
