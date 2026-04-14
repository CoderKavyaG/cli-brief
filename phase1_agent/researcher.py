"""
Researcher: Find the right person and scrape their digital footprint
with deep linking and browser automation
"""

import re
import os
from .tools import TavilySearch, JinaReader
from .advanced_scraper import (
    IdentityLinkage, LinkedInBrowserScraper, RequestCache, 
    DeepProfileExtractor
)


class Researcher:
    """Find a person's identity and scrape their digital presence with deep linking"""
    
    def __init__(self):
        api_key = os.getenv("TAVILY_API_KEY")
        self.search = TavilySearch(api_key)
        self.jina = JinaReader()
        self.linkage = IdentityLinkage()
        self.browser_scraper = LinkedInBrowserScraper()
        self.request_cache = RequestCache(ttl_minutes=5)
        self.extractor = DeepProfileExtractor()
    
    def find_person(self, name: str, company: str, role: str, rejected_urls: list = None) -> dict:
        """
        Find the RIGHT person using 3-point identity lock.
        
        Args:
            name: Person's name
            company: Company/institution
            role: Person's role
            rejected_urls: List of URLs to skip (for research again feature)
        
        Returns dict with identity information:
        - handle: LinkedIn handle
        - linkedin_url: LinkedIn profile URL
        - personal_site: Personal website/portfolio
        - instagram: Instagram profile URL
        - github: GitHub profile URL
        - twitter: Twitter/X profile URL
        - photo_url: Photo extracted from content
        - email: Email extracted from content
        - verified: Whether identity was locked
        """
        
        if rejected_urls is None:
            rejected_urls = []
        
        print(f"[REJECTION] Skipping {len(rejected_urls)} previously rejected URLs")
        
        identity = {
            "handle": None,
            "linkedin_url": None,
            "personal_site": None,
            "instagram": None,
            "github": None,
            "twitter": None,
            "photo_url": None,
            "email": None,
            "verified": False
        }
        
        # Search with all three identifiers for strong disambiguation
        print(f"[SEARCH 1] Searching: \"{name}\" \"{company}\" \"{role}\"")
        results = self.search.search(
            f'"{name}" \"{company}\" \"{role}\"', count=10  # More results to skip rejected ones
        )
        print(f"[SEARCH 1 RESULT] Got {len(results)} results")
        
        # If no results, try name + company only
        if not results:
            print(f"[SEARCH 2] Retrying: \"{name}\" \"{company}\"")
            results = self.search.search(
                f'"{name}" \"{company}\"', count=10
            )
            print(f"[SEARCH 2 RESULT] Got {len(results)} results")
        
        # If still no results, try just name
        if not results:
            print(f"[SEARCH 3] Retrying: \"{name}\"")
            results = self.search.search(name, count=10)
            print(f"[SEARCH 3 RESULT] Got {len(results)} results")
        
        # Filter out rejected URLs
        filtered_results = [r for r in results if r.get("url") not in rejected_urls]
        print(f"[REJECTION] Filtered {len(results)} to {len(filtered_results)} (rejected {len(results) - len(filtered_results)})")
        
        if not filtered_results and rejected_urls:
            print(f"[WARNING] All results were rejected, showing unfiltered")
            filtered_results = results
        
        results = filtered_results
        
        # Debug: print what we got
        if results:
            print(f"[DEBUG] Sample results:")
            for r in results[:2]:
                print(f"  - {r['title'][:60]}")
                print(f"    URL: {r['url']}")
        
        # TIER 1: SMART SEARCH - Use search metadata (titles) as verification source
        linkedin_found = False
        name_parts = name.lower().split()
        company_lower = company.lower()
        
        for r in results:
            if "linkedin.com/in/" in r["url"]:
                print(f"[LINKEDIN FOUND] {r['url']}")
                # Extract handle from URL
                match = re.search(r'linkedin\.com/in/([a-zA-Z0-9_-]+)', r["url"])
                if match:
                    handle = match.group(1)
                    print(f"[HANDLE EXTRACTED] {handle}")
                    
                    # TIER 1: Use search TITLE as verification (faster, more reliable)
                    search_title = r["title"].lower()
                    search_content = r["content"].lower()
                    
                    # Check title first (from Tavily search results)
                    name_in_title = all(p in search_title for p in name_parts)
                    company_in_title = company_lower in search_title or \
                                     self._fuzzy_company_match(search_title, company_lower)
                    
                    print(f"[TIER1 VERIFY] Title: name={name_in_title}, company={company_in_title}")
                    
                    if name_in_title and company_in_title:
                        # TIER 3: Initialize deep linking early
                        identity["handle"] = handle
                        identity["linkedin_url"] = r["url"]
                        identity["verified"] = True
                        identity["verification_source"] = "search_metadata"
                        print(f"[IDENTITY LOCKED] @{handle} (from search title)")
                        linkedin_found = True
                        break
        
        # TIER 3: DEEP LINKING - If not found via title, still accept if LinkedIn found
        # (we'll verify via browser scraping later and link cross-platform)
        if not linkedin_found:
            for r in results:
                if "linkedin.com" in r["url"]:
                    match = re.search(r'/in/([a-zA-Z0-9_-]+)', r["url"])
                    if match:
                        handle = match.group(1)
                        # Accept any LinkedIn profile found - we'll verify via deep linking
                        identity["handle"] = handle
                        identity["linkedin_url"] = r["url"]
                        identity["verified"] = False  # Will verify via scraping + linking
                        identity["verification_source"] = "linkedin_found"
                        print(f"[LINKEDIN FOUND UNVERIFIED] @{handle} - will verify via deep linking")
                        linkedin_found = True
                        break
                    if match:
                        handle = match.group(1)
                    else:
                        # Try /posts/handle pattern
                        match = re.search(r'/posts/([a-zA-Z0-9_-]+)_', r["url"])
                        if match:
                            handle = match.group(1)
                    
                    # If we got a handle and name/company match, accept it
                    if handle and (name_parts[0].lower() in search_content and company_lower in search_content):
                        identity["handle"] = handle
                        identity["linkedin_url"] = r["url"]
                        identity["verified"] = True
                        print(f"[IDENTITY LOCKED] @{handle} (from {r['url'][:60]}...)")
                        linkedin_found = True
                        break
        
        if not linkedin_found:
            print(f"[WARNING] No LinkedIn found or identity verification failed")
        
        return identity
    
    def _fuzzy_company_match(self, text: str, company: str) -> bool:
        """Fuzzy match company names"""
        # Direct match
        if company in text:
            return True
        
        # Common abbreviations
        words = company.lower().split()
        if all(w[:3] in text for w in words if len(w) >= 3):
            return True
        
        # First word + "uni" for universities
        if "university" in text and len(words) > 0:
            if words[0] in text:
                return True
        
        return False
        
        # If handle found, search for other platforms
        if identity["handle"]:
            handle = identity["handle"]
            
            # Personal site
            print(f"[SEARCH] Personal site for {name}")
            site_results = self.search.search(
                f'"{name}" site OR portfolio -linkedin -twitter -github -instagram',
                count=3
            )
            print(f"[PERSONAL SITE] Got {len(site_results)} results")
            skip = ["linkedin.com", "twitter.com", "x.com", "github.com",
                   "instagram.com", "facebook.com", "youtube.com"]
            for r in site_results:
                if not any(s in r["url"] for s in skip):
                    identity["personal_site"] = r["url"]
                    print(f"[FOUND] Personal site: {r['url']}")
                    break
            
            # Instagram
            print(f"[SEARCH] Instagram for @{handle}")
            ig_results = self.search.search(f'instagram.com/{handle}', count=2)
            for r in ig_results:
                if f"instagram.com/{handle}" in r["url"].lower():
                    identity["instagram"] = r["url"]
                    print(f"[FOUND] Instagram: {r['url']}")
                    break
            
            # GitHub (for technical roles)
            tech_keywords = ["engineer", "developer", "cto", "founder", 
                           "cs", "tech", "programmer", "architect"]
            if any(k in role.lower() for k in tech_keywords):
                print(f"[SEARCH] GitHub for {handle}")
                gh_results = self.search.search(f'github.com/{handle}', count=2)
                for r in gh_results:
                    if f"github.com/{handle}" in r["url"].lower():
                        identity["github"] = r["url"]
                        print(f"[FOUND] GitHub: {r['url']}")
                        break
            
            # Twitter
            print(f"[SEARCH] Twitter for @{handle}")
            tw_results = self.search.search(
                f'twitter.com/{handle} OR x.com/{handle}', count=2
            )
            for r in tw_results:
                if f"twitter.com/{handle}" in r["url"].lower() or \
                   f"x.com/{handle}" in r["url"].lower():
                    identity["twitter"] = r["url"]
                    print(f"[FOUND] Twitter: {r['url']}")
                    break
        
        return identity
    
    def scrape_all(self, identity: dict, name: str, company: str) -> list:
        """
        TIER 2: Sequential scraping with browser automation for LinkedIn
        + TIER 3: Deep linking across platforms
        
        Returns list of {"url": str, "content": str} with verified identity.
        """
        sources = []
        
        print(f"\n[TIER 2] Starting scrape for {name}")
        print(f"[IDENTITY] LinkedIn: {identity.get('linkedin_url', 'NONE')}")
        print(f"[IDENTITY] Personal: {identity.get('personal_site', 'NONE')}")
        print(f"[IDENTITY] GitHub: {identity.get('github', 'NONE')}")
        print(f"[IDENTITY] Twitter: {identity.get('twitter', 'NONE')}")
        print(f"[IDENTITY] Instagram: {identity.get('instagram', 'NONE')}")
        
        # Build scraping tasks - LinkedIn uses browser, others use Jina
        scrape_tasks = []
        
        if identity.get("linkedin_url"):
            # Use browser automation for LinkedIn (PRIORITY)
            scrape_tasks.append(("linkedin", identity["linkedin_url"], self.browser_scraper.scrape_profile))
        
        if identity.get("personal_site"):
            scrape_tasks.append(("personal_site", identity["personal_site"], self.jina.scrape))
        
        if identity.get("github"):
            scrape_tasks.append(("github", identity["github"], self.jina.scrape))
        
        if identity.get("twitter"):
            scrape_tasks.append(("twitter", identity["twitter"], self.jina.scrape))
        
        if identity.get("instagram"):
            scrape_tasks.append(("instagram", identity["instagram"], self.jina.scrape))
        
        if not scrape_tasks:
            print(f"[WARNING] No URLs to scrape! Identity not found or verified.")
            return sources
        
        print(f"[TIER 2] Scraping {len(scrape_tasks)} URLs sequentially...")
        
        # Sequential scraping (sync, simpler, more reliable)
        scrape_results = {}
        for source_type, url, scraper_func in scrape_tasks:
            try:
                print(f"[SCRAPE] {source_type}: {url[:60]}...")
                content = scraper_func(url)
                
                scrape_results[source_type] = {
                    "url": url,
                    "content": content,
                    "status": "success" if content else "empty"
                }
                print(f"  ✓ Got {len(content) if content else 0} chars")
                
            except Exception as e:
                print(f"  ✗ Error: {str(e)[:60]}")
                scrape_results[source_type] = {
                    "url": url,
                    "content": "",
                    "status": "failed"
                }
        
        # TIER 3: DEEP LINKING - Collect identifiers for cross-verification
        extracted_identifiers = {
            "linkedin_handle": identity.get("handle"),
            "email": identity.get("email")
        }
        
        # Process results and extract identity info
        name_parts = name.lower().split()
        company_lower = company.lower()
        
        for source_type, result in scrape_results.items():
            url = result.get("url")
            content = result.get("content", "")
            status = result.get("status")
            time_ms = result.get("time_ms", 0)
            
            print(f"\n[RESULT] {source_type.upper()}: {status} ({time_ms}ms)")
            
            if not content or status in ["empty", "failed"]:
                print(f"  -> SKIPPED: {status}")
                continue
            
            # Extract deep contact info from content
            contact_info = self.extractor.extract_contact_info(content)
            print(f"  -> Found contact info: {len(contact_info['emails'])} emails, {len(contact_info['links'])} links")
            
            # TIER 3: Update extracted identifiers for linking
            if contact_info["emails"]:
                extracted_identifiers["email"] = contact_info["emails"][0]
                extracted_identifiers["email_domain"] = contact_info["emails"][0].split("@")[1]
            
            if contact_info["social_handles"].get("github"):
                extracted_identifiers["github_handle"] = contact_info["social_handles"]["github"][0]
            
            if contact_info["social_handles"].get("twitter"):
                extracted_identifiers["twitter_handle"] = contact_info["social_handles"]["twitter"][0]
            
            # Verify content
            combined = content.lower()
            has_name = any(p in combined for p in name_parts)
            
            if source_type == "personal_site":
                # Personal sites don't always mention name/company
                if len(content) > 300:
                    sources.append({"url": url, "content": content})
                    print(f"  -> ADDED: Personal website content ({len(content)} chars)")
            elif has_name:
                sources.append({"url": url, "content": content})
                print(f"  -> ADDED: {source_type.upper()} content ({len(content)} chars)")
            else:
                print(f"  -> SKIPPED: Name not found in {source_type} content")
        
        # TIER 3: DEEP LINKING - Cross-verify identity
        print(f"\n[TIER 3] Performing deep linking analysis...")
        linkage_result = self.linkage.link_identifiers(extracted_identifiers)
        print(f"[DEEP LINK] Confidence: {linkage_result['confidence_score']:.2f}")
        print(f"[DEEP LINK] Linked platforms: {linkage_result['linked_platforms']}")
        
        # Store linkage info in identity
        identity["linkage"] = linkage_result
        identity["extracted_identifiers"] = extracted_identifiers
        
        print(f"[TIER 2-3 DONE] Scraped {len(sources)} sources with deep linking\n")
        
        # TIER 1.5: Search for recent posts using already-found identifiers
        print(f"[POSTS SEARCH] Looking for recent posts...")
        handle = identity.get("handle") or extracted_identifiers.get("github_handle") or extracted_identifiers.get("twitter_handle")
        if handle:
            self._search_and_scrape_posts(identity, name, sources, handle)
        
        return sources
    
    def _search_and_scrape_posts(self, identity: dict, name: str, sources: list, handle: str) -> None:
        """Search for and scrape multiple recent posts from each platform"""
        
        if not handle:
            return
        
        # Cache check
        cache_key = f"posts_{handle}"
        cached = self.request_cache.get(cache_key)
        if cached:
            sources.extend(cached)
            return
        
        posts_found = []
        
        # Search for recent LinkedIn posts
        print(f"[POSTS] Searching for recent posts by @{handle}...")
        linkedin_posts = self.search.search(
            f'site:linkedin.com/{handle}',
            count=2
        )
        for post in linkedin_posts[:1]:
            if "linkedin.com" in post["url"] and post["url"] not in [s["url"] for s in sources]:
                # Use Jina (browser scraping slower for posts)
                content = self.jina.scrape(post["url"])
                if content and len(content) > 200:
                    sources.append({"url": post["url"], "content": content})
                    posts_found.append({"url": post["url"], "content": content})
                    print(f"  ✓ LinkedIn post: {len(content)} chars")
        
        # Search for recent Twitter posts  
        twitter_posts = self.search.search(
            f'site:x.com/{handle} OR site:twitter.com/{handle}',
            count=2
        )
        for post in twitter_posts[:1]:
            if ("x.com" in post["url"] or "twitter.com" in post["url"]) and post["url"] not in [s["url"] for s in sources]:
                content = self.jina.scrape(post["url"])
                if content and len(content) > 100:
                    sources.append({"url": post["url"], "content": content})
                    posts_found.append({"url": post["url"], "content": content})
                    print(f"  ✓ Twitter post: {len(content)} chars")
        
        # Cache posts
        if posts_found:
            self.request_cache.set(cache_key, posts_found)
        
        # Extract photo if not found
        if not identity.get("photo_url"):
            self._extract_profile_image(identity, name, handle)
    
    def _extract_profile_image(self, identity: dict, name: str, handle: str) -> None:
        """Extract profile photo from official CDNs only"""
        
        if not handle:
            return
        
        print(f"[PHOTO] Searching for profile image...")
        
        platforms = [
            ("Twitter/X", ["pbs.twimg.com"]),
            ("LinkedIn", ["media.licdn.com"]),
            ("GitHub", ["avatars.githubusercontent.com"]),
            ("Instagram", ["scontent"]),
        ]
        
        for platform_name, official_cdns in platforms:
            if identity.get("photo_url"):
                break
            
            for cdn in official_cdns:
                if identity.get("photo_url"):
                    break
                
                # Search for images from this CDN
                search_query = f'site:{cdn} {handle}'
                results = self.search.search(search_query, count=1)
                
                for result in results:
                    # Extract image URLs
                    cdn_pattern = cdn.replace(".", r"\.")
                    images = re.findall(rf'(https://[^\s"\'<>]*?{cdn_pattern}[^\s"\'<>]*?\.(?:jpg|jpeg|png|webp))', result.get("content", ""))
                    
                    for img in images:
                        # Filter out logos/banners
                        if not any(x in img.lower() for x in ['logo', 'banner', 'icon', 'cover']):
                            identity["photo_url"] = img
                            print(f"  ✓ Found photo from {platform_name}")
                            return



