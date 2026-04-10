"""
Phase 2: Enhanced Briefing Generator
Extended research with deep profile scraping from LinkedIn, Twitter, personal websites
Generates actionable meeting prep with detailed context
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from phase1_agent.main import IntelAgent
from phase1_agent.models import Person, Briefing
from phase1_agent.tools import TavilySearch, FirecrawlScrape
from datetime import datetime
from typing import Optional, Dict, List


class EnhancedBriefingGenerator:
    """Enhanced briefing with deep profile research"""
    
    def __init__(self):
        self.agent = IntelAgent()
        self.search = TavilySearch()
        self.scraper = FirecrawlScrape()
    
    def gather_comprehensive_data(self, person: Person) -> Dict:
        """
        Gather data from multiple sources:
        - LinkedIn profile
        - Twitter/X account
        - Personal website / company bio
        - Press mentions / news articles
        - GitHub / portfolio (if tech person)
        """
        
        print(f"\n[PHASE 2] GATHERING COMPREHENSIVE DATA FOR {person.name}")
        print("=" * 70)
        
        data = {
            "basic_info": {},
            "linkedin": None,
            "twitter": None,
            "personal_site": None,
            "news_mentions": [],
            "tech_presence": None,  # GitHub, Stack Overflow
            "company_details": {}
        }
        
        # 1. LinkedIn Deep dive
        print("\n[1/5] Searching LinkedIn profile...")
        linkedin_results = self.search.search(
            f'"{person.name}" site:linkedin.com {person.company or ""}'
        )
        if linkedin_results:
            for result in linkedin_results:
                print(f"  → Found: {result.title}")
                scraped = self.scraper.scrape(result.url)
                if scraped and scraped.content:
                    data["linkedin"] = {
                        "url": result.url,
                        "title": result.title,
                        "snippet": result.description,
                        "scraped_length": len(scraped.content)
                    }
                    break
        
        # 2. Twitter/X presence
        print("\n[2/5] Searching Twitter profile...")
        twitter_results = self.search.search(
            f'"{person.name}" Twitter OR X @handle {person.company or ""}'
        )
        if twitter_results:
            for result in twitter_results:
                if "twitter" in result.url.lower() or "x.com" in result.url.lower():
                    print(f"  → Found: {result.title}")
                    data["twitter"] = {
                        "url": result.url,
                        "title": result.title,
                        "snippet": result.description
                    }
                    break
        
        # 3. Personal website / company bio
        print("\n[3/5] Searching personal website & company bio...")
        personal_results = self.search.search(
            f'"{person.name}" {person.company} bio OR about OR profile'
        )
        if personal_results:
            best_result = personal_results[0]
            print(f"  → Found: {best_result.title}")
            scraped = self.scraper.scrape(best_result.url)
            if scraped and scraped.content:
                data["personal_site"] = {
                    "url": best_result.url,
                    "title": best_result.title,
                    "content_preview": scraped.content[:500]
                }
        
        # 4. Recent news mentions
        print("\n[4/5] Searching recent news & press mentions...")
        news_results = self.search.search(
            f'"{person.name}" recent news 2024 2025'
        )
        if news_results:
            for i, result in enumerate(news_results[:3]):
                print(f"  → Found: {result.title}")
                data["news_mentions"].append({
                    "title": result.title,
                    "url": result.url,
                    "snippet": result.description
                })
        
        # 5. Tech presence (if applicable)
        if person.role and any(word in person.role.lower() for word in ["engineer", "developer", "cto", "vp"]):
            print("\n[5/5] Searching GitHub & tech profiles...")
            tech_results = self.search.search(
                f'"{person.name}" GitHub OR Stack Overflow'
            )
            if tech_results:
                data["tech_presence"] = {
                    "results": [
                        {"title": r.title, "url": r.url}
                        for r in tech_results[:2]
                    ]
                }
        
        # 6. Company/Organization details
        if person.company:
            print(f"\n[6/6] Gathering {person.company} company context...")
            company_results = self.search.search(
                f"{person.company} company profile recent updates"
            )
            if company_results:
                for result in company_results[:2]:
                    print(f"  → Found: {result.title}")
                    data["company_details"][result.title] = result.description
        
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
        
        # Add LinkedIn-based insights
        if context_data.get("linkedin"):
            approach += "\n\n**LinkedIn Profile Insights**: This person maintains an active LinkedIn presence. Reference their recent posts or endorsements to show you've done thorough research."
        
        # Add Twitter insights
        if context_data.get("twitter"):
            approach += "\n\n**Social Media Activity**: They're active on Twitter/X. Their recent tweets reveal interests in [check profile] - good talking points."
        
        # Add recent news
        if context_data.get("news_mentions"):
            mentions = context_data["news_mentions"]
            if mentions:
                approach += f"\n\n**Recent News**: {len(mentions)} recent mentions found. Key story: {mentions[0]['title']}"
        
        return approach
    
    def _extract_recent_activity(self, context_data: Dict) -> List[str]:
        """Extract recent activity from all sources"""
        activities = []
        
        # From news mentions
        for mention in context_data.get("news_mentions", []):
            activities.append(f"Press: {mention['title']}")
        
        return activities
    
    def _extract_deep_insights(self, context_data: Dict) -> Dict:
        """Extract deep insights from comprehensive data"""
        return {
            "linkedin_active": bool(context_data.get("linkedin")),
            "twitter_active": bool(context_data.get("twitter")),
            "news_mentions_count": len(context_data.get("news_mentions", [])),
            "tech_presence": bool(context_data.get("tech_presence")),
            "company_updates": len(context_data.get("company_details", {}))
        }
    
    def generate_context_aware_briefing(self, person: Person, meeting_type: str = "") -> Briefing:
        """
        Main entry point:
        1. Gather comprehensive data
        2. Generate enhanced briefing
        3. Return with deep context
        """
        
        print(f"\n{'=' * 70}")
        print(f"PHASE 2: ENHANCED BRIEFING GENERATOR")
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
            print(f"\n✓ PHASE 2 COMPLETE - Enhanced briefing ready")
            print(f"  • LinkedIn data: {'✓' if comprehensive_data.get('linkedin') else '✗'}")
            print(f"  • Twitter data: {'✓' if comprehensive_data.get('twitter') else '✗'}")
            print(f"  • News mentions: {len(comprehensive_data.get('news_mentions', []))}")
            print(f"  • Company details: {len(comprehensive_data.get('company_details', {}))}")
        
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
