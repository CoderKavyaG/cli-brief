"""
Simple web search and scraping tools
"""

import requests
import json
from typing import List, Dict, Optional


class TavilySearch:
    """Web search using Tavily API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.url = "https://api.tavily.com/search"
    
    def search(self, query: str, count: int = 5) -> List[Dict]:
        """
        Search the web using Tavily API.
        Returns: list of {"title": str, "url": str, "content": str}
        """
        try:
            if not self.api_key:
                print(f"[TAVILY ERROR] No API key set!")
                return []
            
            payload = {
                "api_key": self.api_key,
                "query": query,
                "max_results": count
            }
            
            print(f"[TAVILY] Searching: {query}")
            response = requests.post(self.url, json=payload, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            if "results" in data:
                for item in data["results"]:
                    results.append({
                        "title": item.get("title", ""),
                        "url": item.get("url", ""),
                        "content": item.get("content", "")
                    })
            
            print(f"[TAVILY] Got {len(results)} results")
            return results
        
        except requests.exceptions.RequestException as e:
            print(f"[TAVILY ERROR] HTTP Error: {e.response.status_code if hasattr(e, 'response') else 'unknown'}")
            print(f"[TAVILY ERROR] {str(e)[:200]}")
            return []
        
        except Exception as e:
            print(f"[TAVILY ERROR] {str(e)}")
            return []


class JinaReader:
    """Read webpage content using Jina API (free, no auth)"""
    
    def scrape(self, url: str) -> str:
        """
        Scrape webpage content using Jina at r.jina.ai
        Returns: content as markdown if successful, empty string otherwise
        """
        try:
            jina_url = f"https://r.jina.ai/{url}"
            print(f"[JINA] Scraping: {url}")
            
            response = requests.get(
                jina_url,
                headers={
                    "Accept": "text/markdown",
                    "User-Agent": "Mozilla/5.0"
                },
                timeout=20
            )
            
            print(f"[JINA] Status: {response.status_code}")
            
            if response.status_code == 200:
                if len(response.text) > 300:
                    # Return first 4000 chars
                    return response.text[:4000]
                else:
                    print(f"[JINA] Content too short: {len(response.text)} chars (need >300)")
                    return ""
            else:
                print(f"[JINA] Error response: {response.status_code}")
                return ""
        
        except requests.exceptions.Timeout:
            print(f"[JINA ERROR] Timeout scraping {url}")
            return ""
        
        except Exception as e:
            print(f"[JINA ERROR] {str(e)[:200]}")
            return ""
