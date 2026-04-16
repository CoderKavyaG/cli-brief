"""
Researcher: Find the right person and scrape their digital footprint
with deep linking and browser automation
"""

import re
import os
from .tools import TavilySearch, JinaReader
from .advanced_scraper import (
    IdentityLinkage, LinkedInBrowserScraper, RequestCache, 
    DeepProfileExtractor, LinkExtractor
)
from .email_finder import EmailFinder


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
        self.email_finder = EmailFinder()
        self.link_extractor = LinkExtractor()
    
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
        
        # AFTER IDENTITY LOCKED: Search for other platforms
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
    
    def scrape_all(self, identity: dict, name: str, company: str) -> list:
        """
        TIER 2: Sequential scraping with browser automation for LinkedIn
        + TIER 3: Deep linking across platforms
        + TIER 1.5: Extract links from posts to discover other profiles
        
        Returns list of {"url": str, "content": str} with verified identity.
        """
        sources = []
        
        print(f"\n[TIER 2] Starting scrape for {name}")
        print(f"[IDENTITY] LinkedIn: {identity.get('linkedin_url', 'NONE')}")
        print(f"[IDENTITY] Personal: {identity.get('personal_site', 'NONE')}")
        print(f"[IDENTITY] GitHub: {identity.get('github', 'NONE')}")
        print(f"[IDENTITY] Twitter: {identity.get('twitter', 'NONE')}")
        print(f"[IDENTITY] Instagram: {identity.get('instagram', 'NONE')}")
        
        # BUILD SCRAPING TASKS - Start with known URLs
        scrape_tasks = []
        
        if identity.get("linkedin_url"):
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
        
        # EXECUTE SCRAPING
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
        
        # EXTRACT LINKS FROM POSTS - Discover other platforms
        print(f"\n[POST LINK EXTRACTION] Starting post scraping for link discovery...")
        posts = self._search_and_scrape_posts(identity, name)
        
        if posts:
            print(f"[POST LINK EXTRACTION] Found {len(posts)} posts, extracting links...")
            discovered_links = self.link_extractor.extract_links_from_posts(posts)
            
            if discovered_links:
                print(f"[POST LINK EXTRACTION] Discovered links:")
                for platform, data in discovered_links.items():
                    print(f"  {platform}: {len(data['urls'])} URLs (confidence: {data['confidence']:.2f})")
                    
                    # Add discovered platforms to sources if not already scraped
                    if platform not in [st[0] for st in scrape_tasks]:
                        for url in data["urls"]:
                            if len(url) > 10:  # Basic validation
                                try:
                                    content = self.jina.scrape(url)
                                    if content and len(content) > 200:
                                        sources.append({"url": url, "content": content})
                                        print(f"  ✓ Added {platform} link: {url[:60]} ({len(content)} chars)")
                                except Exception as e:
                                    print(f"  ✗ Failed to scrape {url[:60]}: {str(e)[:40]}")
        
        # PROCESS INITIAL SCRAPE RESULTS
        name_parts = name.lower().split()
        company_lower = company.lower()
        extracted_identifiers = {
            "linkedin_handle": identity.get("handle"),
            "email": identity.get("email")
        }
        
        for source_type, result in scrape_results.items():
            url = result.get("url")
            content = result.get("content", "")
            status = result.get("status")
            
            print(f"\n[RESULT] {source_type.upper()}: {status}")
            
            if not content or status in ["empty", "failed"]:
                print(f"  -> SKIPPED: {status}")
                continue
            
            # Extract deep contact info from content
            contact_info = self.extractor.extract_contact_info(content)
            print(f"  -> Found contact info: {len(contact_info['emails'])} emails, {len(contact_info['links'])} links")
            
            # Update extracted identifiers
            if contact_info["emails"]:
                extracted_identifiers["email"] = contact_info["emails"][0]
                extracted_identifiers["email_domain"] = contact_info["emails"][0].split("@")[1]
            
            if contact_info["social_handles"].get("github"):
                extracted_identifiers["github_handle"] = contact_info["social_handles"]["github"][0]
            
            if contact_info["social_handles"].get("twitter"):
                extracted_identifiers["twitter_handle"] = contact_info["social_handles"]["twitter"][0]
            
            # Add source (trust verified identity URLs)
            # If we already locked the identity, the URL is verified - add content regardless
            if source_type in ["personal_site", "instagram"]:
                # Personal sites and Instagram need minimum content
                if len(content) > 100:  # Lower threshold (was 300)
                    sources.append({"url": url, "content": content})
                    print(f"  -> ADDED: {source_type.upper()} content ({len(content)} chars)")
                else:
                    print(f"  -> SKIPPED: {source_type} content too short ({len(content)} chars)")
            elif source_type in ["github", "twitter"]:
                # GitHub and Twitter are identity-verified by URL - add without name check
                if len(content) > 50:  # Just need any content
                    sources.append({"url": url, "content": content})
                    print(f"  -> ADDED: {source_type.upper()} content ({len(content)} chars)")
                else:
                    print(f"  -> SKIPPED: {source_type} content too minimal ({len(content)} chars)")
            else:
                # LinkedIn and other sources - check name match
                combined = content.lower()
                has_name = any(p in combined for p in name_parts)
                if has_name:
                    sources.append({"url": url, "content": content})
                    print(f"  -> ADDED: {source_type.upper()} content ({len(content)} chars)")
                else:
                    print(f"  -> SKIPPED: Name not found in {source_type} content")
        
        # TIER 3: DEEP LINKING
        print(f"\n[TIER 3] Performing deep linking analysis...")
        linkage_result = self.linkage.link_identifiers(extracted_identifiers)
        print(f"[DEEP LINK] Confidence: {linkage_result['confidence_score']:.2f}")
        print(f"[DEEP LINK] Linked platforms: {linkage_result['linked_platforms']}")
        
        identity["linkage"] = linkage_result
        identity["extracted_identifiers"] = extracted_identifiers
        
        print(f"[TIER 2-3 DONE] Scraped {len(sources)} sources with deep linking\n")
        
        # EMAIL FINDING: Try to discover email address
        print(f"[EMAIL FINDER] Starting email discovery...")
        email_result = self._find_email(name, company, identity)
        if email_result["email"]:
            identity["email"] = email_result["email"]
            identity["email_source"] = email_result["source"]
            identity["email_variants"] = email_result["variants"]
            print(f"[EMAIL] Found: {email_result['email']} ({email_result['source']})")
        else:
            print(f"[EMAIL] No email found")
        
        return sources
    
    def _search_and_scrape_posts(self, identity: dict, name: str) -> list:
        """Search for and scrape multiple recent posts from each platform, return them for link extraction"""
        
        handle = identity.get("handle")
        if not handle:
            return []
        
        # Cache check
        cache_key = f"posts_{handle}"
        cached = self.request_cache.get(cache_key)
        if cached:
            print(f"[POSTS CACHE HIT] Returning {len(cached)} cached posts")
            return cached
        
        posts_found = []
        
        # Search for recent LinkedIn posts
        print(f"[POSTS] Searching for recent posts by @{handle}...")
        linkedin_posts = self.search.search(
            f'site:linkedin.com/{handle}',
            count=3
        )
        for post in linkedin_posts[:2]:
            if "linkedin.com" in post["url"]:
                try:
                    content = self.jina.scrape(post["url"])
                    if content and len(content) > 150:
                        posts_found.append({"url": post["url"], "content": content, "platform": "linkedin"})
                        print(f"  ✓ LinkedIn post: {len(content)} chars")
                except Exception as e:
                    print(f"  ✗ LinkedIn post failed: {str(e)[:40]}")
        
        # Search for recent Twitter posts  
        twitter_posts = self.search.search(
            f'site:x.com/{handle} OR site:twitter.com/{handle}',
            count=3
        )
        for post in twitter_posts[:2]:
            if "x.com" in post["url"] or "twitter.com" in post["url"]:
                try:
                    content = self.jina.scrape(post["url"])
                    if content and len(content) > 80:
                        posts_found.append({"url": post["url"], "content": content, "platform": "twitter"})
                        print(f"  ✓ Twitter post: {len(content)} chars")
                except Exception as e:
                    print(f"  ✗ Twitter post failed: {str(e)[:40]}")
        
        # Extract profile image if not found
        if not identity.get("photo_url"):
            self._extract_profile_image(identity, name, handle)
        
        # Cache posts for 5 minutes
        if posts_found:
            self.request_cache.set(cache_key, posts_found)
            print(f"[POSTS] Cached {len(posts_found)} posts")
        
        return posts_found
    
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
    
    def _find_email(self, name: str, company: str, identity: dict) -> dict:
        """Find email using EmailFinder with domain fallback"""
        
        # Strategy 1: Check if already extracted from content
        if identity.get("email"):
            return {
                "email": identity["email"],
                "source": "extracted",
                "variants": [],
                "confidence": 0.7
            }
        
        # Strategy 2: Extract domain from LinkedIn if available
        domain = None
        if identity.get("linkedin_url"):
            # Try to extract company domain from LinkedIn search or scrape
            # For now, use email finder's company-to-domain lookup
            domain = self.email_finder.find_domain_from_company(company)
        
        # Strategy 3: Use Hunter.io if we have domain
        if domain:
            email_result = self.email_finder.find_email(name, company, domain)
            if email_result["email"]:
                return email_result
        
        # Strategy 4: Try without domain (Hunter will attempt to find domain)
        email_result = self.email_finder.find_email(name, company)
        if email_result["email"]:
            return email_result
        
        return {
            "email": None,
            "source": "none",
            "variants": [],
            "confidence": 0.0
        }



