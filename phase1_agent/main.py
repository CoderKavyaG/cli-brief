#!/usr/bin/env python3
"""
Phase 1: Agent Loop
Intel briefing agent using local Ollama
"""

import sys
import json
import requests
from datetime import datetime
from typing import Optional, List, Dict, Any

from phase1_agent.config import OLLAMA_GENERATE_URL, OLLAMA_MODEL, OUTPUT_DIR
from phase1_agent.models import Person, Briefing, SearchResult, ScrapedContent
from phase1_agent.tools import TavilySearch, FirecrawlScrape, FileSave
from phase1_agent.prompts import SYSTEM_PROMPT, get_user_prompt, format_search_results_for_claude, format_scraped_content_for_claude
from phase1_agent.cache import BriefingCache
import os

class IntelAgent:
    """Main agent that orchestrates research"""
    
    def __init__(self):
        self.cache = BriefingCache()
        self.search_tool = TavilySearch()
        self.scrape_tool = FirecrawlScrape()
        self.file_tool = FileSave()
        self.conversation_history = []
    
    def _call_ollama(self, prompt: str, system: str = SYSTEM_PROMPT) -> str:
        """Call Ollama locally"""
        try:
            response = requests.post(
                OLLAMA_GENERATE_URL,
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "system": system,
                    "stream": False
                },
                timeout=60
            )
            response.raise_for_status()
            return response.json()["response"]
        except Exception as e:
            print(f"[OLLAMA ERROR] {str(e)}")
            raise
    
    def research(self, person: Person) -> Optional[Briefing]:
        """Main research loop"""
        
        print(f"\n{'='*60}")
        print(f"RESEARCHING: {person.name} ({person.role})")
        print(f"{'='*60}\n")
        
        # Check cache first
        cached = self.cache.get(person.name, person.role)
        if cached:
            briefing = Briefing(**cached)
            return briefing
        
        # Step 1: Initial research query
        print("[STEP 1] Planning research strategy...")
        search_plan_prompt = f"""Plan the research strategy for:
Name: {person.name}
Role: {person.role}
Company: {person.company}

What 3-4 specific searches would give the most useful information about this person's current priorities and company situation?"""
        
        search_plan = self._call_ollama(search_plan_prompt)
        print(f"Research plan:\n{search_plan}\n")
        
        # Step 2: Execute searches
        print("[STEP 2] Executing searches...")
        all_search_results = []
        
        search_queries = [
            f"{person.name} {person.role} {datetime.now().year}",
            f"{person.company} recent news",
            f"{person.name} LinkedIn posts",
            f"{person.company} latest announcements"
        ]
        
        for query in search_queries[:2]:  # Limit to save credits
            results = self.search_tool.search(query, count=3)
            all_search_results.extend(results)
        
        if not all_search_results:
            print("[WARNING] No search results found")
            return None
        
        # Step 3: Decide which URLs to scrape
        print("[STEP 3] Analyzing which sources to scrape...")
        results_formatted = format_search_results_for_claude(all_search_results[:5])
        
        scrape_decision_prompt = f"""Based on these search results, which URLs are most valuable to scrape for understanding {person.name}'s current thinking and their company's situation?

{results_formatted}

List the top 3-4 URLs to scrape, in order of usefulness."""
        
        scrape_decision = self._call_ollama(scrape_decision_prompt)
        print(f"URLs to scrape:\n{scrape_decision}\n")
        
        # Step 4: Scrape valuable content
        print("[STEP 4] Scraping content...")
        scraped_contents = []
        
        for result in all_search_results[:4]:  # Limit scrapes
            content = self.scrape_tool.scrape(result.url)
            if content:
                scraped_contents.append(content)
        
        if not scraped_contents:
            print("[WARNING] Could not scrape any content")
            return None
        
        # Step 5: Synthesize into briefing
        print("[STEP 5] Synthesizing briefing...")
        
        content_summary = "\n\n".join([
            format_scraped_content_for_claude(c) for c in scraped_contents
        ])
        
        synthesis_prompt = f"""Based on this research about {person.name}, create a focused briefing.

Person: {person.name}, {person.role} at {person.company}
Meeting Context: {person.context}

Research findings:
{content_summary}

Generate the briefing in this JSON format:
{{
    "who_they_are": "2-sentence human description",
    "what_they_care_about": "What they're focused on now",
    "company_situation": "Company stage and current focus",
    "meeting_approach": "How to approach them given the context",
    "smart_questions": ["Q1", "Q2", "Q3"],
    "things_to_avoid": ["A1", "A2"],
    "icebreaker": "Specific recent thing to mention"
}}"""
        
        briefing_json_str = self._call_ollama(synthesis_prompt)
        
        # Parse JSON from response
        try:
            briefing_data = json.loads(briefing_json_str)
        except json.JSONDecodeError:
            print("[ERROR] Could not parse briefing JSON")
            return None
        
        # Step 6: Create briefing object
        briefing = Briefing(
            person=person,
            who_they_are=briefing_data.get("who_they_are", ""),
            what_they_care_about=briefing_data.get("what_they_care_about", ""),
            company_situation=briefing_data.get("company_situation", ""),
            meeting_approach=briefing_data.get("meeting_approach", ""),
            smart_questions=briefing_data.get("smart_questions", []),
            things_to_avoid=briefing_data.get("things_to_avoid", []),
            icebreaker=briefing_data.get("icebreaker", ""),
            sources=[r.url for r in all_search_results[:5]],
            timestamp=datetime.now().isoformat()
        )
        
        # Step 7: Save briefing
        print("[STEP 6] Saving briefing...")
        filename = f"briefing_{person.name.replace(' ', '_').lower()}_{datetime.now().strftime('%Y-%m-%d')}.md"
        markdown = briefing.to_markdown()
        self.file_tool.save_briefing(filename, markdown, OUTPUT_DIR)
        
        # Cache it
        self.cache.set(person.name, person.role, briefing.to_dict())
        
        print(f"\n[DONE] Briefing ready!\n")
        return briefing

def main():
    """Entry point"""
    if len(sys.argv) < 3:
        print("Usage: python -m phase1_agent.main <name> <role> [company] [context]")
        print("Example: python -m phase1_agent.main 'Satya Nadella' 'CEO' 'Microsoft' 'acquisition meeting'")
        sys.exit(1)
    
    name = sys.argv[1]
    role = sys.argv[2]
    company = sys.argv[3] if len(sys.argv) > 3 else "Unknown"
    context = sys.argv[4] if len(sys.argv) > 4 else "General business meeting"
    
    person = Person(name=name, role=role, company=company, context=context)
    
    agent = IntelAgent()
    briefing = agent.research(person)
    
    if briefing:
        print("\n" + "="*60)
        print("BRIEFING PREVIEW")
        print("="*60)
        print(briefing.to_markdown()[:1000] + "...\n")

if __name__ == "__main__":
    main()
