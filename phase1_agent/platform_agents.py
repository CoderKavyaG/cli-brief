#!/usr/bin/env python3
"""
Platform-Specific Research Agents
Each agent specializes in extracting deep insights from a specific platform
"""

import json
import requests
from typing import List, Dict, Optional
from phase1_agent.config import TAVILY_API_KEY, TAVILY_SEARCH_URL, GROQ_API_KEY, GROQ_API_URL, GROQ_MODEL
from phase1_agent.models import ScrapedContent
from datetime import datetime


def extract_with_groq(html_content: str, platform: str, person_name: str = "") -> Dict:
    """
    Extract structured data from HTML using Groq AI.
    More reliable than keyword matching on large HTML files.
    Handles rate limiting with backoff and large payloads gracefully.
    """
    import time
    from html.parser import HTMLParser
    
    # Strip HTML tags to get readable text
    class HTMLToText(HTMLParser):
        def __init__(self):
            super().__init__()
            self.text = []
        def handle_data(self, data):
            self.text.append(data)
        def get_text(self):
            return ' '.join(self.text)
    
    parser = HTMLToText()
    try:
        # Limit content to first 30KB to avoid 413 payload errors
        parser.feed(html_content[:30000])
        cleaned_text = parser.get_text()
    except:
        # Fallback: raw HTML, truncated
        cleaned_text = html_content[:30000]
    
    # Define extraction fields per platform
    extraction_fields = {
        "linkedin": ["current_role", "bio", "skills", "education", "recommendations"],
        "twitter": ["bio", "followers", "website", "recent_posts"],
        "github": ["bio", "languages", "popular_repos", "contributions"],
        "personal_site": ["bio", "role", "projects", "skills"],
        "company": ["company_name", "description", "industry", "size"]
    }
    
    fields = extraction_fields.get(platform, ["bio", "role", "skills"])
    
    extraction_prompt = f"""Extract structured information from the following web page content.
Platform: {platform}
Person/Entity: {person_name}

CONTENT:
{cleaned_text[:25000]}

Extract the following fields ONLY if they are clearly present in the content.
Return ONLY valid JSON with no extra text. If a field is not found, use null.

{{
  "current_role": "Their current position/job title (if clearly stated)",
  "bio": "Brief professional biography or about section",
  "skills": "Technical or professional skills mentioned",
  "education": "Educational background",
  "projects": "Notable projects or work",
  "website": "Any website, portfolio, or social media links found",
  "company_name": "Company or organization name",
  "description": "Description of the company or person",
  "followers": "Number of followers or connections if mentioned",
  "recent_posts": "Summary of recent activity or posts",
  "languages": "Programming languages used (for GitHub)",
  "industry": "Industry or field",
  "recommendations": "Recommendations or endorsements",
  "endorsements": "Skill endorsements"
}}

EXTRACTION RULES:
- Extract ONLY factual information actually visible in the content
- Do NOT make up or assume information
- If a field is not clearly visible, return null
- Be specific and concise
- Do NOT include generic template text"""

    max_retries = 3
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            response = requests.post(
                GROQ_API_URL,
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": GROQ_MODEL,
                    "messages": [
                        {
                            "role": "user",
                            "content": extraction_prompt
                        }
                    ],
                    "temperature": 0,  # Zero temp for consistency
                    "max_tokens": 1000  # Reduced token limit
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result['choices'][0]['message']['content']
                
                # Extract JSON from response
                try:
                    # Try to parse as JSON directly
                    extracted = json.loads(response_text)
                except:
                    # If response has extra text, try to find JSON block
                    import re
                    json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                    if json_match:
                        extracted = json.loads(json_match.group())
                    else:
                        extracted = {}  # Return empty dict if parsing fails
                
                # Convert None values to "[NOT FOUND]" for consistency
                for key in extracted:
                    if extracted[key] is None or extracted[key] == "":
                        extracted[key] = "[NOT FOUND]"
                
                return extracted
                
            elif response.status_code == 429:
                # Rate limit - retry with exponential backoff
                if attempt < max_retries - 1:
                    delay = retry_delay * (2 ** attempt)  # Exponential backoff
                    print(f"[RATE LIMIT] Retrying in {delay}s (attempt {attempt + 1}/{max_retries})...")
                    time.sleep(delay)
                    continue
                else:
                    print(f"[RATE LIMIT EXCEEDED] Max retries exceeded")
                    return {}
                    
            elif response.status_code == 413:
                # Payload too large - reduce content more aggressively
                print(f"[PAYLOAD TOO LARGE] Skipping extraction")
                return {}
                
            else:
                print(f"[GROQ EXTRACTION ERROR] Status {response.status_code}: {response.text[:100]}")
                return {}
                
        except requests.Timeout:
            if attempt < max_retries - 1:
                print(f"[TIMEOUT] Retrying... (attempt {attempt + 1}/{max_retries})")
                time.sleep(retry_delay)
                continue
            else:
                print(f"[TIMEOUT EXCEEDED] Max retries exceeded")
                return {}
                
        except Exception as e:
            print(f"[EXTRACTION ERROR] {str(e)[:100]}")
            return {}
    
    return {}


class LinkedInAgent:
    """Specialized agent for LinkedIn profile research"""
    
    @staticmethod
    def search_profile(person_name: str) -> List[Dict]:
        """Search for LinkedIn profile specifically"""
        queries = [
            f"{person_name} LinkedIn profile",
            f"LinkedIn in/{person_name.lower().replace(' ', '-')}",
            f"site:linkedin.com {person_name}",
        ]
        
        all_results = []
        for query in queries:
            payload = {
                "api_key": TAVILY_API_KEY,
                "query": query,
                "max_results": 5,
                "include_answer": True
            }
            
            try:
                print(f"  [LINKEDIN SEARCH] {query}")
                response = requests.post(TAVILY_SEARCH_URL, json=payload, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                if "results" in data:
                    for item in data["results"]:
                        if "linkedin.com" in item.get("url", "").lower():
                            all_results.append({
                                "title": item.get("title", ""),
                                "url": item.get("url", ""),
                                "snippet": item.get("content", ""),
                                "platform": "LinkedIn"
                            })
            except Exception as e:
                print(f"  [LINKEDIN ERROR] {str(e)}")
                continue
        
        return all_results
    
    @staticmethod
    def extract_profile_data(scraped_content: str, person_name: str) -> Dict:
        """Extract structured data from LinkedIn profile using Groq"""
        return extract_with_groq(scraped_content, "linkedin", person_name)


class PersonalSiteAgent:
    """Specialized agent for personal website/portfolio research"""
    
    @staticmethod
    def search_personal_site(person_name: str, known_domain: str = None) -> List[Dict]:
        """Search for personal website"""
        queries = [
            f"{person_name} portfolio site",
            f"{person_name}.me OR {person_name}.com OR {person_name}.dev website",
        ]
        
        if known_domain:
            queries.insert(0, f"site:{known_domain}")
        
        all_results = []
        for query in queries:
            payload = {
                "api_key": TAVILY_API_KEY,
                "query": query,
                "max_results": 5,
                "include_answer": True
            }
            
            try:
                print(f"  [PERSONAL SITE SEARCH] {query}")
                response = requests.post(TAVILY_SEARCH_URL, json=payload, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                if "results" in data:
                    for item in data["results"]:
                        # Filter for personal domains (not LinkedIn, Twitter, etc.)
                        url = item.get("url", "").lower()
                        if not any(domain in url for domain in ["linkedin", "twitter", "github.com", "facebook"]):
                            all_results.append({
                                "title": item.get("title", ""),
                                "url": item.get("url", ""),
                                "snippet": item.get("content", ""),
                                "platform": "Personal Site"
                            })
            except Exception as e:
                print(f"  [PERSONAL SITE ERROR] {str(e)}")
                continue
        
        return all_results
    
    @staticmethod
    def extract_personal_data(scraped_content: str) -> Dict:
        """Extract data from personal site using Groq"""
        return extract_with_groq(scraped_content, "personal_site", "")


class TwitterAgent:
    """Specialized agent for Twitter/X research"""
    
    @staticmethod
    def search_twitter(person_name: str, twitter_handle: str = None) -> List[Dict]:
        """Search for Twitter profile and tweets"""
        queries = [
            f"site:twitter.com {person_name}" if not twitter_handle else f"site:twitter.com @{twitter_handle}",
            f"{person_name} tweets latest thoughts",
            f"@{twitter_handle} recent" if twitter_handle else None,
        ]
        
        all_results = []
        for query in [q for q in queries if q]:
            payload = {
                "api_key": TAVILY_API_KEY,
                "query": query,
                "max_results": 5,
                "include_answer": True
            }
            
            try:
                print(f"  [TWITTER SEARCH] {query}")
                response = requests.post(TAVILY_SEARCH_URL, json=payload, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                if "results" in data:
                    for item in data["results"]:
                        if "twitter.com" in item.get("url", "").lower() or "x.com" in item.get("url", "").lower():
                            all_results.append({
                                "title": item.get("title", ""),
                                "url": item.get("url", ""),
                                "snippet": item.get("content", ""),
                                "platform": "Twitter/X"
                            })
            except Exception as e:
                print(f"  [TWITTER ERROR] {str(e)}")
                continue
        
        return all_results
    
    @staticmethod
    def extract_twitter_data(scraped_content: str) -> Dict:
        """Extract insights from Twitter profile and recent tweets using Groq"""
        return extract_with_groq(scraped_content, "twitter", "")


class CompanyAgent:
    """Specialized agent for company research"""
    
    @staticmethod
    def search_company(company_name: str, company_website: str = None) -> List[Dict]:
        """Search for company information"""
        queries = [
            f"{company_name} official website team",
            f"site:{company_website}" if company_website else None,
            f"{company_name} about mission vision",
        ]
        
        all_results = []
        for query in [q for q in queries if q]:
            payload = {
                "api_key": TAVILY_API_KEY,
                "query": query,
                "max_results": 5,
                "include_answer": True
            }
            
            try:
                print(f"  [COMPANY SEARCH] {query}")
                response = requests.post(TAVILY_SEARCH_URL, json=payload, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                if "results" in data:
                    all_results.extend([
                        {
                            "title": item.get("title", ""),
                            "url": item.get("url", ""),
                            "snippet": item.get("content", ""),
                            "platform": "Company"
                        }
                        for item in data["results"]
                    ])
            except Exception as e:
                print(f"  [COMPANY ERROR] {str(e)}")
                continue
        
        return all_results
    
    @staticmethod
    def extract_company_data(scraped_content: str) -> Dict:
        """Extract company insights using Groq"""
        return extract_with_groq(scraped_content, "company", "")


class GitHubAgent:
    """Specialized agent for GitHub profile research"""
    
    @staticmethod
    def search_github(person_name: str, github_handle: str = None) -> List[Dict]:
        """Search for GitHub profile"""
        queries = [
            f"site:github.com {person_name}" if not github_handle else f"site:github.com/{github_handle}",
            f"GitHub {person_name} open source",
        ]
        
        all_results = []
        for query in queries:
            payload = {
                "api_key": TAVILY_API_KEY,
                "query": query,
                "max_results": 5,
                "include_answer": True
            }
            
            try:
                print(f"  [GITHUB SEARCH] {query}")
                response = requests.post(TAVILY_SEARCH_URL, json=payload, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                if "results" in data:
                    for item in data["results"]:
                        if "github.com" in item.get("url", "").lower():
                            all_results.append({
                                "title": item.get("title", ""),
                                "url": item.get("url", ""),
                                "snippet": item.get("content", ""),
                                "platform": "GitHub"
                            })
            except Exception as e:
                print(f"  [GITHUB ERROR] {str(e)}")
                continue
        
        return all_results
    
    @staticmethod
    def extract_github_data(scraped_content: str) -> Dict:
        """Extract GitHub profile insights using Groq"""
        return extract_with_groq(scraped_content, "github", "")


def extract_section(content: str, keywords: str, person_name: str = "") -> str:
    """Extract relevant sections from content based on keywords"""
    if not content:
        return "[NOT FOUND]"
    
    keyword_list = keywords.split("|")
    lines = content.split("\n")
    relevant_lines = []
    
    for i, line in enumerate(lines):
        line_lower = line.lower()
        # Check if line contains keywords
        if any(kw in line_lower for kw in keyword_list):
            # Include surrounding context
            start = max(0, i - 1)
            end = min(len(lines), i + 3)
            relevant_lines.extend(lines[start:end])
    
    result = "\n".join(relevant_lines[:500])  # Limit to 500 chars
    return result if result.strip() else "[NOT FOUND]"


def extract_social_links(content: str) -> List[str]:
    """Extract social media links from content"""
    import re
    
    social_patterns = {
        "twitter": r"twitter\.com/[\w]+|x\.com/[\w]+",
        "github": r"github\.com/[\w-]+",
        "linkedin": r"linkedin\.com/in/[\w-]+",
        "instagram": r"instagram\.com/[\w.]+",
        "youtube": r"youtube\.com/@?[\w-]+",
        "portfolio": r"https?://[a-zA-Z0-9.-]+\.(me|dev|com|io)(?!/twitter|/github|/linkedin)"
    }
    
    links = {}
    for platform, pattern in social_patterns.items():
        match = re.search(pattern, content)
        if match:
            links[platform] = match.group(0)
    
    return links
