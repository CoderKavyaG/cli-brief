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
                    
                    # Try /posts/handle pattern if not an /in/ URL
                    handle = None
                    match = re.search(r'/posts/([a-zA-Z0-9_-]+)_', r["url"])
                    if match:
                        handle = match.group(1)
                    
                    # If we got a handle and name/company match, accept it
                    search_content = r.get("content", "").lower()
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
            
            # Personal site - search with HANDLE FIRST (more unique + validate)
            print(f"[SEARCH] Personal site for {name} (@{handle})")
            # Prioritize handle - more unique and specific than full name
            site_queries = [
                f'{handle} portfolio OR site OR about',
                f'{handle} -linkedin -github -twitter',
                f'"{name}" portfolio -linkedin',
            ]
            
            identity["personal_site"] = None
            identity["company_domain"] = None
            skip = ["linkedin", "twitter", "github", "instagram", "facebook", 
                   "youtube", "help.", "support.", "docs.", "medium.com", "reddit"]
            # Skip institutional/aggregator/portfolio sites - these are NOT personal websites
            skip_domains = ["slideshare", "about.me", "beacons", "taplink", "carrd", "wix",
                           "slidingscale", "gravatar", "resume.com", "minteractive", "resumepace",
                           "scribd", "pinterest", "issuu", 
                           # Institutional and talent/portfolio aggregators
                           "lshtm.ac.uk", "hercampus", "university", "college", "school",
                           "talentrack", "talent", "profile", "portfolio"]
            
            name_lower = name.lower()
            for query in site_queries:
                site_results = self.search.search(query, count=5)
                print(f"[PERSONAL SITE] Searching: {query} ({len(site_results)} results)")
                
                for r in site_results:
                    url_lower = r["url"].lower()
                    domain_lower = url_lower.split("/")[2].replace("www.", "")
                    title_lower = r.get("title", "").lower()
                    content_lower = r.get("content", "").lower()[:500]
                    
                    # Skip blacklist
                    if any(s in url_lower for s in skip):
                        continue
                    if any(s in domain_lower for s in skip_domains):
                        continue
                    
                    # VALIDATE: Content must mention the person
                    mentions = (handle in url_lower or handle in title_lower or 
                               handle in content_lower or name_lower in title_lower)
                    
                    # Extract company domain if visible
                    if company.lower() in domain_lower:
                        identity["company_domain"] = domain_lower
                    
                    if mentions:
                        print(f"[FOUND] {url_lower[:60]} (mentions person)")
                        identity["personal_site"] = r["url"]
                        break
                
                if identity["personal_site"]:
                    break
            
            if not identity["personal_site"]:
                print(f"[PERSONAL SITE] No valid personal site found")
            
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
            
            # Twitter - get PROFILE URL, not tweet URLs
            print(f"[SEARCH] Twitter for @{handle}")
            tw_results = self.search.search(
                f'twitter.com/{handle} OR x.com/{handle}', count=3
            )
            print(f"[TWITTER DEBUG] Got {len(tw_results)} results")
            for i, r in enumerate(tw_results):
                url_lower = r["url"].lower()
                print(f"[TWITTER DEBUG] Result {i+1}: {url_lower[:80]}")
                print(f"  Has /status/: {'/status/' in url_lower}")
                print(f"  Has twitter.com/{handle}: {'twitter.com/' + handle in url_lower}")
                print(f"  Has x.com/{handle}: {'x.com/' + handle in url_lower}")
                
                # Only accept profile URLs, NOT tweet/status URLs
                if "/status/" not in url_lower and "/web/" not in url_lower:
                    if (f"twitter.com/{handle}" in url_lower or \
                        f"x.com/{handle}" in url_lower):
                        identity["twitter"] = r["url"]
                        print(f"[FOUND] Twitter: {r['url']}")
                        break
                else:
                    print(f"[TWITTER DEBUG] Skipped (has /status/ or /web/)")
            
            if not identity.get("twitter"):
                print(f"[TWITTER DEBUG] No profile URL found, may only have tweets")
        
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
        print(f"[IDENTITY] Company Domain: {identity.get('company_domain', 'NONE')}")
        
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
        
        # EXECUTE SCRAPING CONCURRENTLY
        scrape_results = {}
        import concurrent.futures
        
        def run_scrape(task):
            source_type, url, scraper_func = task
            try:
                print(f"[SCRAPE] {source_type}: {url[:60]}...")
                content = scraper_func(url)
                print(f"  [OK] {source_type} Got {len(content) if content else 0} chars")
                return source_type, {
                    "url": url,
                    "content": content,
                    "status": "success" if content else "empty"
                }
            except Exception as e:
                print(f"  [ERROR] {source_type} {str(e)[:60]}")
                return source_type, {
                    "url": url,
                    "content": "",
                    "status": "failed"
                }

        print(f"[TIER 2] Scraping {len(scrape_tasks)} URLs concurrently...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(run_scrape, task) for task in scrape_tasks]
            for future in concurrent.futures.as_completed(futures):
                source_type, result = future.result()
                scrape_results[source_type] = result
        
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
        handle = identity.get("handle", "").lower()
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
            
            # VALIDATION: For non-LinkedIn sources, verify person is mentioned
            content_lower = content.lower()
            if source_type != "linkedin":
                has_person = (handle in content_lower or 
                             any(p in content_lower for p in name_parts if len(p) > 3) or
                             company_lower in content_lower)
                
                if not has_person:
                    print(f"  -> VALIDATION FAILED: Person not mentioned in {source_type}")
                    continue
            
            # Extract deep contact info from content
            contact_info = self.extractor.extract_contact_info(content)
            print(f"  -> VALIDATED: Found {len(contact_info['emails'])} emails")
            
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
        
        # PROPAGATE EXTRACTED IDENTIFIERS BACK TO IDENTITY DICT
        # So app.py can return them in the response
        print(f"[EXTRACTION] Propagating extracted identifiers to identity dict...")
        if extracted_identifiers.get("github_handle"):
            # Build full GitHub URL if only handle is available
            gh_input = extracted_identifiers["github_handle"]
            if gh_input.startswith("http"):
                identity["github"] = gh_input
            else:
                identity["github"] = f"https://github.com/{gh_input}"
            print(f"[EXTRACTION] GitHub: {identity['github']}")
        
        if extracted_identifiers.get("twitter_handle"):
            # Build full Twitter URL if only handle is available
            tw_input = extracted_identifiers["twitter_handle"]
            if tw_input.startswith("http"):
                identity["twitter"] = tw_input
            else:
                identity["twitter"] = f"https://x.com/{tw_input}"
            print(f"[EXTRACTION] Twitter: {identity['twitter']}")
        
        if extracted_identifiers.get("instagram_handle"):
            # Build full Instagram URL if only handle is available
            ig_input = extracted_identifiers["instagram_handle"]
            if ig_input.startswith("http"):
                identity["instagram"] = ig_input
            else:
                identity["instagram"] = f"https://www.instagram.com/{ig_input}/"
            print(f"[EXTRACTION] Instagram: {identity['instagram']}")
        
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
        """Try to extract profile photo - optional, doesn't block research"""
        
        if not handle:
            return
        
        try:
            # Quick attempt: try LinkedIn media search only (minimal API usage)
            print(f"[PHOTO] Attempting to fetch profile image...")
            results = self.search.search(f'site:media.licdn.com {handle}', count=1)
            
            if results and results[0].get("content"):
                content = results[0]["content"]
                # Look for image URL pattern
                images = re.findall(r'(https://[^\s"\'<>]*?media\.licdn\.com[^\s"\'<>]*?\.jpg)', content)
                
                if images:
                    identity["photo_url"] = images[0]
                    print(f"  ✓ Found photo from LinkedIn")
                    return
            
            print(f"  [SKIP] No profile photo available")
        except Exception as e:
            # Image extraction is optional - don't fail research if it fails
            print(f"  [SKIP] Photo extraction error (non-critical): {str(e)[:40]}")
    
    def _find_email(self, name: str, company: str, identity: dict) -> dict:
        """
        ONLY extract email from verified scraped content.
        DO NOT guess patterns or use Hunter API - email MUST be explicitly found in content.
        """
        
        print(f"[EMAIL] Finding email for {name}...")
        
        # ONLY: Extract from content if found
        extracted_identifiers = identity.get("extracted_identifiers", {})
        if extracted_identifiers.get("email"):
            email = extracted_identifiers["email"]
            print(f"[EMAIL] ✓ VERIFIED from content: {email}")
            return {
                "email": email,
                "source": "extracted_from_content",
                "variants": [],
                "confidence": 0.95,
                "finder_method": "content_extraction"
            }
        
        print(f"[EMAIL] ✗ Could not verify from content - NOT reporting email")
        return {
            "email": None,
            "source": "none",
            "variants": [],
            "confidence": 0.0,
            "finder_method": "none"
        }



