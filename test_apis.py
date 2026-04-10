#!/usr/bin/env python3
"""Test Tavily and Firecrawl APIs"""

from phase1_agent.tools import TavilySearch, FirecrawlScrape

print("[TEST] Searching for Sam Altman...")
search = TavilySearch()
results = search.search("Sam Altman OpenAI CEO latest", count=3)

if results:
    print(f"\n[SUCCESS] Found {len(results)} results")
    print(f"Top result: {results[0].title}")
    print(f"URL: {results[0].url}\n")
    
    print("[TEST] Scraping first URL...")
    scraper = FirecrawlScrape()
    content = scraper.scrape(results[0].url)
    
    if content:
        print(f"[SUCCESS] Got {len(content.content)} characters from {content.url}")
        print(f"Title: {content.title}")
        print(f"Preview: {content.content[:300]}...")
    else:
        print("[FAILED] Could not scrape content")
else:
    print("[FAILED] No search results")
