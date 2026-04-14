"""
Researcher: Find the right person and scrape their digital footprint
"""

import re
import os
from .tools import TavilySearch, JinaReader


class Researcher:
    """Find a person's identity and scrape their digital presence"""
    
    def __init__(self):
        api_key = os.getenv("TAVILY_API_KEY")
        self.search = TavilySearch(api_key)
        self.jina = JinaReader()
    
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
        
        # First pass: Look for LinkedIn /in/ profile
        linkedin_found = False
        for r in results:
            if "linkedin.com/in/" in r["url"]:
                print(f"[LINKEDIN FOUND] {r['url']}")
                # Extract handle from URL
                match = re.search(r'linkedin\.com/in/([a-zA-Z0-9_-]+)', r["url"])
                if match:
                    handle = match.group(1)
                    print(f"[HANDLE EXTRACTED] {handle}")
                    
                    # Verify this result mentions name AND company
                    combined = (r["title"] + " " + r["content"]).lower()
                    name_parts = name.lower().split()
                    company_lower = company.lower()
                    
                    print(f"[VERIFY] Looking for: {name_parts} + {company_lower}")
                    print(f"[VERIFY] In: {combined[:100]}...")
                    
                    name_check = all(p in combined for p in name_parts)
                    company_check = company_lower in combined
                    
                    print(f"[VERIFY] Name match: {name_check}, Company match: {company_check}")
                    
                    if name_check and company_check:
                        identity["handle"] = handle
                        identity["linkedin_url"] = r["url"]
                        identity["verified"] = True
                        print(f"[IDENTITY LOCKED] @{handle}")
                        linkedin_found = True
                        break
        
        # Second pass if no /in/ found: Look for any linkedin.com URL and extract handle
        if not linkedin_found:
            for r in results:
                if "linkedin.com" in r["url"]:
                    combined = (r["title"] + " " + r["content"]).lower()
                    name_parts = name.lower().split()
                    company_lower = company.lower()
                    
                    # Very flexible handle extraction from any LinkedIn URL
                    handle = None
                    
                    # Try /in/handle pattern
                    match = re.search(r'/in/([a-zA-Z0-9_-]+)', r["url"])
                    if match:
                        handle = match.group(1)
                    else:
                        # Try /posts/handle pattern
                        match = re.search(r'/posts/([a-zA-Z0-9_-]+)_', r["url"])
                        if match:
                            handle = match.group(1)
                    
                    # If we got a handle and name/company match, accept it
                    if handle and (name_parts[0].lower() in combined and company_lower in combined):
                        identity["handle"] = handle
                        identity["linkedin_url"] = r["url"]
                        identity["verified"] = True
                        print(f"[IDENTITY LOCKED] @{handle} (from {r['url'][:60]}...)")
                        linkedin_found = True
                        break
        
        if not linkedin_found:
            print(f"[WARNING] No LinkedIn found or identity verification failed")
        
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
        Scrape all found URLs. Return list of {"url": str, "content": str}.
        Only include content that verifies the person's identity.
        """
        sources = []
        urls_to_scrape = []
        
        print(f"\n[SCRAPE_ALL] Starting scrape for {name}")
        print(f"[IDENTITY] LinkedIn: {identity.get('linkedin_url', 'NONE')}")
        print(f"[IDENTITY] Personal: {identity.get('personal_site', 'NONE')}")
        print(f"[IDENTITY] Instagram: {identity.get('instagram', 'NONE')}")
        print(f"[IDENTITY] GitHub: {identity.get('github', 'NONE')}")
        print(f"[IDENTITY] Twitter: {identity.get('twitter', 'NONE')}")
        
        # Priority order: personal site first (best info), then LinkedIn
        if identity.get("personal_site"):
            urls_to_scrape.append(("personal_site", identity["personal_site"]))
        if identity.get("linkedin_url"):
            urls_to_scrape.append(("linkedin", identity["linkedin_url"]))
        if identity.get("instagram"):
            urls_to_scrape.append(("instagram", identity["instagram"]))
        if identity.get("github"):
            urls_to_scrape.append(("github", identity["github"]))
        if identity.get("twitter"):
            urls_to_scrape.append(("twitter", identity["twitter"]))
        
        if not urls_to_scrape:
            print(f"[WARNING] No URLs to scrape! Identity not found or verified.")
            return sources
        
        print(f"[SCRAPE_ALL] Will scrape {len(urls_to_scrape)} URLs")
        
        name_parts = name.lower().split()
        company_lower = company.lower()
        
        for source_type, url in urls_to_scrape[:5]:
            print(f"[SCRAPING {source_type}] {url[:70]}")
            content = self.jina.scrape(url)
            print(f"[JINA RESULT] Got {len(content)} chars")
            
            if not content:
                print(f"  -> SKIPPED: Empty content")
                continue
            
            # Personal sites: ALWAYS accept valid content (portfolio sites may not mention name in all sections)
            if source_type == "personal_site":
                # Check if content looks like a valid portfolio/site (has text, links, etc)
                has_content = len(content) > 500
                has_structure = (
                    ("http" in content.lower() or "#" in content or content.count("\n") > 5) and
                    content.count(name_parts[0]) >= 0  # Don't strictly require name
                )
                
                should_accept = has_content or has_structure
                print(f"  -> Content check: length={len(content)}, has_structure={has_structure}")
                
                if should_accept:
                    sources.append({"url": url, "content": content})
                    print(f"  -> ADDED: {len(content)} chars (portfolio/site content)")
                    
                    # Extract photo URL
                    if not identity.get("photo_url"):
                        photo = re.search(
                            r'https?://[^\s"\']+\.(?:jpg|jpeg|png|webp)',
                            content
                        )
                        if photo:
                            identity["photo_url"] = photo.group(0)
                            print(f"  -> Photo found: {identity['photo_url'][:50]}")
                    
                    # Extract email
                    if not identity.get("email"):
                        email = re.search(
                            r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b',
                            content
                        )
                        if email:
                            identity["email"] = email.group(0)
                            print(f"  -> Email found: {identity['email']}")
                else:
                    print(f"  -> SKIPPED: Not enough valid content")
            
            # LinkedIn, GitHub, Twitter, Instagram: verify identity
            else:
                combined = content.lower()
                has_name = any(p in combined for p in name_parts)
                print(f"  -> Name check: {has_name}")
                
                if has_name:
                    sources.append({"url": url, "content": content})
                    print(f"  -> ADDED: {len(content)} chars")
                else:
                    print(f"  -> SKIPPED: Name not found in {source_type} content")
        
        print(f"[SCRAPE_ALL DONE] Scraped {len(sources)} sources\n")
        
        # ENHANCEMENT: Search for and scrape recent posts/tweets from each platform for more depth
        print(f"[POSTS SEARCH] Looking for recent posts from each platform...")
        self._search_and_scrape_posts(identity, name, sources)
        
        return sources
    
    def _search_and_scrape_posts(self, identity: dict, name: str, sources: list) -> None:
        """Search for and scrape multiple recent posts from each platform"""
        
        handle = identity.get("handle")
        if not handle:
            return
        
        # Search for recent LinkedIn posts
        if handle:
            print(f"[POSTS] Searching for recent LinkedIn posts by @{handle}...")
            linkedin_posts = self.search.search(
                f'site:linkedin.com/{handle} OR site:linkedin.com/in/{handle}',
                count=3
            )
            for post in linkedin_posts[:2]:  # Get up to 2 more posts
                if "linkedin.com" in post["url"] and post["url"] not in [s["url"] for s in sources]:
                    content = self.jina.scrape(post["url"])
                    if content and len(content) > 300:
                        sources.append({"url": post["url"], "content": content})
                        print(f"  [LINKEDIN POST] Added {len(content)} chars from {post['url'][:50]}")
        
        # Search for recent Twitter/X posts  
        if handle:
            print(f"[POSTS] Searching for recent Twitter posts by @{handle}...")
            twitter_posts = self.search.search(
                f'site:x.com/{handle} OR site:twitter.com/{handle}',
                count=3
            )
            for post in twitter_posts[:2]:  # Get up to 2 more posts
                if ("x.com" in post["url"] or "twitter.com" in post["url"]) and post["url"] not in [s["url"] for s in sources]:
                    content = self.jina.scrape(post["url"])
                    if content and len(content) > 200:
                        sources.append({"url": post["url"], "content": content})
                        print(f"  [TWITTER POST] Added {len(content)} chars from {post['url'][:50]}")
        
        # Search for recent Instagram posts
        if handle:
            print(f"[POSTS] Searching for recent Instagram posts by @{handle}...")
            insta_posts = self.search.search(
                f'site:instagram.com/{handle}',
                count=2
            )
            for post in insta_posts[:1]:  # Get 1 more post
                if "instagram.com" in post["url"] and post["url"] not in [s["url"] for s in sources]:
                    content = self.jina.scrape(post["url"])
                    if content and len(content) > 200:
                        sources.append({"url": post["url"], "content": content})
                        print(f"  [INSTAGRAM POST] Added {len(content)} chars from {post['url'][:50]}")
        
        # Extract profile image if not found yet
        if not identity.get("photo_url"):
            print(f"[PHOTO] Searching for profile image...")
            self._extract_profile_image(identity, name, handle)
    
    def _extract_profile_image(self, identity: dict, name: str, handle: str) -> None:
        """Search for and extract profile image from various platforms - ONLY from official CDNs"""
        
        if not handle:
            return
        
        print(f"[PHOTO] Searching for profile image...")
        
        # ONLY accept images from official platform CDNs - NO generic websites!
        platforms_to_check = [
            ("Twitter/X", "x.com", ["pbs.twimg.com", "twitter.com/profile_images"], 2),
            ("LinkedIn", "linkedin.com/in", ["media.licdn.com", "linkedin.com/media", "platform.linkedin.com"], 1),
            ("Instagram", "instagram.com", ["instagram.com/profile_images", "scontent"], 1),
            ("GitHub", "github.com", ["avatars.githubusercontent.com"], 1),
        ]
        
        for platform_name, platform_url, official_cdns, count in platforms_to_check:
            if identity.get("photo_url"):
                break
                
            print(f"[PHOTO] Checking {platform_name}...")
            search_query = f'site:{platform_url}/{handle}'
            results = self.search.search(search_query, count=count)
            
            for result in results:
                if identity.get("photo_url"):
                    break
                    
                if platform_url in result.get("url", ""):
                    try:
                        content = self.jina.scrape(result["url"])
                        if not content or len(content) < 100:
                            continue
                        
                        # ONLY extract images from official platform CDNs
                        for official_cdn in official_cdns:
                            if identity.get("photo_url"):
                                break
                            
                            # Build safe regex that ONLY matches official CDN URLs
                            cdn_safe = official_cdn.replace(".", r"\.")
                            pattern = rf'(https://[^\s"\'<>]*?{cdn_safe}[^\s"\'<>]*?\.(?:jpg|jpeg|png|webp))'
                            images = re.findall(pattern, content)
                            
                            # Filter out obviously fake or large image URLs
                            for img_url in images:
                                # Skip if URL is too long (usually fake)
                                if len(img_url) > 300:
                                    continue
                                # Skip if contains common non-profile-pic patterns
                                if any(x in img_url.lower() for x in ['banner', 'header', 'cover', 'background', 'logo', 'icon']):
                                    continue
                                
                                identity["photo_url"] = img_url
                                print(f"  [PHOTO FOUND] {platform_name}: {img_url[:60]}")
                                return
                    except Exception as e:
                        print(f"  [PHOTO ERROR] {platform_name}: {str(e)[:50]}")
                        continue
        
        if not identity.get("photo_url"):
            print(f"  [NO PHOTO FOUND] No profile image from official sources")



