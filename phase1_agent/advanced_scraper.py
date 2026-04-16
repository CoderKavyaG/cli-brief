"""
Advanced scraper with browser automation for LinkedIn + async parallel scraping
"""

import asyncio
import aiohttp
import requests
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta


class IdentityLinkage:
    """Cross-platform identity linking - match same person across platforms"""
    
    def __init__(self):
        self.identity_graph = {}  # Maps: identifier -> [all_identifiers_of_same_person]
    
    def link_identifiers(self, identifiers: Dict[str, str]) -> Dict:
        """
        Link identifiers across platforms.
        
        Input:
        {
            "linkedin_handle": "jeet-biswas-123",
            "twitter": "@jeetbiswas",
            "github": "jeetbiswas",
            "email": "jeet@chitkara.ac.in"
        }
        
        Output: Confidence scores for each link
        {
            "linkedin_handle": "jeet-biswas-123",
            "variants": ["jeetbiswas", "jeet-biswas", "jeet.biswas"],
            "confidence": 0.95,
            "cross_platform_matches": {
                "twitter": matched,
                "github": matched,
                "email_domain": matched
            }
        }
        """
        linkage = {
            "primary_identifier": None,
            "all_identifiers": [],
            "confidence_score": 0.0,
            "cross_platform_matches": {},
            "linked_platforms": []
        }
        
        # Extract base name variations
        base_names = self._extract_name_variations(identifiers)
        linkage["all_identifiers"] = base_names
        
        # Check cross-platform consistency
        for platform, identifier in identifiers.items():
            if not identifier:
                continue
            
            # Check if identifier matches any base name
            normalized = self._normalize_identifier(identifier)
            if any(self._fuzzy_match(normalized, bn) for bn in base_names):
                linkage["cross_platform_matches"][platform] = True
                linkage["linked_platforms"].append(platform)
            else:
                linkage["cross_platform_matches"][platform] = False
        
        # Calculate confidence
        if len(linkage["linked_platforms"]) >= 2:
            linkage["confidence_score"] = 0.9 + (len(linkage["linked_platforms"]) * 0.02)
        elif len(linkage["linked_platforms"]) >= 1:
            linkage["confidence_score"] = 0.7
        
        linkage["primary_identifier"] = identifiers.get("linkedin_handle") or \
                                       identifiers.get("email") or \
                                       identifiers.get("github")
        
        return linkage
    
    def _extract_name_variations(self, identifiers: Dict[str, str]) -> List[str]:
        """Extract all name variations from identifiers"""
        variations = set()
        
        for platform, identifier in identifiers.items():
            if not identifier:
                continue
            
            # Remove special chars, split
            clean = re.sub(r'[^a-zA-Z0-9\-_\.]', '', identifier).lower()
            
            # Add full identifier
            variations.add(clean)
            
            # Add split variations
            for sep in ['-', '_', '.']:
                if sep in clean:
                    parts = clean.split(sep)
                    variations.update(parts)
            
            # Extract name from email
            if '@' in identifier:
                email_part = identifier.split('@')[0]
                clean_email = re.sub(r'[^a-zA-Z0-9\-_\.]', '', email_part).lower()
                variations.add(clean_email)
                for sep in ['-', '_', '.']:
                    if sep in clean_email:
                        variations.update(clean_email.split(sep))
        
        return list(variations)
    
    def _normalize_identifier(self, identifier: str) -> str:
        """Normalize identifier for comparison"""
        return re.sub(r'[^a-zA-Z0-9]', '', identifier).lower()
    
    def _fuzzy_match(self, s1: str, s2: str, threshold=0.8) -> bool:
        """Simple fuzzy match - both contain each other or very similar"""
        s1, s2 = s1.lower(), s2.lower()
        
        # Exact match
        if s1 == s2:
            return True
        
        # One contains other (for short identifiers)
        if len(s1) > 3 and len(s2) > 3:
            if s1 in s2 or s2 in s1:
                return True
        
        # Levenshtein-style check (simple)
        if len(s1) == len(s2):
            diff = sum(1 for a, b in zip(s1, s2) if a != b)
            if diff <= 2:
                return True
        
        return False


class LinkedInBrowserScraper:
    """Scrape LinkedIn using browser automation (Playwright) with Jina fallback"""
    
    def __init__(self):
        self.browser = None
        self.context = None
    
    def scrape_profile(self, url: str, timeout: int = 15) -> Optional[str]:
        """
        Scrape LinkedIn profile using Playwright (sync wrapper) with Jina fallback
        Returns: Profile content or None if unavailable
        """
        # Try browser scraping first
        text = self._browser_scrape(url, timeout)
        if text:
            return text
        
        # Fallback to Jina
        print(f"[LINKEDIN] Browser scraping failed, trying Jina fallback...")
        return self._jina_fallback(url)
    
    def _browser_scrape(self, url: str, timeout: int) -> Optional[str]:
        """Try browser scraping with multiple strategies"""
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            print("[LINKEDIN] Playwright not installed")
            return None
        
        strategies = [
            ("networkidle", "networkidle"),
            ("domcontentloaded", None),
            ("load", None)
        ]
        
        for wait_strategy, load_state in strategies:
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(
                        headless=True,
                        args=['--disable-blink-features=AutomationControlled']
                    )
                    
                    context = browser.new_context(
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                        viewport={"width": 1920, "height": 1080}
                    )
                    
                    page = context.new_page()
                    
                    try:
                        print(f"[LINKEDIN BROWSER] Strategy: {wait_strategy}")
                        page.goto(url, wait_until=wait_strategy, timeout=timeout * 1000)
                        
                        if load_state:
                            page.wait_for_load_state(load_state, timeout=5000)
                        
                        # Extract text content
                        text = page.evaluate("() => document.body.innerText")
                        
                        browser.close()
                        
                        if text and len(text) > 100:
                            print(f"[LINKEDIN BROWSER SUCCESS] {wait_strategy}: Got {len(text)} chars")
                            return text
                        
                    except Exception as e:
                        print(f"[LINKEDIN BROWSER] {wait_strategy} failed: {str(e)[:50]}")
                        browser.close()
                        continue
            
            except Exception as e:
                print(f"[LINKEDIN BROWSER INIT] Error: {str(e)[:50]}")
                continue
        
        print(f"[LINKEDIN BROWSER] All strategies failed")
        return None
    
    def _jina_fallback(self, url: str) -> Optional[str]:
        """Fallback to Jina for reading LinkedIn profile"""
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
            
            if response.status_code == 200 and len(response.text) > 300:
                print(f"[JINA FALLBACK] Success: {len(response.text)} chars")
                return response.text[:4000]
            else:
                print(f"[JINA FALLBACK] Failed: {response.status_code}")
                return None
        
        except Exception as e:
            print(f"[JINA FALLBACK] Error: {str(e)[:50]}")
            return None


class RequestCache:
    """Simple in-memory cache for search results"""
    
    def __init__(self, ttl_minutes: int = 5):
        self.cache = {}
        self.ttl = timedelta(minutes=ttl_minutes)
    
    def get(self, key: str) -> Optional:
        """Get value from cache if not expired"""
        if key in self.cache:
            value, timestamp = self.cache[key]
            if datetime.now() - timestamp < self.ttl:
                print(f"[CACHE HIT] {key[:50]}")
                return value
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, value) -> None:
        """Store value in cache"""
        self.cache[key] = (value, datetime.now())
    
    def clear_expired(self) -> None:
        """Remove expired entries"""
        now = datetime.now()
        expired = [k for k, (_, ts) in self.cache.items() if now - ts > self.ttl]
        for k in expired:
            del self.cache[k]


class DeepProfileExtractor:
    """Extract all contact info, emails, socials from scraped content"""
    
    @staticmethod
    def extract_contact_info(content: str) -> Dict[str, List[str]]:
        """
        Extract emails, phone, links, etc from content
        """
        if not content:
            return {}
        
        info = {
            "emails": [],
            "phones": [],
            "links": [],
            "social_handles": {},
            "keywords": []
        }
        
        # Email extraction
        emails = re.findall(r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b', content)
        info["emails"] = list(set(emails))
        
        # Phone extraction
        phones = re.findall(r'\+?1?\s*\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})', content)
        info["phones"] = [''.join(p) for p in phones]
        
        # Links extraction
        links = re.findall(r'https?://[^\s<>\"]+', content)
        info["links"] = list(set(links))
        
        # Social handles
        info["social_handles"]["twitter"] = re.findall(r'@([a-zA-Z0-9_]{1,15})\b', content)
        info["social_handles"]["instagram"] = re.findall(r'@([a-zA-Z0-9_.]{1,30})', content)
        info["social_handles"]["github"] = re.findall(r'github\.com/([a-zA-Z0-9_-]+)', content)
        
        return info


class LinkExtractor:
    """Extract and rank URLs from post content"""
    
    def extract_links_from_posts(self, posts: list) -> Dict[str, Dict]:
        """
        Extract links from post content with rankings.
        
        Input: [{url: str, content: str}, ...]
        Output: {
            "twitter": {"urls": ["x.com/user1", ...], "count": 3, "confidence": 0.9},
            "github": {"urls": ["github.com/user1", ...], "count": 2, "confidence": 0.8},
            ...
        }
        """
        link_map = {}
        platform_patterns = {
            "twitter": [r'((?:https?://)?(?:twitter\.com|x\.com)/[a-zA-Z0-9_]+)'],
            "github": [r'((?:https?://)?github\.com/[a-zA-Z0-9_-]+)'],
            "personal": [r'(https?://(?!(?:linkedin|twitter|x|github|instagram|facebook)\.com)[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'],
            "linkedin": [r'((?:https?://)?linkedin\.com/in/[a-zA-Z0-9_-]+)'],
            "instagram": [r'((?:https?://)?instagram\.com/[a-zA-Z0-9_.-]+)'],
        }
        
        all_links = {}
        
        # Extract links from all posts
        for post in posts:
            content = post.get("content", "")
            if not content:
                continue
            
            for platform, patterns in platform_patterns.items():
                for pattern in patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    
                    for match in matches:
                        # Normalize URL
                        url = match.lower()
                        if not url.startswith("http"):
                            url = "https://" + url
                        
                        if url not in all_links:
                            all_links[url] = {
                                "platform": platform,
                                "count": 0,
                                "posts": []
                            }
                        
                        all_links[url]["count"] += 1
                        all_links[url]["posts"].append(post.get("url", ""))
        
        # Group by platform and rank by frequency
        for url, data in all_links.items():
            platform = data["platform"]
            
            if platform not in link_map:
                link_map[platform] = {
                    "urls": [],
                    "count": 0,
                    "confidence": 0.0
                }
            
            link_map[platform]["urls"].append(url)
            link_map[platform]["count"] += data["count"]
        
        # Calculate confidence scores
        for platform, data in link_map.items():
            if data["count"] >= 2:
                data["confidence"] = 0.9  # Multiple mentions = high confidence
            elif data["count"] == 1:
                data["confidence"] = 0.6  # Single mention = medium confidence
            else:
                data["confidence"] = 0.3
            
            # Deduplicate URLs
            data["urls"] = list(set(data["urls"]))
        
        return link_map if link_map else {}
