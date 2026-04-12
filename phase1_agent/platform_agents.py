#!/usr/bin/env python3
"""
Platform-Specific Research Agents
Each agent specializes in extracting deep insights from a specific platform
"""

import json
import requests
from typing import List, Dict, Optional
from phase1_agent.config import TAVILY_API_KEY, TAVILY_SEARCH_URL
from phase1_agent.models import ScrapedContent
from datetime import datetime


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
        """Extract structured data from LinkedIn profile"""
        return {
            "current_role": extract_section(scraped_content, "experience", person_name),
            "bio": extract_section(scraped_content, "about", person_name),
            "skills": extract_section(scraped_content, "skills", person_name),
            "education": extract_section(scraped_content, "education", person_name),
            "recommendations": extract_section(scraped_content, "recommendation", person_name),
            "endorsements": extract_section(scraped_content, "endorse", person_name),
        }


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
        """Extract data from personal site"""
        return {
            "intro": extract_section(scraped_content, "about|hello|welcome|bio", person_name=""),
            "projects": extract_section(scraped_content, "project|portfolio|work", person_name=""),
            "skills_tech": extract_section(scraped_content, "tech|stack|skills", person_name=""),
            "social_links": extract_social_links(scraped_content),
            "contact_info": extract_section(scraped_content, "contact|email|connect", person_name=""),
        }


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
        """Extract insights from Twitter profile and recent tweets"""
        return {
            "bio": extract_section(scraped_content, "bio|about", person_name=""),
            "interests": extract_section(scraped_content, "focus|interested|working on", person_name=""),
            "recent_thoughts": extract_section(scraped_content, "tweet|post|think|believe", person_name=""),
            "engagement_style": extract_section(scraped_content, "quote|reply|retweet", person_name=""),
        }


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
        """Extract company insights"""
        return {
            "mission": extract_section(scraped_content, "mission|purpose|goal", person_name=""),
            "team": extract_section(scraped_content, "team|founder|leader|member", person_name=""),
            "products": extract_section(scraped_content, "product|service|offer|build", person_name=""),
            "funding": extract_section(scraped_content, "funding|raise|invest|series", person_name=""),
            "recent_news": extract_section(scraped_content, "announce|launch|release|news", person_name=""),
        }


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
        """Extract GitHub profile insights"""
        return {
            "bio": extract_section(scraped_content, "bio|about", person_name=""),
            "languages": extract_section(scraped_content, "javascript|python|go|rust|java", person_name=""),
            "popular_repos": extract_section(scraped_content, "repository|repo|project", person_name=""),
            "contributions": extract_section(scraped_content, "contribution|commit|open source", person_name=""),
        }


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
