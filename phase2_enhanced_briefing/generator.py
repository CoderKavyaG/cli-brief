"""
Phase 2: Enhanced Briefing Generator
Extended research with deep profile scraping from LinkedIn, Twitter, personal websites
Generates actionable meeting prep with detailed context

IMPROVEMENTS:
- Validator-based disambiguation to find CORRECT person (not just any match)
- Social handle extraction (LinkedIn, Twitter/X, Instagram, GitHub, etc.)
- Organization-specific filtering
- Better matching to eliminate wrong profiles
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from phase1_agent.main import IntelAgent
from phase1_agent.models import Person, Briefing, SearchResult
from phase1_agent.tools import TavilySearch, FirecrawlScrape
from phase1_agent.validator import ResultValidator
from datetime import datetime
from typing import Optional, Dict, List
import re


class SocialHandleExtractor:
    """Extract social media handles and URLs from text"""
    
    @staticmethod
    def extract_handles(text: str, url: str = "") -> Dict[str, str]:
        """Extract all social handles from text and URL"""
        handles = {}
        text_lower = text.lower()
        url_lower = url.lower()
        combined = text_lower + " " + url_lower
        
        # LinkedIn
        linkedin_match = re.search(r'https?://(?:www\.)?(?:in|linkedin)\.com/in/([a-z0-9\-]+)', combined)
        if linkedin_match:
            handles['linkedin'] = f"https://linkedin.com/in/{linkedin_match.group(1)}"
        
        # Twitter/X
        x_patterns = [
            r'https?://(?:x\.com|twitter\.com)/(@?[\w]+)',
            r'@([\w]+)\s+(?:on\s+)?twitter',
            r'twitter:\s*@([\w]+)'
        ]
        for pattern in x_patterns:
            match = re.search(pattern, combined)
            if match:
                handle = match.group(1).lstrip('@')
                handles['twitter_x'] = f"https://x.com/{handle}"
                break
        
        # Instagram
        instagram_match = re.search(r'https?://(?:www\.)?instagram\.com/([a-z0-9\._\-]+)', combined)
        if instagram_match:
            handles['instagram'] = f"https://instagram.com/{instagram_match.group(1)}"
        elif "@" in text_lower and "instagram" in text_lower:
            insta_handle = re.search(r'@([\w\.]+).*instagram', combined)
            if insta_handle:
                handles['instagram'] = f"@{insta_handle.group(1)}"
        
        # GitHub
        github_match = re.search(r'https?://github\.com/([a-z0-9\-]+)', combined)
        if github_match:
            handles['github'] = f"https://github.com/{github_match.group(1)}"
        
        # TikTok
        tiktok_match = re.search(r'https?://(?:www\.)?tiktok\.com/@([\w\.]+)', combined)
        if tiktok_match:
            handles['tiktok'] = f"https://tiktok.com/@{tiktok_match.group(1)}"
        
        return handles


class EnhancedBriefingGenerator:
    """Enhanced briefing with deep profile research + smart disambiguation"""
    
    def __init__(self):
        self.agent = IntelAgent()
        self.search = TavilySearch()
        self.scraper = FirecrawlScrape()
        self.validator = ResultValidator()
        self.handle_extractor = SocialHandleExtractor()
    
    def gather_comprehensive_data(self, person: Person) -> Dict:
        """
        Gather data from multiple sources with PROPER DISAMBIGUATION:
        - LinkedIn profile (filtered by organization)
        - Twitter/X account + handle
        - Instagram + handle
        - Personal website / company bio
        - Press mentions / news articles
        - GitHub / portfolio (if tech person)
        """
        
        print(f"\n[PHASE 2] GATHERING COMPREHENSIVE DATA FOR {person.name}")
        print(f"Organization: {person.company or 'Not specified'}")
        print("=" * 70)
        
        data = {
            "basic_info": {},
            "linkedin": None,
            "social_handles": {},  # ALL handles extracted
            "twitter": None,
            "instagram": None,
            "personal_site": None,
            "news_mentions": [],
            "tech_presence": None,
            "company_details": {}
        }
        
        # 1. LinkedIn Deep dive WITH DISAMBIGUATION
        print("\n[1/6] Searching LinkedIn profile (organization-filtered)...")
        linkedin_queries = [
            f'"{person.name}" site:linkedin.com "{person.company}"' if person.company else f'"{person.name}" site:linkedin.com',
            f'"{person.name}" "{person.role}" "{person.company}"' if person.company and person.role else f'"{person.name}" {person.role}',
        ]
        
        best_linkedin = None
        for query in linkedin_queries:
            linkedin_results = self.search.search(query)
            if linkedin_results:
                # VALIDATE: Filter by organization match
                validated = [r for r in linkedin_results 
                           if person.company.lower() in (r.title + " " + r.description).lower()]
                
                if validated:
                    best_linkedin = validated[0]
                    print(f"  ✓ Found (organization confirmed): {best_linkedin.title[:60]}")
                    break
                elif linkedin_results:
                    # Check if ANY result matches using validator
                    scored = [(r, self.validator.score_result(r, person)) for r in linkedin_results[:5]]
                    scored.sort(key=lambda x: x[1], reverse=True)
                    
                    if scored[0][1] > 0.6:
                        best_linkedin = scored[0][0]
                        print(f"  ✓ Found (high confidence): {best_linkedin.title[:60]}")
                        break
        
        if best_linkedin:
            # Extract LinkedIn URL
            data["social_handles"]["linkedin"] = best_linkedin.url
            scraped = self.scraper.scrape(best_linkedin.url)
            if scraped and scraped.content:
                data["linkedin"] = {
                    "url": best_linkedin.url,
                    "title": best_linkedin.title,
                    "snippet": best_linkedin.description,
                    "scraped_length": len(scraped.content)
                }
                # Extract any handles from scraped content
                extracted = self.handle_extractor.extract_handles(scraped.content, best_linkedin.url)
                data["social_handles"].update(extracted)
        
        # 2. Twitter/X presence
        print("\n[2/6] Searching Twitter/X profile...")
        x_queries = [
            f'"{person.name}" site:x.com OR site:twitter.com "{person.company}"' if person.company else f'"{person.name}" site:x.com OR site:twitter.com',
            f'"{person.name}" X handle' if person.name else "",
        ]
        
        for query in x_queries:
            if not query:
                continue
            twitter_results = self.search.search(query)
            if twitter_results:
                for result in twitter_results:
                    if "x.com" in result.url.lower() or "twitter.com" in result.url.lower():
                        print(f"  ✓ Found: {result.title[:60]}")
                        data["twitter"] = {
                            "url": result.url,
                            "title": result.title,
                            "snippet": result.description
                        }
                        # Extract X handle from URL
                        handle_match = re.search(r'(?:x\.com|twitter\.com)/(@?[\w]+)', result.url)
                        if handle_match:
                            data["social_handles"]["twitter_x"] = result.url
                        break
                if data["twitter"]:
                    break
        
        # 3. Instagram + other social media
        print("\n[3/6] Searching Instagram & other social profiles...")
        instagram_queries = [
            f'"{person.name}" site:instagram.com "{person.company}"' if person.company else f'"{person.name}" site:instagram.com',
        ]
        
        for query in instagram_queries:
            insta_results = self.search.search(query)
            if insta_results:
                for result in insta_results:
                    if "instagram.com" in result.url.lower():
                        print(f"  ✓ Instagram found: {result.title[:60]}")
                        data["instagram"] = result.url
                        data["social_handles"]["instagram"] = result.url
                        break
        
        # 4. Personal website / company bio
        print("\n[4/6] Searching personal website & company bio...")
        personal_results = self.search.search(
            f'"{person.name}" {person.company or ""} bio OR about OR profile'
        )
        if personal_results:
            best_result = personal_results[0]
            print(f"  ✓ Found: {best_result.title[:60]}")
            scraped = self.scraper.scrape(best_result.url)
            if scraped and scraped.content:
                data["personal_site"] = {
                    "url": best_result.url,
                    "title": best_result.title,
                    "content_preview": scraped.content[:500]
                }
                # Extract handles
                extracted = self.handle_extractor.extract_handles(scraped.content, best_result.url)
                data["social_handles"].update(extracted)
        
        # 5. Recent news mentions (ORGANIZED)
        print("\n[5/6] Searching recent news & press mentions...")
        news_results = self.search.search(
            f'"{person.name}" {person.company or ""} 2024 2025 OR news OR achievement'
        )
        if news_results:
            for i, result in enumerate(news_results[:3]):
                print(f"  ✓ {result.title[:60]}")
                data["news_mentions"].append({
                    "title": result.title,
                    "url": result.url,
                    "snippet": result.description
                })
        
        # 6. Company/Organization details
        if person.company:
            print(f"\n[6/6] Gathering {person.company} company context...")
            company_results = self.search.search(
                f"{person.company} company profile recent updates"
            )
            if company_results:
                for result in company_results[:2]:
                    print(f"  ✓ {result.title[:60]}")
                    data["company_details"][result.title] = result.description
        
        # Summary
        print(f"\n[EXTRACTION SUMMARY]")
        print(f"  Social handles found: {len(data['social_handles'])}")
        for platform, handle in data['social_handles'].items():
            print(f"    • {platform}: {handle[:40]}")
        
        return data
    
    def generate_enhanced_briefing(self, person: Person, context_data: Dict) -> Briefing:
        """
        Generate briefing using both Phase 1 agent AND comprehensive data
        """
        print(f"\n[SYNTHESIS] Creating enhanced briefing...")
        
        # Get Phase 1 briefing as foundation
        base_briefing = self.agent.research(person)
        
        if not base_briefing:
            print("  ✗ Failed to generate base briefing")
            return None
        
        # Enhance with comprehensive data for better meeting approach
        enhanced_data = {
            "person": base_briefing.person,
            "who_they_are": base_briefing.who_they_are,
            "what_they_care_about": base_briefing.what_they_care_about,
            "company_situation": base_briefing.company_situation,
            
            # Enhanced fields based on scraped data
            "meeting_approach": self._enhance_approach(base_briefing, context_data),
            "recent_activity": self._extract_recent_activity(context_data),
            "deep_insights": self._extract_deep_insights(context_data),
            "social_handles": context_data.get("social_handles", {}),  # NEW: Store all handles
            
            "smart_questions": base_briefing.smart_questions,
            "things_to_avoid": base_briefing.things_to_avoid,
            "icebreaker": base_briefing.icebreaker,
            "sources": base_briefing.sources,
            "timestamp": base_briefing.timestamp
        }
        
        # Create Briefing with enhanced data
        return Briefing(**enhanced_data)
    
    def _enhance_approach(self, base_briefing: Briefing, context_data: Dict) -> str:
        """
        Enhance meeting approach based on scraped data
        """
        approach = base_briefing.meeting_approach
        handles = context_data.get("social_handles", {})
        
        # Add LinkedIn-based insights with actual link
        if handles.get("linkedin"):
            approach += f"\n\n**LinkedIn Profile**: {handles['linkedin']} - Active presence. Reference their endorsements and recent activity."
        
        # Add Twitter/X insights with handle
        if handles.get("twitter_x"):
            approach += f"\n\n**X/Twitter Activity**: {handles['twitter_x']} - Check recent tweets for interests and trending discussions."
        
        # Add Instagram if available
        if handles.get("instagram"):
            approach += f"\n\n**Instagram**: {handles['instagram']} - Shows more personal side and interests."
        
        # Add recent news
        if context_data.get("news_mentions"):
            mentions = context_data["news_mentions"]
            if mentions:
                approach += f"\n\n**Recent News ({len(mentions)} mentions)**: Key story - {mentions[0]['title']}"
        
        return approach
    
    def _extract_recent_activity(self, context_data: Dict) -> List[str]:
        """Extract recent activity from all sources"""
        activities = []
        
        # From news mentions
        for mention in context_data.get("news_mentions", []):
            activities.append(f"Press: {mention['title']}")
        
        # From social handles available
        handles = context_data.get("social_handles", {})
        activity_msg = []
        if handles.get("linkedin"):
            activity_msg.append("LinkedIn")
        if handles.get("twitter_x"):
            activity_msg.append("X/Twitter")
        if handles.get("instagram"):
            activity_msg.append("Instagram")
        
        if activity_msg:
            activities.insert(0, f"Active on: {', '.join(activity_msg)}")
        
        return activities
    
    def _extract_deep_insights(self, context_data: Dict) -> Dict:
        """Extract deep insights from comprehensive data"""
        handles = context_data.get("social_handles", {})
        return {
            "linkedin_active": bool(handles.get("linkedin")),
            "twitter_x_active": bool(handles.get("twitter_x")),
            "instagram_active": bool(handles.get("instagram")),
            "github_active": bool(handles.get("github")),
            "news_mentions_count": len(context_data.get("news_mentions", [])),
            "tech_presence": bool(context_data.get("tech_presence")),
            "company_updates": len(context_data.get("company_details", {})),
            "total_social_platforms": len(handles)
        }
    
    def generate_context_aware_briefing(self, person: Person, meeting_type: str = "") -> Briefing:
        """
        Main entry point:
        1. Gather comprehensive data WITH PROPER DISAMBIGUATION
        2. Generate enhanced briefing with social handles
        3. Return with deep context
        """
        
        print(f"\n{'=' * 70}")
        print(f"PHASE 2: ENHANCED BRIEFING GENERATOR (IMPROVED)")
        print(f"{'=' * 70}")
        print(f"Person: {person.name} | Role: {person.role}")
        print(f"Company: {person.company or 'Not specified'}")
        if person.context:
            print(f"Context: {person.context}")
        
        # Step 1: Gather comprehensive data
        comprehensive_data = self.gather_comprehensive_data(person)
        
        # Step 2: Generate enhanced briefing
        briefing = self.generate_enhanced_briefing(person, comprehensive_data)
        
        if briefing:
            print(f"\n{'=' * 70}")
            print(f"✓ PHASE 2 COMPLETE - Enhanced briefing ready")
            print(f"{'=' * 70}")
            
            social = comprehensive_data.get('social_handles', {})
            print(f"\n📱 SOCIAL HANDLES FOUND ({len(social)}):")
            if social:
                for platform, handle in social.items():
                    print(f"   • {platform.upper()}: {handle}")
            else:
                print(f"   (No direct profiles found - may be private)")
            
            print(f"\n📰 DATA SOURCES:")
            print(f"   • LinkedIn: {'✓' if comprehensive_data.get('linkedin') else '✗'}")
            print(f"   • Twitter/X: {'✓' if comprehensive_data.get('twitter') else '✗'}")
            print(f"   • Instagram: {'✓' if comprehensive_data.get('instagram') else '✗'}")
            print(f"   • Personal Site: {'✓' if comprehensive_data.get('personal_site') else '✗'}")
            print(f"   • News Mentions: {len(comprehensive_data.get('news_mentions', []))}")
            print(f"   • Company Details: {len(comprehensive_data.get('company_details', {}))}")
        
        return briefing


def main():
    """Test Phase 2 enhanced briefing"""
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python -m phase2_enhanced_briefing.generator 'Name' 'Role' ['Company'] ['Context']")
        sys.exit(1)
    
    name = sys.argv[1]
    role = sys.argv[2]
    company = sys.argv[3] if len(sys.argv) > 3 else None
    context = sys.argv[4] if len(sys.argv) > 4 else None
    
    person = Person(name=name, role=role, company=company, context=context)
    
    generator = EnhancedBriefingGenerator()
    briefing = generator.generate_context_aware_briefing(person, context)
    
    if briefing:
        print(f"\n{'=' * 70}")
        print("BRIEFING PREVIEW")
        print(f"{'=' * 70}")
        print(briefing.to_markdown()[:800] + "...\n")


if __name__ == "__main__":
    main()
