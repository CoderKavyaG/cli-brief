#!/usr/bin/env python3
"""
Platform Research Coordinator
Orchestrates multiple specialized agents to research a person deeply
"""

import json
from typing import Dict, List, Optional
from phase1_agent.models import Person, Briefing, ScrapedContent
from phase1_agent.tools import JinaScrape, FileSave
from phase1_agent.platform_agents import (
    LinkedInAgent, PersonalSiteAgent, TwitterAgent, CompanyAgent, GitHubAgent
)
from datetime import datetime


class PlatformCoordinator:
    """Master orchestrator for multi-platform research"""
    
    def __init__(self):
        self.scraper = JinaScrape()
        self.file_tool = FileSave()
        self.platforms_researched = {}
        self.all_sources = []
    
    def research_person_deep(self, person: Person) -> Dict:
        """
        Execute deep research across all available platforms
        Returns comprehensive research data without synthesis (raw findings)
        """
        
        print("\n" + "="*70)
        print(f"[DEEP RESEARCH] {person.name} - Multi-Platform Research")
        print("="*70 + "\n")
        
        results = {
            "person": person.name,
            "role": person.role,
            "company": person.company,
            "timestamp": datetime.now().isoformat(),
            "platforms": {}
        }
        
        # Platform 1: LinkedIn
        print("[1/5] RESEARCHING LINKEDIN...")
        linkedin_results = self._research_linkedin(person)
        results["platforms"]["linkedin"] = linkedin_results
        print(f"[OK] LinkedIn: {len(linkedin_results.get('urls', []))} profiles found\n")
        
        # Platform 2: Personal Site
        print("[2/5] RESEARCHING PERSONAL SITE...")
        personal_results = self._research_personal_site(person)
        results["platforms"]["personal_site"] = personal_results
        print(f"[OK] Personal Site: {len(personal_results.get('urls', []))} sites found\n")
        
        # Platform 3: Twitter/X
        print("[3/5] RESEARCHING TWITTER/X...")
        twitter_results = self._research_twitter(person)
        results["platforms"]["twitter"] = twitter_results
        print(f"[OK] Twitter: {len(twitter_results.get('urls', []))} profiles found\n")
        
        # Platform 4: GitHub
        print("[4/5] RESEARCHING GITHUB...")
        github_results = self._research_github(person)
        results["platforms"]["github"] = github_results
        print(f"[OK] GitHub: {len(github_results.get('urls', []))} profiles found\n")
        
        # Platform 5: Company
        print("[5/5] RESEARCHING COMPANY...")
        company_results = self._research_company(person)
        results["platforms"]["company"] = company_results
        print(f"[OK] Company: {len(company_results.get('urls', []))} pages found\n")
        
        return results
    
    def _research_linkedin(self, person: Person) -> Dict:
        """Research LinkedIn profile"""
        print(f"  Searching for LinkedIn profile: {person.name}")
        urls = LinkedInAgent.search_profile(person.name)
        
        research = {
            "urls": urls,
            "scraped_content": []
        }
        
        for url_data in urls[:1]:  # Limit to top 1 to reduce API calls
            print(f"  -> Scraping: {url_data['url'][:50]}...")
            content = self.scraper.scrape(url_data['url'])
            
            if content and len(content.content) > 100:
                extracted = LinkedInAgent.extract_profile_data(content.content, person.name)
                research["scraped_content"].append({
                    "url": content.url,
                    "extracted": extracted,
                    "raw_length": len(content.content)
                })
                print(f"     [OK] Extracted: {list(extracted.keys())}")
        
        return research
    
    def _research_personal_site(self, person: Person) -> Dict:
        """Research personal website/portfolio"""
        print(f"  Searching for personal site: {person.name}")
        urls = PersonalSiteAgent.search_personal_site(person.name)
        
        research = {
            "urls": urls,
            "scraped_content": []
        }
        
        for url_data in urls[:1]:  # Limit to top 1 to reduce API calls
            print(f"  -> Scraping: {url_data['url'][:50]}...")
            content = self.scraper.scrape(url_data['url'])
            
            if content and len(content.content) > 100:
                extracted = PersonalSiteAgent.extract_personal_data(content.content)
                research["scraped_content"].append({
                    "url": content.url,
                    "extracted": extracted,
                    "raw_length": len(content.content)
                })
                print(f"     [OK] Extracted: {list(extracted.keys())}")
                
                # Check for social links
                if extracted.get("social_links"):
                    print(f"     [OK] Found social links: {list(extracted['social_links'].keys())}")
        
        return research
    
    def _research_twitter(self, person: Person) -> Dict:
        """Research Twitter/X profile"""
        print(f"  Searching for Twitter profile: {person.name}")
        urls = TwitterAgent.search_twitter(person.name)
        
        research = {
            "urls": urls,
            "scraped_content": []
        }
        
        for url_data in urls[:1]:  # Limit to top 1 to reduce API calls
            if "twitter" in url_data['url'].lower() or "x.com" in url_data['url'].lower():
                print(f"  -> Scraping: {url_data['url'][:50]}...")
                content = self.scraper.scrape(url_data['url'])
                
                if content and len(content.content) > 100:
                    extracted = TwitterAgent.extract_twitter_data(content.content)
                    research["scraped_content"].append({
                        "url": content.url,
                        "extracted": extracted,
                        "raw_length": len(content.content)
                    })
                    print(f"     [OK] Extracted: {list(extracted.keys())}")
        
        return research
    
    def _research_github(self, person: Person) -> Dict:
        """Research GitHub profile"""
        print(f"  Searching for GitHub profile: {person.name}")
        urls = GitHubAgent.search_github(person.name)
        
        research = {
            "urls": urls,
            "scraped_content": []
        }
        
        for url_data in urls[:1]:  # Limit to top 1 to reduce API calls
            print(f"  -> Scraping: {url_data['url'][:50]}...")
            content = self.scraper.scrape(url_data['url'])
            
            if content and len(content.content) > 100:
                extracted = GitHubAgent.extract_github_data(content.content)
                research["scraped_content"].append({
                    "url": content.url,
                    "extracted": extracted,
                    "raw_length": len(content.content)
                })
                print(f"     [OK] Extracted: {list(extracted.keys())}")
        
        return research
    
    def _research_company(self, person: Person) -> Dict:
        """Research company"""
        print(f"  Searching for company: {person.company}")
        urls = CompanyAgent.search_company(person.company)
        
        research = {
            "urls": urls,
            "scraped_content": []
        }
        
        for url_data in urls[:1]:  # Limit to top 1 to reduce API calls
            print(f"  -> Scraping: {url_data['url'][:50]}...")
            content = self.scraper.scrape(url_data['url'])
            
            if content and len(content.content) > 100:
                extracted = CompanyAgent.extract_company_data(content.content)
                research["scraped_content"].append({
                    "url": content.url,
                    "extracted": extracted,
                    "raw_length": len(content.content)
                })
                print(f"     [OK] Extracted: {list(extracted.keys())}")
        
        return research
    
    def generate_audit_report(self, research: Dict) -> str:
        """
        Generate readable audit report from multi-platform research
        Shows what data was found on each platform
        """
        report = f"""
================================================================================
                   MULTI-PLATFORM RESEARCH AUDIT REPORT
================================================================================

PERSON: {research['person']}
ROLE: {research['role']} | COMPANY: {research['company']}
GENERATED: {research['timestamp']}

================================================================================

PLATFORM RESEARCH SUMMARY:

"""
        
        for platform_name, platform_data in research['platforms'].items():
            platform_display = platform_name.replace('_', ' ').title()
            urls_found = len(platform_data.get('urls', []))
            scraped = len(platform_data.get('scraped_content', []))
            
            report += f"\n[{platform_display.upper()}]\n"
            report += f"  URLs Found: {urls_found}\n"
            report += f"  Successfully Scraped: {scraped}\n"
            
            if platform_data.get('urls'):
                report += f"  Top URLs:\n"
                for url_data in platform_data['urls'][:2]:
                    report += f"    - {url_data['url'][:60]}...\n"
            
            if platform_data.get('scraped_content'):
                report += f"  Extracted Data Fields:\n"
                for scraped_item in platform_data['scraped_content']:
                    fields = scraped_item['extracted'].keys()
                    report += f"    From: {scraped_item['url'][:50]}...\n"
                    for field in fields:
                        status = "[OK]" if scraped_item['extracted'][field] != "[NOT FOUND]" else "[X]"
                        report += f"      {status} {field}\n"
            else:
                report += f"  [WARNING] No content scraped\n"
        
        report += f"\n{'='*80}\n"
        report += f"\n[SUCCESS] AUDIT COMPLETE: {sum(len(p.get('scraped_content', [])) for p in research['platforms'].values())} pages scraped across {len(research['platforms'])} platforms\n"
        
        return report


def run_deep_research(name: str, role: str, company: str, context: str):
    """Execute multi-platform research and generate audit"""
    person = Person(name=name, role=role, company=company, context=context)
    coordinator = PlatformCoordinator()
    
    # Execute research
    research_data = coordinator.research_person_deep(person)
    
    # Generate audit report
    audit_report = coordinator.generate_audit_report(research_data)
    print(audit_report)
    
    return research_data, audit_report


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python coordinator.py <name> <role> [company] [context]")
        sys.exit(1)
    
    name = sys.argv[1]
    role = sys.argv[2]
    company = sys.argv[3] if len(sys.argv) > 3 else "Unknown"
    context = sys.argv[4] if len(sys.argv) > 4 else "General research"
    
    run_deep_research(name, role, company, context)


