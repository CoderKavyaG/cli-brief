#!/usr/bin/env python3
"""Test multiple URLs with Firecrawl"""

from phase1_agent.tools import FirecrawlScrape

urls = [
    "https://blog.samaltman.com/",
    "https://en.wikipedia.org/wiki/Sam_Altman",
    "https://www.youtube.com/watch?v=ZpUKNYcgM-E"
]

scraper = FirecrawlScrape()

for url in urls:
    print(f"\n[TEST] Scraping: {url}")
    content = scraper.scrape(url)
    
    if content and content.content:
        print(f"  ✓ Got {len(content.content)} characters")
        print(f"  Title: {content.title[:60]}")
        print(f"  Preview: {content.content[:200]}...")
    else:
        print(f"  ✗ No content extracted")
