"""
Profile Selector & Confirmation Interface
Lets users choose the correct profile from search results
Shows all profile IDs, URLs, and metadata for manual confirmation
"""

from typing import List, Optional, Dict
from phase1_agent.models import SearchResult, Person
from phase1_agent.tools import TavilySearch
from phase1_agent.validator import ResultValidator
import re


class ProfileExtractor:
    """Extract profile IDs and metadata from URLs"""
    
    @staticmethod
    def extract_profile_id(url: str) -> Optional[str]:
        """Extract profile ID from various URL formats"""
        
        # LinkedIn: https://www.linkedin.com/in/john-smith-123abc/
        linkedin_match = re.search(r'linkedin\.com/in/([a-z0-9\-]+)', url)
        if linkedin_match:
            return f"linkedin:{linkedin_match.group(1)}"
        
        # Twitter/X: https://x.com/handle or https://twitter.com/handle
        twitter_match = re.search(r'(?:x\.com|twitter\.com)/(@?[\w]+)', url)
        if twitter_match:
            handle = twitter_match.group(1).lstrip('@')
            return f"twitter:{handle}"
        
        # Instagram: https://www.instagram.com/username/
        instagram_match = re.search(r'instagram\.com/([a-z0-9\._\-]+)', url)
        if instagram_match:
            return f"instagram:{instagram_match.group(1)}"
        
        # GitHub: https://github.com/username
        github_match = re.search(r'github\.com/([a-z0-9\-]+)', url)
        if github_match:
            return f"github:{github_match.group(1)}"
        
        # Facebook: https://www.facebook.com/username
        fb_match = re.search(r'facebook\.com/([a-z0-9\.\-]+)', url)
        if fb_match:
            return f"facebook:{fb_match.group(1)}"
        
        # TikTok: https://www.tiktok.com/@username
        tiktok_match = re.search(r'tiktok\.com/@([\w\.]+)', url)
        if tiktok_match:
            return f"tiktok:{tiktok_match.group(1)}"
        
        return None


class ProfileSelector:
    """Interactive profile selection from search results"""
    
    def __init__(self):
        self.search = TavilySearch()
        self.validator = ResultValidator()
        self.extractor = ProfileExtractor()
    
    def search_profiles(self, person: Person, limit: int = 5) -> List[Dict]:
        """
        Search for person and return ALL results with profile IDs
        User can then confirm which one is correct
        """
        
        print(f"\n{'=' * 80}")
        print(f"SEARCHING FOR: {person.name} | {person.role} | {person.company}")
        print(f"{'=' * 80}\n")
        
        # Generate search queries
        queries = [
            f'"{person.name}" "{person.company}"' if person.company else f'"{person.name}"',
            f'"{person.name}" {person.role} {person.company}' if person.company and person.role else f'"{person.name}" {person.role}',
            f'{person.name} {person.company}' if person.company else person.name,
        ]
        
        all_results = []
        seen_urls = set()
        
        for i, query in enumerate(queries, 1):
            if len(all_results) >= limit:
                break
            
            print(f"[QUERY {i}] {query}")
            results = self.search.search(query)
            
            if results:
                for result in results:
                    if result.url not in seen_urls and len(all_results) < limit:
                        seen_urls.add(result.url)
                        
                        # Extract profile ID
                        profile_id = self.extractor.extract_profile_id(result.url)
                        
                        # Score result
                        score = self.validator.score_result(result, person)
                        
                        all_results.append({
                            "rank": len(all_results) + 1,
                            "title": result.title,
                            "url": result.url,
                            "description": result.description,
                            "profile_id": profile_id or "N/A",
                            "confidence": round(score * 100, 1),
                        })
        
        return all_results
    
    def display_results(self, results: List[Dict], person: Person) -> None:
        """Display results in user-friendly format"""
        
        print(f"\n{'=' * 80}")
        print(f"FOUND {len(results)} PROFILES")
        print(f"{'=' * 80}\n")
        
        for result in results:
            print(f"[{result['rank']}] {result['title']}")
            print(f"    URL: {result['url']}")
            print(f"    ID: {result['profile_id']}")
            print(f"    Confidence: {result['confidence']}%")
            print(f"    Summary: {result['description'][:100]}...")
            print()
    
    def get_user_selection(self, results: List[Dict]) -> Optional[Dict]:
        """
        Ask user to select their choice
        Returns selected result or None
        """
        
        if not results:
            print("❌ No results found")
            return None
        
        if len(results) == 1:
            print(f"✓ Only one result found - using it automatically\n")
            return results[0]
        
        print(f"\n{'=' * 80}")
        print("SELECT THE CORRECT PROFILE")
        print(f"{'=' * 80}\n")
        
        while True:
            try:
                selection = input(f"Enter profile number (1-{len(results)}) or 'skip' (or press Enter for #1): ").strip()
                
                if not selection:
                    selection = "1"
                
                if selection.lower() == "skip":
                    return None
                
                idx = int(selection) - 1
                if 0 <= idx < len(results):
                    selected = results[idx]
                    print(f"\n✓ Selected: {selected['title']}")
                    print(f"  ID: {selected['profile_id']}")
                    return selected
                else:
                    print(f"❌ Invalid selection. Enter 1-{len(results)}")
            
            except ValueError:
                print(f"❌ Invalid input. Enter a number or 'skip'")
    
    def search_and_select(self, person: Person) -> Optional[Dict]:
        """
        Complete workflow:
        1. Search
        2. Display results
        3. User selects one
        4. Return selected profile info
        """
        
        # Step 1: Search
        results = self.search_profiles(person)
        
        # Step 2: Display
        self.display_results(results, person)
        
        # Step 3: User selects
        selected = self.get_user_selection(results)
        
        if selected:
            print(f"\n{'=' * 80}")
            print(f"CONFIRMED PROFILE")
            print(f"{'=' * 80}")
            print(f"Name: {person.name}")
            print(f"Role: {person.role}")
            print(f"Company: {person.company}")
            print(f"URL: {selected['url']}")
            print(f"Profile ID: {selected['profile_id']}")
            print(f"Confidence: {selected['confidence']}%")
            print(f"{'=' * 80}\n")
        
        return selected


def interactive_profile_search(
    name: str,
    role: str,
    company: str,
    context: str = ""
) -> Optional[Dict]:
    """
    Main entry point for interactive profile search
    
    Usage:
        profile = interactive_profile_search("Jane Doe", "VP Product", "Google")
        if profile:
            print(f"Using profile: {profile['profile_id']}")
    """
    
    person = Person(name=name, role=role, company=company, context=context)
    selector = ProfileSelector()
    
    return selector.search_and_select(person)


if __name__ == "__main__":
    # Example usage
    profile = interactive_profile_search(
        "Ananya Malhotra",
        "Student",
        "Chitkara University"
    )
    
    if profile:
        print(f"\n✓ Profile selected: {profile['profile_id']}")
