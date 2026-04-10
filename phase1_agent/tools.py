import requests
import json
from typing import List, Optional, Dict, Any
from phase1_agent.config import (
    BRAVE_API_KEY, FIRECRAWL_API_KEY, BRAVE_SEARCH_URL, FIRECRAWL_SCRAPE_URL,
    MAX_SEARCHES, SEARCH_TIMEOUT, SCRAPE_TIMEOUT
)
from phase1_agent.models import SearchResult, ScrapedContent
from datetime import datetime

class BraveSearch:
    """Tool 1: Search the web using Brave API"""
    
    @staticmethod
    def search(query: str, count: int = MAX_SEARCHES) -> List[SearchResult]:
        """Search using Brave API"""
        if not BRAVE_API_KEY:
            raise ValueError("BRAVE_API_KEY not set in .env")
        
        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": BRAVE_API_KEY
        }
        
        params = {
            "q": query,
            "count": count
        }
        
        try:
            print(f"[SEARCH] Query: {query}")
            response = requests.get(BRAVE_SEARCH_URL, headers=headers, params=params, timeout=SEARCH_TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            if "web" in data:
                for item in data["web"][:count]:
                    result = SearchResult(
                        title=item.get("title", ""),
                        url=item.get("url", ""),
                        description=item.get("description", ""),
                        source="Brave Search"
                    )
                    results.append(result)
                    print(f"  → {result.title[:60]}... ({result.url})")
            
            print(f"[SEARCH DONE] Found {len(results)} results")
            return results
            
        except requests.exceptions.RequestException as e:
            print(f"[SEARCH ERROR] {str(e)}")
            return []

class FirecrawlScrape:
    """Tool 2: Scrape webpage content"""
    
    @staticmethod
    def scrape(url: str) -> Optional[ScrapedContent]:
        """Scrape URL using Firecrawl"""
        if not FIRECRAWL_API_KEY:
            raise ValueError("FIRECRAWL_API_KEY not set in .env")
        
        headers = {
            "Authorization": f"Bearer {FIRECRAWL_API_KEY}"
        }
        
        try:
            print(f"[SCRAPE] URL: {url}")
            response = requests.post(
                FIRECRAWL_SCRAPE_URL,
                json={"url": url},
                headers=headers,
                timeout=SCRAPE_TIMEOUT
            )
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("success"):
                content = ScrapedContent(
                    url=url,
                    title=data.get("metadata", {}).get("title", ""),
                    content=data.get("markdown", ""),
                    timestamp=datetime.now().isoformat()
                )
                print(f"[SCRAPE DONE] Got {len(content.content)} characters")
                return content
            else:
                print(f"[SCRAPE FAILED] {data.get('error', 'Unknown error')}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"[SCRAPE ERROR] {str(e)}")
            return None

class FileSave:
    """Tool 3: Save files to disk"""
    
    @staticmethod
    def save_briefing(filename: str, content: str, directory: str = "output") -> str:
        """Save briefing markdown file"""
        import os
        
        os.makedirs(directory, exist_ok=True)
        filepath = os.path.join(directory, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"[SAVE] Briefing saved to {filepath}")
        return filepath
