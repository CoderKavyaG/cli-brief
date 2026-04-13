import requests
import json
import re
from typing import List, Optional, Dict, Any
from phase1_agent.config import (
    TAVILY_API_KEY, FIRECRAWL_API_KEY, TAVILY_SEARCH_URL, FIRECRAWL_SCRAPE_URL,
    MAX_SEARCHES, SEARCH_TIMEOUT, SCRAPE_TIMEOUT
)
from phase1_agent.models import SearchResult, ScrapedContent
from datetime import datetime

class TavilySearch:
    """Tool 1: Search the web using Tavily API (free, no credit card)"""
    
    @staticmethod
    def search(query: str, count: int = MAX_SEARCHES) -> List[SearchResult]:
        """Search using Tavily API"""
        if not TAVILY_API_KEY:
            raise ValueError("TAVILY_API_KEY not set in .env")
        
        payload = {
            "api_key": TAVILY_API_KEY,
            "query": query,
            "max_results": count,
            "include_answer": True
        }
        
        try:
            print(f"[SEARCH] Query: {query}")
            response = requests.post(TAVILY_SEARCH_URL, json=payload, timeout=SEARCH_TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            if "results" in data:
                for item in data["results"][:count]:
                    result = SearchResult(
                        title=item.get("title", ""),
                        url=item.get("url", ""),
                        description=item.get("content", ""),
                        source="Tavily Search"
                    )
                    results.append(result)
                    print(f"  - {result.title[:60]}... ({result.url})")
            
            print(f"[SEARCH DONE] Found {len(results)} results")
            return results
            
        except requests.exceptions.RequestException as e:
            print(f"[SEARCH ERROR] {str(e)}")
            return []

class JinaScrape:
    """Tool 2: Scrape webpage content using Jina API (no auth needed)"""
    
    @staticmethod
    def scrape(url: str, fallback_snippet: str = "") -> Optional[ScrapedContent]:
        """Scrape URL using Jina AI API at r.jina.ai (no auth required)"""
        try:
            jina_url = f"https://r.jina.ai/{url}"
            response = requests.get(
                jina_url,
                headers={
                    "Accept": "text/markdown",
                    "User-Agent": "Mozilla/5.0"
                },
                timeout=20
            )
            if response.status_code == 200 and len(response.text.strip()) > 200:
                print(f"[JINA OK] Got {len(response.text)} chars from {url[:60]}...")
                return ScrapedContent(
                    url=url,
                    title="",
                    content=response.text,
                    timestamp=datetime.now().isoformat()
                )
            else:
                print(f"[JINA FAILED] {url[:60]}... - only {len(response.text)} chars")
                if fallback_snippet:
                    return ScrapedContent(
                        url=url,
                        title="",
                        content=fallback_snippet,
                        timestamp=datetime.now().isoformat()
                    )
                return None
        except Exception as e:
            print(f"[JINA ERROR] {url[:60]}... - {str(e)[:50]}")
            if fallback_snippet:
                return ScrapedContent(
                    url=url,
                    title="",
                    content=fallback_snippet,
                    timestamp=datetime.now().isoformat()
                )
            return None

class LinkExtractor:
    """Tool 3: Extract social media & personal links from content"""
    
    PATTERNS = {
        "linkedin": r"https?://(?:www\.)?(?:linkedin\.com|in\.linkedin\.com)/(?:in|company|showcase)/([a-z0-9\-]+)",
        "twitter": r"https?://(?:x\.com|twitter\.com)/(@?[\w]+)",
        "instagram": r"https?://(?:www\.)?instagram\.com/([a-z0-9\._\-]+)",
        "github": r"https?://github\.com/([a-z0-9\-]+)",
        "facebook": r"https?://(?:www\.)?facebook\.com/([a-z0-9\.\-]+)",
        "tiktok": r"https?://(?:www\.)?tiktok\.com/@([\w\.]+)",
        "website": r"https?://(?:www\.)?([a-z0-9\-]+\.(?:com|io|org|net|co|dev|me|blog|site))",
        "email": r"\b([a-z0-9\._\-]+@[a-z0-9\._\-]+\.[a-z]+)\b"
    }
    
    @staticmethod
    def extract_from_text(text: str) -> Dict[str, List[str]]:
        """Extract all social & contact links from text"""
        results = {}
        
        for platform, pattern in LinkExtractor.PATTERNS.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                results[platform] = list(set(matches))  # Remove duplicates
        
        return results
    
    @staticmethod
    def extract_from_snippet(snippet: str) -> Dict[str, List[str]]:
        """Extract from search result snippet"""
        return LinkExtractor.extract_from_text(snippet)
    
    @staticmethod
    def format_links(extracted: Dict[str, List[str]]) -> str:
        """Format extracted links nicely"""
        output = ""
        
        for platform, values in extracted.items():
            if values:
                output += f"\n**{platform.capitalize()}**: {', '.join(values)}"
        
        return output


class FileSave:
    """Tool 4: Save files to disk"""
    
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
