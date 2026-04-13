#!/usr/bin/env python3
"""
Phase 1: Agent Loop with Groq Tool Calling
Intel briefing agent - Groq decides what tools to call
"""

import sys
import json
import requests
import time
from datetime import datetime
from typing import Optional, List, Dict, Any

from phase1_agent.config import GROQ_API_KEY, GROQ_MODEL, GROQ_API_URL, OUTPUT_DIR
from phase1_agent.models import Person, Briefing, SearchResult, ScrapedContent
from phase1_agent.tools import TavilySearch, JinaScrape, FileSave, LinkExtractor
from phase1_agent.prompts import SYSTEM_PROMPT, get_user_prompt
from phase1_agent.cache import BriefingCache
from phase1_agent.quality import BriefingValidator
import os
import re

class IntelAgent:
    """Main agent that orchestrates research via Groq tool calling"""
    
    def __init__(self):
        self.cache = BriefingCache()
        self.search_tool = TavilySearch()
        self.scrape_tool = JinaScrape()
        self.file_tool = FileSave()
        self.messages = []
        self.search_count = 0
        self.scrape_count = 0
        self.scrape_success = 0
        self.scraped_contents = []  # Track all scraped content for synthesis
        self.identity_locked = None  # Store locked identity handle for verification
        self.verified_urls = []  # Store verified URLs that matched identity
        self.footprint = {}  # Store extracted footprint data (photo, bio, email, etc)
    
    def find_digital_footprint(self, person):
        """
        Find digital identity using company+city for disambiguation
        Lock identity by handle to prevent mixing data with other people with same name
        """
        footprint = {
            "linkedin": None,
            "instagram": None,
            "twitter": None,
            "github": None,
            "personal_site": None,
            "confirmed_urls": [],
            "handle": None,  # LOCK: use handle to prevent identity mixing
            "photo_url": None
        }
        
        # Search with company+city for strong disambiguation
        # This returns the CORRECT person more reliably
        search_query = f'"{person.name}" "{person.company}"'
        print(f"[IDENTITY] Finding {person.name} with company lock: {search_query}")
        
        results = self.search_tool.search(search_query, count=5)
        
        # Extract handle from first confirmed LinkedIn URL
        for r in results:
            if "linkedin.com/in/" in r.url:
                handle_match = re.search(
                    r'linkedin\.com/in/([a-zA-Z0-9_-]+)',
                    r.url
                )
                if handle_match:
                    footprint["handle"] = handle_match.group(1)
                    footprint["linkedin"] = r.url
                    footprint["confirmed_urls"].append(r.url)
                    self.identity_locked = footprint["handle"]
                    self.verified_urls.append(r.url)
                    print(f"[IDENTITY LOCKED] Handle: {footprint['handle']}")
                    print(f"[VERIFIED URL] LinkedIn: {r.url}")
                    break
        
        # BUG FIX 1: Extract personal sites from all search results
        # Look for non-social domains that might be personal sites
        for r in results:
            url = r.url
            # Skip known social platforms
            skip = ["linkedin.com", "instagram.com", "twitter.com",
                    "x.com", "github.com", "facebook.com", 
                    "youtube.com", "wikipedia.org", "crunchbase.com",
                    "rocketreach.co", "zoominfo.com"]
            
            if not any(s in url for s in skip):
                # This is likely a personal site
                footprint["personal_site"] = url
                footprint["confirmed_urls"].append(url)
                print(f"[FOOTPRINT] Personal site: {url}")
                break
        
        # If we found a handle, use it for ALL subsequent searches
        # This prevents finding wrong person when searching by name alone
        handle = footprint["handle"]
        
        # BUG FIX 1: Immediately scrape LinkedIn in footprint step
        if footprint["linkedin"]:
            print(f"[FOOTPRINT SCRAPE] LinkedIn: {footprint['linkedin']}")
            li_content = self.scrape_tool.scrape(footprint["linkedin"])
            if li_content and self.is_right_person(
                li_content.content, person.name, person.company
            ):
                self.scraped_contents.append(li_content)
                print(f"[FOOTPRINT SCRAPED] LinkedIn: {len(li_content.content)} chars")
        
        # BUG FIX 1: Immediately scrape personal site in footprint step
        if footprint["personal_site"]:
            print(f"[FOOTPRINT SCRAPE] Personal site: {footprint['personal_site']}")
            site_content = self.scrape_tool.scrape(footprint["personal_site"])
            if site_content and len(site_content.content) > 200:
                # Personal site - relax identity check
                # (may not mention company name explicitly)
                self.scraped_contents.append(site_content)
                print(f"[FOOTPRINT SCRAPED] Personal site: {len(site_content.content)} chars")
                
                # CHANGE 1: Extract personal site data - photo, bio, email, github, twitter
                content = site_content.content
                
                # Extract photo URL - look for ibb.co, imgur, cdn, .jpg/.png near Profile/Avatar
                photo_match = re.search(
                    r'(?:https?://)?(?:i\.)?(?:ibb\.co|imgur\.com|cdn|\.jpg|\.png)[^\s"\'<>]*',
                    content,
                    re.IGNORECASE
                )
                if photo_match:
                    photo_url = photo_match.group(0)
                    if not photo_url.startswith('http'):
                        photo_url = 'https://' + photo_url
                    footprint["photo_url"] = photo_url
                    print(f"[PHOTO] Found: {photo_url}")
                
                # Extract email - pattern: word.chars@domain.ext
                email_match = re.search(r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b', content)
                if email_match:
                    footprint["email"] = email_match.group(0)
                    print(f"[EMAIL] Found: {footprint['email']}")
                
                # Extract GitHub URL
                github_match = re.search(r'(?:https?://)?(?:www\.)?github\.com/[a-zA-Z0-9_-]+', content)
                if github_match:
                    github_url = github_match.group(0)
                    if not github_url.startswith('http'):
                        github_url = 'https://' + github_url
                    footprint["github"] = github_url
                    print(f"[GITHUB] Found: {github_url}")
                
                # Extract Twitter/X URL
                twitter_match = re.search(r'(?:https?://)?(?:www\.)?(?:twitter\.com|x\.com)/[a-zA-Z0-9_]+', content)
                if twitter_match:
                    twitter_url = twitter_match.group(0)
                    if not twitter_url.startswith('http'):
                        twitter_url = 'https://' + twitter_url
                    footprint["twitter"] = twitter_url
                    print(f"[TWITTER] Found: {twitter_url}")
                
                # Extract bio - first paragraph after name
                # Look for first substantial paragraph (100+ chars)
                paragraphs = re.split(r'\n{2,}', content)
                for para in paragraphs:
                    if len(para) > 100 and person.name.lower() not in para.lower():
                        # Skip the heading, get first real paragraph
                        bio = ' '.join(para.split()[:50])  # First 50 words
                        if len(bio) > 50:
                            footprint["bio"] = bio
                            print(f"[BIO] Found: {bio[:100]}")
                            break
                
                # CHANGE 5: Store footprint on self for use in synthesis
                self.footprint = footprint
        
        if handle:
            # Search Instagram using handle to avoid name collisions
            ig_results = self.search_tool.search(
                f'instagram.com/{handle} OR "@{handle}"',
                count=3
            )
            for r in ig_results:
                if "instagram.com/" in r.url and handle.lower() in r.url.lower():
                    footprint["instagram"] = r.url
                    footprint["confirmed_urls"].append(r.url)
                    self.verified_urls.append(r.url)
                    print(f"[VERIFIED URL] Instagram: {r.url}")
                    break
            
            # Search Twitter using handle to avoid name collisions
            tw_results = self.search_tool.search(
                f'twitter.com/{handle} OR x.com/{handle}',
                count=3
            )
            for r in tw_results:
                if ("twitter.com/" in r.url or "x.com/" in r.url):
                    footprint["twitter"] = r.url
                    footprint["confirmed_urls"].append(r.url)
                    self.verified_urls.append(r.url)
                    print(f"[VERIFIED URL] Twitter: {r.url}")
                    break
        
        return footprint
    
    def is_right_person(self, content, person_name, company):
        """
        Verify scraped content is actually about the correct person
        Prevents mixing data from people with same name
        
        BUG FIX 3: Accept content if:
        - EITHER (name + company) together
        - OR (name + handle) where handle is the locked identity  
        - OR (name alone in long personal site content)
        """
        if not content:
            return False
        
        content_lower = content.lower()
        first_name = person_name.split()[0].lower()
        last_name = person_name.split()[-1].lower() if len(person_name.split()) > 1 else ""
        company_lower = company.lower()
        
        has_name = (first_name in content_lower and last_name in content_lower) if last_name else first_name in content_lower
        has_company = company_lower in content_lower
        has_handle = (self.identity_locked and 
                      self.identity_locked.lower() in content_lower)
        
        # Accept if name+company OR name+handle
        if has_name and (has_company or has_handle):
            print(f"[IDENTITY VERIFIED] Content matches {person_name} + {company}")
            return True
        
        # Also accept personal sites (URL contains handle)
        # These are already verified by URL pattern
        if has_name and len(content) > 500:
            # Long content with the person's name - likely right person (personal site)
            print(f"[IDENTITY VERIFIED] Content has name + long personal site content ({len(content)} chars)")
            return True
        
        print(f"[IDENTITY REJECTED] Content doesn't match {person_name} + {company}")
        return False
    
    def detect_alerts(self, scraped_contents, person_name):
        """Scan scraped content for high-signal events and return alerts"""
        alerts = []
        
        # Extract first and last name for better matching
        name_parts = person_name.lower().split()
        first_name = name_parts[0] if name_parts else ""
        
        role_keywords = ["resigned", "stepping down", "new ceo", 
                         "appointed as", "leaving", "departed", 
                         "replaced by", "transition", "steps down"]
        
        funding_keywords = ["raised", "funding round", "valuation", 
                            "series a", "series b", "series c",
                            "billion", "ipo", "acquisition", "acquired"]
        
        controversy_keywords = ["lawsuit", "controversy", "fired", 
                                "scandal", "investigation", "charged",
                                "alleged", "backlash", "criticism",
                                "arrested", "fraud", "accused"]
        
        launch_keywords = ["launched", "announced", "unveiled", 
                           "introducing", "new product", "new feature",
                           "beta", "released", "just launched"]
        
        for source in scraped_contents:
            content_lower = source.content.lower()
            domain = source.url.split('/')[2].replace('www.', '')
            
            # Get the sentence containing the keyword
            sentences = source.content.split('.')
            
            for sentence in sentences:
                sentence_lower = sentence.lower()
                real_sentence = sentence.strip()
                
                # VALIDATE: Only create alerts if the sentence is real and meaningful
                if len(real_sentence) < 25:
                    continue  # Too short to be meaningful
                if not any(c.isalpha() for c in real_sentence):
                    continue  # No real words
                
                # IMPORTANT: Only create alerts if the person's name is ACTUALLY mentioned
                # This prevents alerts about unrelated tech news
                has_name = first_name in sentence_lower or person_name.lower() in sentence_lower
                
                if not has_name:
                    continue  # Skip this sentence if person not mentioned
                
                # Check role changes
                if any(kw in sentence_lower for kw in role_keywords):
                    alerts.append({
                        "type": "role_change",
                        "emoji": "[ALERT]",
                        "label": "ROLE CHANGE DETECTED",
                        "text": real_sentence[:200],
                        "source": domain,
                        "url": source.url,
                        "priority": 1
                    })
                
                # Check funding
                if any(kw in sentence_lower for kw in funding_keywords):
                    alerts.append({
                        "type": "funding",
                        "emoji": "[FUNDING]", 
                        "label": "FUNDING EVENT",
                        "text": sentence.strip()[:200],
                        "source": domain,
                        "url": source.url,
                        "priority": 2
                    })
                
                # Check controversy
                if any(kw in sentence_lower for kw in controversy_keywords):
                    alerts.append({
                        "type": "controversy",
                        "emoji": "[WARNING]",
                        "label": "CONTROVERSY FLAGGED", 
                        "text": real_sentence[:200],
                        "source": domain,
                        "url": source.url,
                        "priority": 1
                    })
                
                # Check launches
                if any(kw in sentence_lower for kw in launch_keywords):
                    alerts.append({
                        "type": "launch",
                        "emoji": "[LAUNCH]",
                        "label": "RECENT LAUNCH",
                        "text": sentence.strip()[:200],
                        "source": domain,
                        "url": source.url,
                        "priority": 3
                    })
        
        # Remove duplicates (same text appearing in multiple sources)
        seen_texts = set()
        unique_alerts = []
        for alert in alerts:
            # Use first 50 chars as dedup key
            key = alert["text"][:50].lower()
            if key not in seen_texts:
                seen_texts.add(key)
                unique_alerts.append(alert)
        
        # Sort by priority (1=highest)
        unique_alerts.sort(key=lambda x: x["priority"])
        
        # Limit to top 5 most important
        return unique_alerts[:5]
    
    def _call_groq_with_tools(self, messages: List[Dict], tools: List[Dict], system_message: str = None) -> Dict:
        """Call Groq API with tool calling support"""
        max_retries = 5  # Increased retries for rate limits
        base_wait = 3    # Longer initial wait
        
        # Prepend system message if provided
        if system_message:
            messages_to_send = [
                {"role": "system", "content": system_message}
            ] + messages
        else:
            messages_to_send = messages
        
        for attempt in range(max_retries):
            try:
                headers = {
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                }
                
                response = requests.post(
                    GROQ_API_URL,
                    json={
                        "model": GROQ_MODEL,
                        "messages": messages_to_send,
                        "tools": tools,
                        "temperature": 0.7,
                        "max_tokens": 2000
                    },
                    headers=headers,
                    timeout=30
                )
                response.raise_for_status()
                return response.json()
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:  # Rate limit
                    if attempt < max_retries - 1:
                        wait_time = base_wait * (2 ** attempt)
                        print(f"\n{'='*60}")
                        print(f"[GROQ RATE LIMITED] Hit API rate limit (429)")
                        print(f"Reason: Groq free tier limits requests to ~30 req/min")
                        print(f"Retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})...")
                        print(f"{'='*60}\n")
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"\n{'='*60}")
                        print(f"[GROQ ERROR] Rate limit hit {max_retries} times")
                        print(f"⚠️  SOLUTION: Wait a few minutes before trying again")
                        print(f"{'='*60}\n")
                        raise
                if e.response.status_code == 400:
                    # Try to extract useful info from 400 error
                    error_text = e.response.text
                    print(f"[GROQ 400 ERROR] Bad Request")
                    print(f"[GROQ] Response: {error_text[:500]}")
                    
                    # Try to extract failed_generation content
                    if "failed_generation" in error_text:
                        try:
                            error_json = json.loads(error_text)
                            failed_gen = error_json.get("error", {}).get("failed_generation", "")
                            if failed_gen:
                                print(f"[GROQ] Failed generation extracted: {failed_gen[:200]}")
                                # Return a synthetic response with the generated content as assistant message
                                return {
                                    "choices": [{
                                        "message": {
                                            "content": failed_gen,
                                            "role": "assistant"
                                        }
                                    }]
                                }
                        except:
                            pass
                    
                    print(f"[GROQ] Payload size: {len(str(messages_to_send))} chars, {len(str(tools))} chars in tools")
                print(f"[GROQ ERROR] {str(e)}")
                raise
            except Exception as e:
                print(f"[GROQ ERROR] {str(e)}")
                raise
        
        raise Exception(f"[GROQ ERROR] Max retries exceeded")
    
    def _validate_search_query(self, query: str) -> str:
        """Validate and enhance search query with required signal words/dates"""
        # Check if query has date or signal word
        signal_words = ['interview', 'news', 'said', 'announced', 'believes', 'latest', 'recent', '2025', '2026', 'april', 'march', 'february', 'january', 'december', 'november', 'october']
        has_signal = any(word.lower() in query.lower() for word in signal_words)
        
        # If no signal word or year, add 2026
        if not has_signal or ('2026' not in query and '2025' not in query):
            query = query + " 2026"
        
        print(f"  [QUERY VALIDATED] {query}")
        return query
    
    def _execute_tool(self, tool_name: str, arguments: Dict) -> str:
        """Execute a tool and return result as string"""
        try:
            if tool_name == "tavily_search":
                query = arguments.get("query", "")
                # Validate query has signal words and dates
                query = self._validate_search_query(query)
                print(f"  [SEARCH] {query}")
                self.search_count += 1
                results = self.search_tool.search(query, count=2)
                
                # Format results - compact to reduce payload
                formatted = []
                for r in results[:2]:
                    formatted.append({
                        "title": r.title[:70],
                        "url": r.url,
                        "snippet": r.description[:80]
                    })
                return json.dumps({"results": formatted}, separators=(',', ':'))
            
            elif tool_name == "jina_scrape":
                url = arguments.get("url", "")
                print(f"  [SCRAPE] {url}")
                self.scrape_count += 1
                
                scraped = self.scrape_tool.scrape(url, fallback_snippet="")
                
                if scraped and len(scraped.content) > 200:
                    # IDENTITY VERIFICATION: Check this is about the right person
                    person = getattr(self, 'current_person', None)
                    if person and not self.is_right_person(scraped.content, person.name, person.company):
                        print(f"  [IDENTITY REJECTED] Content at {url} doesn't match {person.name} + {person.company}")
                        return json.dumps({
                            "success": False,
                            "url": url,
                            "reason": "Content doesn't match identity (wrong person or company)"
                        }, separators=(',', ':'), ensure_ascii=True)
                    
                    self.scrape_success += 1
                    # Keep substantial content for synthesis (3000 chars = ~600 words)
                    content_capped = scraped.content[:3000]
                    print(f"[DEBUG SCRAPE] {url}: {len(scraped.content)} total chars, keeping {len(content_capped)}")
                    # Track this scraped content for synthesis
                    self.scraped_contents.append(scraped)
                    # Escape JSON but preserve structure (keep newlines for formatting)
                    content_safe = content_capped.replace('\\', '\\\\').replace('"', '\\"')
                    return json.dumps({
                        "success": True,
                        "url": url,
                        "content": content_safe
                    }, separators=(',', ':'), ensure_ascii=True)
                else:
                    print(f"[JINA FAILED] {url}: got {len(scraped.content) if scraped else 0} chars")
                    return json.dumps({
                        "success": False,
                        "url": url
                    }, separators=(',', ':'), ensure_ascii=True)
            
            elif tool_name == "save_briefing":
                import re
                content = arguments.get("content", "")
                name = arguments.get("name", "briefing")
                
                # Clean content to prevent issues
                # Remove problematic characters that might cause JSON issues
                content = content.replace('\r', '').replace('\t', ' ')
                # Normalize multiple newlines
                content = re.sub(r'\n\n+', '\n', content)
                
                # Normalize headers before saving
                normalized = content
                # Replace level 3 headers (###) with level 2 (##)
                normalized = re.sub(r'^### ', '## ', normalized, flags=re.MULTILINE)
                # Normalize abbreviated section names
                normalized = normalized.replace("## Who\n", "## Who They Are\n")
                normalized = normalized.replace("## What They Care\n", "## What They Care About\n")
                normalized = normalized.replace("## What\n", "## What They Care About\n")
                normalized = normalized.replace("## Company\n", "## Current Company Situation\n")  
                normalized = normalized.replace("## Approach\n", "## Meeting Approach\n")
                normalized = normalized.replace("## Questions\n", "## Smart Questions to Ask\n")
                normalized = normalized.replace("## Avoid\n", "## Things to Avoid\n")
                normalized = normalized.replace("## Icebreaker\n", "## Icebreaker / Common Ground\n")
                
                # Add title if missing
                if "# Executive Briefing:" not in normalized:
                    normalized = f"# Executive Briefing: {name}\n\n{normalized}"
                
                # NOTE: We will NOT save the file here. Instead, it will be saved in the research() method
                # after alerts are detected. This ensures alerts are included in the saved file.
                print(f"  [SAVE_BRIEFING_CALLED] Ready to save (alerts will be prepended before saving)")
                
                return json.dumps({
                    "success": True,
                    "filename": f"briefing_{name.replace(' ', '_').lower()}_{datetime.now().strftime('%Y-%m-%d')}.md",
                    "content": normalized  # Return the content so we can access it in research()
                })
            
            else:
                return json.dumps({"error": f"Unknown tool: {tool_name}"})
        
        except Exception as e:
            return json.dumps({"error": str(e)})
    
    def research(self, person: Person) -> Optional[Briefing]:
        """
        Main research loop using Groq tool calling.
        Groq decides what tools to call.
        """
        
        print("="*60)
        print(f"RESEARCHING: {person.name} ({person.role})")
        print("="*60 + "\n")
        
        # Store current person for identity verification in _execute_tool
        self.current_person = person
        
        # CRITICAL: Call find_digital_footprint FIRST to lock identity and pre-scrape sources
        print("[STEP 1] Locking identity and finding digital footprint...")
        footprint = self.find_digital_footprint(person)
        print(f"[FOOTPRINT COMPLETE] Locked handle: {footprint['handle']}, Personal site: {footprint.get('personal_site', 'N/A')}, Pre-scraped sources: {len(self.scraped_contents)}\n")
        
        final_briefing_content = ""  # Store briefing from save_briefing tool call
        
        # BUG FIX 2: Limit Groq API calls to prevent rate limiting (max 2 per research run)
        groq_call_count = 0
        max_groq_calls = 2
        
        # SYSTEM INSTRUCTIONS FOR GROQ (Phase 1: Search & Scrape)
        identity_lock_prompt = f"""IDENTITY LOCK: This briefing is ONLY about {person.name} who works at {person.company}.

If any scraped content mentions {person.name} in context of a DIFFERENT company or role, IGNORE that content completely.

CRITICAL - Prevent mixing data from same-named people:
- The correct person: {person.name} at {person.company}
- Verified LinkedIn handle: Will be provided
- Any content NOT matching these markers = WRONG PERSON = SKIP IT

Example rejections:
- If you see "{person.name}" + "PyTorch blogger" but they work at {person.company} for packaging = REJECT
- If you see "{person.name}" + "Diamond Challenge mentor" but they work at {person.company} = CHECK if it's the same company
- Only accept if BOTH name + company match scraped content"""

        system_message_research = f"""You are an Executive Briefing Specialist AI. Your task is to research a person and create an executive briefing.

{identity_lock_prompt}

REQUIREMENTS:
1. SEARCH STRATEGY - Use tavily_search with SPECIFIC queries to find the person:
   - First search: "{person.name} {person.company}" - find their professional profile
   - Second search: "{person.name} LinkedIn profile" - find more details
   - Only use results that ACTUALLY mention BOTH {person.name} AND {person.company} - ignore unrelated people
2. Use jina_scrape to read the best URLs found in search results (2-3 URLs maximum)
   - PRIORITY DOMAINS: linkedin.com, github.com, {person.company if person.company not in ['Unknown', 'N/A'] else 'company website'}
   - AVOID: Generic news sites, unrelated content
3. VERIFY IDENTITY: After scraping, check that content actually mentions {person.name} + {person.company} together
   - If content mentions {person.name} but NOT {person.company}, SKIP it (wrong person)
   - If content mentions another company for {person.name}, SKIP it (wrong person)
4. After gathering verified information, ALWAYS call save_briefing tool with the complete briefing
5. CRITICAL: Use ONLY the information from the tool results (scraped web content) in your briefing
6. Do NOT use training data - base EVERY fact on the scraped research provided
7. IMPORTANT: You MUST call save_briefing when ready - do NOT just generate text
8. CRITICAL: Every factual sentence must end with [Source: domain.com]
9. If you cannot find verified information for a section, write [TOO LITTLE DATA - RESEARCH FAILED]
10. NEVER mix data about different people - when in doubt, omit it"""
        
        # Start with research phase
        system_message = system_message_research
        
        # Define tools for Groq - OpenAI format
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "tavily_search",
                    "description": "Search the web for information about a person. Returns recent news, articles, and information.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query (name, company, keywords)"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "jina_scrape",
                    "description": "Read the full content of a webpage. Use after finding URLs in search results.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "The URL to scrape"
                            }
                        },
                        "required": ["url"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "save_briefing",
                    "description": "Save the completed executive briefing. Call this when you have gathered enough research.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "content": {
                                "type": "string",
                                "description": "The complete briefing markdown with all 8 sections"
                            },
                            "name": {
                                "type": "string",
                                "description": "Person's full name"
                            }
                        },
                        "required": ["content", "name"]
                    }
                }
            }
        ]
        
        # Initial system message
        initial_prompt = f"""Please research this person and create their executive briefing:

Name: {person.name}
Role: {person.role}
Company: {person.company}
Context: {person.context}

YOUR RESEARCH STRATEGY:
1. SEARCH CAREFULLY (call tavily_search 2 times with SPECIFIC queries):
   - Search 1: "{person.name} LinkedIn" - to find professional profile
   - Search 2: "{person.name} {person.company}" - to find company info
   - ONLY use results that ACTUALLY mention {person.name} - ignore generic articles

2. VERIFY SOURCES (call jina_scrape 2-3 times):
   - Check that scraped content ACTUALLY contains about {person.name}
   - Prefer: LinkedIn profiles, company websites, personal sites
   - Avoid: Generic news sites that don't mention this person

3. Create the briefing with these EXACT section headers:
   - # Executive Briefing: {person.name}
   - ## Who They Are
   - ## What They Care About
   - ## Current Company Situation
   - ## Meeting Approach
   - ## Smart Questions to Ask
   - ## Things to Avoid
   - ## Icebreaker / Common Ground

4. CRITICAL: Call save_briefing with complete content and name

QUALITY RULES:
- Only include facts you found in scraped content
- Every sentence must have [Source: domain.com]
- Don't use any training data about this person
- If not found in research, write [NOT FOUND]"""

        self.messages = [
            {"role": "user", "content": initial_prompt}
        ]
        
        # Agentic loop
        loop_count = 0
        max_loops = 3  # Reduced from 5 - fewer API calls = less rate limiting
        max_msg_history = 4  # Keep only most recent messages to minimize payload
        
        while loop_count < max_loops:
            # BUG FIX 2: Check Groq call counter before making API call
            groq_call_count += 1
            if groq_call_count > max_groq_calls:
                print(f"[GROQ LIMIT] Reached {max_groq_calls} calls, stopping loop")
                break
            
            loop_count += 1
            print(f"[LOOP {loop_count}] Calling Groq... (call {groq_call_count}/{max_groq_calls})")
            
            # Trim messages to prevent payload too large errors
            msgs_to_send = self.messages[-max_msg_history:] if len(self.messages) > max_msg_history else self.messages
            
            # Pass system message on EVERY call
            response = self._call_groq_with_tools(msgs_to_send, tools, system_message)
            
            # BUG FIX 2: Increase throttle between Groq calls to prevent rate limiting
            # Groq free tier: ~2 requests per second max, so 2 second delay is safer
            if loop_count < max_loops - 1:  # Don't delay on last potential loop
                print(f"[THROTTLE] Waiting 2 seconds before next Groq call...")
                time.sleep(2)
            
            message_content = response["choices"][0]["message"]
            
            # Store the full message for tool calls, but can truncate text later
            assistant_message = {
                "role": "assistant", 
                "content": message_content.get("content", "")
            }
            
            # Add tool_calls if present 
            if "tool_calls" in message_content:
                assistant_message["tool_calls"] = message_content["tool_calls"]
            
            self.messages.append(assistant_message)
            
            # Check for tool calls
            tool_calls = message_content.get("tool_calls", [])
            
            if not tool_calls:
                # No more tool calls - Groq generated briefing as text (not via save_briefing tool)
                print("\n[AGENT COMPLETE] Groq finished without calling save_briefing")
                print("[INFO] Using message content briefing (alternate generation mode)")
                
                # Extract final briefing from last message
                final_content = message_content.get("content", "")
                
                if final_content:
                    import re
                    # Normalize section headers if needed
                    normalized_content = final_content
                    
                    # Add main title if missing
                    if "# Executive Briefing:" not in normalized_content:
                        normalized_content = f"# Executive Briefing: {person.name}\n\n{normalized_content}"
                    
                    # Replace level 3 headers (###) with level 2 (##) for consistency
                    normalized_content = re.sub(r'^### ', '## ', normalized_content, flags=re.MULTILINE)
                    
                    # Normalize abbreviated section header names
                    normalized_content = normalized_content.replace("## Who\n", "## Who They Are\n")
                    normalized_content = normalized_content.replace("## What They Care\n", "## What They Care About\n")
                    normalized_content = normalized_content.replace("## What\n", "## What They Care About\n")
                    normalized_content = normalized_content.replace("## Company\n", "## Current Company Situation\n")  
                    normalized_content = normalized_content.replace("## Approach\n", "## Meeting Approach\n")
                    normalized_content = normalized_content.replace("## Questions\n", "## Smart Questions to Ask\n")
                    normalized_content = normalized_content.replace("## Avoid\n", "## Things to Avoid\n")
                    normalized_content = normalized_content.replace("## Icebreaker\n", "## Icebreaker / Common Ground\n")
                    
                    filename = f"briefing_{person.name.replace(' ', '_').lower()}_{datetime.now().strftime('%Y-%m-%d')}.md"
                    self.file_tool.save_briefing(filename, normalized_content, OUTPUT_DIR)
                    print(f"[SAVE] {filename}")
                    
                    final_content = normalized_content
                
                # Build briefing object with fallback content
                briefing = Briefing(
                    person=person,
                    who_they_are=final_content[:400],
                    what_they_care_about=final_content[400:900],
                    company_situation=final_content[900:1400],
                    meeting_approach=final_content[1400:1900],
                    smart_questions=["See full briefing"],
                    things_to_avoid=["See full briefing"],
                    icebreaker=final_content[1900:2100],
                    sources=[f"Research: {self.search_count} searches, {self.scrape_success} scrapes"],
                    timestamp=datetime.now().isoformat()
                )
                
                # CHANGE 5: Attach footprint data to briefing
                briefing.footprint = self.footprint
                
                # Detect critical alerts
                briefing.alerts = self.detect_alerts(self.scraped_contents, person.name)
                print(f"[ALERTS] Detected {len(briefing.alerts)} alerts in FALLBACK PATH")
                
                # Update markdown file to include alerts at the top
                if briefing.alerts:
                    print(f"[DEBUG] Has alerts, update file flag is True in FALLBACK PATH")
                    alerts_section = "## 🔔 Critical Meeting Intel\n> Read these before anything else\n\n"
                    for alert in briefing.alerts:
                        alerts_section += f"**{alert['emoji']} {alert['label']}**\n"
                        alerts_section += f"{alert['text']}\n"
                        alerts_section += f"[Source: {alert['source']}]({alert['url']})\n\n"
                    alerts_section += "---\n\n"
                    
                    # Prepend alerts to final markdown
                    markdown_with_alerts = alerts_section + final_content
                    filename = f"briefing_{person.name.replace(' ', '_').lower()}_{datetime.now().strftime('%Y-%m-%d')}.md"
                    self.file_tool.save_briefing(filename, markdown_with_alerts, OUTPUT_DIR)
                    print(f"[UPDATE] Markdown file updated with {len(briefing.alerts)} alerts - FALLBACK PATH")
                else:
                    print(f"[DEBUG] No alerts to update in FALLBACK PATH")
            
            # Execute tool calls
            print(f"[TOOLS] Executing {len(tool_calls)} tool calls...")
            tool_results = []
            
            for i, tool_call in enumerate(tool_calls):
                tool_name = tool_call["function"]["name"]
                arguments = json.loads(tool_call["function"]["arguments"])
                
                # CRITICAL FIX: Extract briefing content from save_briefing BEFORE executing
                if tool_name == "save_briefing":
                    final_briefing_content = arguments.get("content", "")
                
                print(f"  > {tool_name}")
                result = self._execute_tool(tool_name, arguments)
                
                tool_results.append({
                    "tool_call_id": tool_call["id"],
                    "tool_name": tool_name,
                    "result": result
                })
                
                # BUG FIX 2: Increase throttle between tool calls (1s -> 2s)
                if i < len(tool_calls) - 1 and tool_name != "save_briefing":
                    print(f"  [THROTTLE] Waiting 2 seconds before next tool call...")
                    time.sleep(2)
                
                # If save_briefing was called, stop the loop - research is complete
                if tool_name == "save_briefing":
                    print("\n[AGENT COMPLETE] Briefing saved successfully")
                    print(f"[STATS] Total: {self.search_count} searches, {self.scrape_count} scrapes, {self.scrape_success} successful\n")
                    
                    # Build briefing object with actual content
                    briefing = Briefing(
                        person=person,
                        who_they_are=final_briefing_content[:400],
                        what_they_care_about=final_briefing_content[400:900],
                        company_situation=final_briefing_content[900:1400],
                        meeting_approach=final_briefing_content[1400:1900],
                        smart_questions=final_briefing_content.split("## Smart Questions")[-1].split("##")[0].strip().split("\n") if "## Smart Questions" in final_briefing_content else ["See full briefing"],
                        things_to_avoid=final_briefing_content.split("## Things to Avoid")[-1].split("##")[0].strip().split("\n") if "## Things to Avoid" in final_briefing_content else ["See full briefing"],
                        icebreaker=final_briefing_content[1900:2100],
                        sources=[f"Research: {self.search_count} searches, {self.scrape_success} scrapes"],
                        timestamp=datetime.now().isoformat()
                    )
                    
                    # CHANGE 5: Attach footprint data to briefing
                    briefing.footprint = self.footprint
                    
                    # Detect critical alerts
                    briefing.alerts = self.detect_alerts(self.scraped_contents, person.name)
                    
                    with open('debug.log', 'w', encoding='utf-8') as f:
                        f.write(f"Detected {len(briefing.alerts)} alerts\n")
                        f.write(f"final_briefing_content length: {len(final_briefing_content)}\n")
                        f.write(f"final_briefing_content preview: {final_briefing_content[:100]}\n")
                        if briefing.alerts:
                            f.write("HAS ALERTS - will prepend\n")
                        else:
                            f.write("NO ALERTS\n")
                    
                    # Update markdown file to include alerts at the top
                    if briefing.alerts:
                        alerts_section = "## 🔔 Critical Meeting Intel\n> Read these before anything else\n\n"
                        for alert in briefing.alerts:
                            alerts_section += f"**{alert['emoji']} {alert['label']}**\n"
                            alerts_section += f"{alert['text']}\n"
                            alerts_section += f"[Source: {alert['source']}]({alert['url']})\n\n"
                        alerts_section += "---\n\n"
                        
                        # Prepend alerts to final markdown
                        markdown_with_alerts = alerts_section + final_briefing_content
                        
                        filename = f"briefing_{person.name.replace(' ', '_').lower()}_{datetime.now().strftime('%Y-%m-%d')}.md"
                        print(f"[SAVING WITH ALERTS] {filename}")
                        self.file_tool.save_briefing(filename, markdown_with_alerts, OUTPUT_DIR)
                        
                        with open('debug.log', 'a', encoding='utf-8') as f:
                            f.write(f"SAVED FILE WITH {len(briefing.alerts)} ALERTS\n")
                    else:
                        with open('debug.log', 'a', encoding='utf-8') as f:
                            f.write("NO ALERTS - no file update\n")
                    
                    return briefing
            
            # Add tool results to messages - preserve ALL content for synthesis
            total_scrape_chars = 0
            for tool_result in tool_results:
                result_content = tool_result["result"]
                total_scrape_chars += len(result_content)
                # IMPORTANT: Keep results intact - Groq needs full content to synthesize from research
                # NOT truncating (was truncating to 400 chars - that was the bug!)
                print(f"[DEBUG MESSAGE] Adding {tool_result['tool_name']}: {len(result_content)} chars to messages")
                
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tool_result["tool_call_id"],
                    "content": result_content
                })
            
            # Build scraped_text from all collected scrapes for synthesis visibility
            # LIMIT: 600 chars per source to keep total request size within Groq limits
            scraped_text = "\n\n".join([
                f"SOURCE: {s.url}\nCONTENT: {s.content[:600]}"
                for s in self.scraped_contents
                if s.content and len(s.content) > 100
            ])
            
            # CHANGE 2: Add personal site context before scraped content (LIMIT TO 500 chars)
            personal_site_context = ""
            if self.footprint:
                fp = self.footprint
                if fp.get('photo_url'):
                    personal_site_context += f"PHOTO: {fp['photo_url']}\n"
                # LIMIT: Truncate bio to 500 chars to avoid payload bloat
                if fp.get('bio'):
                    bio_text = fp['bio'][:500]
                    personal_site_context += f"PERSONAL BIO: {bio_text}\n"
                if fp.get('email'):
                    personal_site_context += f"EMAIL: {fp['email']}\n"
                if fp.get('github'):
                    personal_site_context += f"GITHUB: {fp['github']}\n"
                if fp.get('twitter'):
                    personal_site_context += f"TWITTER: {fp['twitter']}\n"
            
            if personal_site_context:
                scraped_text = personal_site_context + "\n" + scraped_text
            
            # SAFETY: Cap total scraped_text to 3500 chars to stay within Groq payload limits
            if len(scraped_text) > 3500:
                scraped_text = scraped_text[:3500] + "\n[... research data truncated for API limits ...]"
            
            print(f"[DEBUG SYNTHESIS] {len(self.scraped_contents)} sources, {len(scraped_text)} total chars collected")
            if len(scraped_text) < 500:
                print("[WARNING] Very little research content - briefing may be low quality")
            print(f"[DEBUG TOTAL CONTENT] {total_scrape_chars} chars of research now in messages sent to Groq")
            
            # Generate synthesis_prompt with source citation enforcement
            synthesis_prompt = f"""You are writing an executive briefing for a meeting with {person.name}.

SCRAPED RESEARCH (use ONLY this, nothing else):
{scraped_text}

STRICT RULE: Never copy-paste any text from the scraped content. You are an analyst, not a transcriber.

Read the scraped content, extract meaning, then write in clean professional sentences.

NEVER include in your output:
- CAPTCHA warnings
- 'See new posts' or UI navigation text
- Raw URLs embedded in sentences
- Markdown link syntax like [text](url)
- Warning messages from websites
- Cookie notices or login prompts
- Any text that looks like website UI

If scraped content contains mostly navigation/UI text and less than 3 real facts about the person, write [NOT FOUND] for that section instead of using the UI text as content.

RULES — CRITICAL:
- Every single factual sentence ends with [Source: domain.com]
- Extract the domain from the SOURCE: URL in the research above
- If you cannot find a fact in the research above, write [NOT FOUND]
- Never write a sentence without a source tag
- Numbers, dates, names of products must all have source tags

WRITE THE BRIEFING IN THIS EXACT FORMAT:

# Executive Briefing: {person.name}
**Role:** {person.role} | **Company:** {person.company}
**Meeting Context:** {person.context}
**Generated:** {datetime.now().strftime('%B %d, %Y')}

---

## Research Confidence
- Sources scraped: {len(self.scraped_contents)}
- Total chars analyzed: {len(scraped_text)}
- Confidence: {"HIGH" if len(self.scraped_contents) >= 3 else "MEDIUM" if len(self.scraped_contents) >= 1 else "LOW"}

---

## Who They Are
Write 3 sentences about {person.name} as a real human.
Use their actual bio from the scraped content.
Reference their age, background, what drives them personally.
Example of good output:
"Ishan Kumar is a 20-year-old CS undergrad at Chitkara 
University who founded InTheBox in April 2025. He describes 
himself as someone who loves building businesses and solving 
problems, and when he is not studying, he is locking down 
new clients for InTheBox. He recently won ₹1.25L at TiE U, 
signaling early validation for his packaging startup."
[Source: ishankumax.me]

## What They Care About Right Now  
Write 4 bullet points. Each must be a full sentence with 
a specific fact from research. No vague statements.
Bad: "Cares about packaging innovation"
Good: "Building custom premium packaging for brands — 
InTheBox's tagline is 'Where Packaging Meets Innovation' 
and they focus on the unboxing moment specifically [Source: ishankumax.me]"

## Current Company Situation
Write a real paragraph about the company with numbers.
Use every stat you found: clients, orders, satisfaction score,
revenue milestones, awards, founding date.
Bad: "InTheBox is a packaging company"
Good: "InTheBox, founded in April 2025, has already served 
500+ brands and delivered 50K+ orders with a 98% satisfaction 
rate. [Source: inthebox.co.in] The company positions itself as a 
premium packaging studio — design-led and experience-driven, 
helping brands stand out through the unboxing moment."

## How To Approach This Meeting
3 specific tactical points directly tied to the meeting 
context: {person.context}
Each point must reference something specific from research.

## Three Smart Questions
Each question must reference a specific fact you found.
Bad: "What are your plans for growth?"
Good: "You've hit 500+ brands in under a year — 
what's the bottleneck stopping you from 10x-ing that? [Source: inthebox.co.in]"

## Two Things To Avoid
Based only on specific signals from research.
Not generic advice.

## Icebreaker
One specific, genuine thing. Quote something real.
Example: "I saw on your site that you won ₹1.25L at 
TiE U — what was the pitch about and how did InTheBox 
come from that? [Source: ishankumax.me]"
This must be something you actually found, not invented.

ABSOLUTE RULES:
- Every section minimum 3 sentences or 3 bullet points
- Every claim has [Source: domain] after it  
- Never split a sentence across two sections
- If you start writing a word, finish it before any heading
- Zero generic phrases: no "strong background", no "passionate about",
  no "industry leader", no "innovative solutions" without specifics
- Use their actual words when possible — quote them

## Sources
[List every URL that had content, one per line]
"""
            
            # Update system message to include synthesis instructions
            system_message = synthesis_prompt
            
            print(f"[STATS] Searches: {self.search_count}, Scrapes: {self.scrape_count}, Successful: {self.scrape_success}\n")
        
        print("[ERROR] Max loop count exceeded")
        return None


def main():
    """Entry point - use Groq-based research with identity locking"""
    if len(sys.argv) < 3:
        print("Usage: python -m phase1_agent.main <name> <role> [company] [context]")
        print("Example: python -m phase1_agent.main 'Ishan Kumar' 'CEO' 'InTheBox' 'meeting for intern hiring'")
        sys.exit(1)
    
    name = sys.argv[1]
    role = sys.argv[2]
    company = sys.argv[3] if len(sys.argv) > 3 else "Unknown"
    context = sys.argv[4] if len(sys.argv) > 4 else "General business meeting"
    
    person = Person(name=name, role=role, company=company, context=context)
    
    # Use Groq-based research with identity locking via IntelAgent
    agent = IntelAgent()
    briefing = agent.research(person)
    
    if briefing:
        print("\n" + "="*60)
        print("[SUCCESS] RESEARCH COMPLETE")
        print("="*60)
        print(briefing.to_markdown()[:1000])
    else:
        print("\n[ERROR] Research failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
