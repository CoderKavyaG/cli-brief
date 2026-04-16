#!/usr/bin/env python3
"""
Check what content is being scraped for the wrong URLs
"""

from dotenv import load_dotenv
load_dotenv()

from phase1_agent.tools import JinaReader
from phase1_agent.advanced_scraper import DeepProfileExtractor

# Test what gets scraped from the wrong URLs
test_urls = [
    "https://www.slidingscale.org/",  # The "personal site" we're finding
    "https://x.com/ishankumax/",  # Try the profile directly
    "https://www.instagram.com/ishankumax/",  # Instagram
]

jina = JinaReader()
extractor = DeepProfileExtractor()

print("\n" + "=" * 80)
print("CHECKING SCRAPED CONTENT")
print("=" * 80)

for url in test_urls:
    print(f"\n[URL] {url}")
    print(f"{'─' * 40}".replace('─', '-'))
    
    try:
        content = jina.scrape(url)
        if content:
            print(f"Scraped {len(content)} chars")
            print(f"Preview: {content[:200]}...\n")
            
            # Extract contact info
            info = extractor.extract_contact_info(content)
            print(f"Emails: {info.get('emails', [])}")
            print(f"Socials: {info.get('social_handles', {})}")
        else:
            print("No content returned")
    except Exception as e:
        print(f"Error: {str(e)[:100]}")

print("\n" + "=" * 80)
