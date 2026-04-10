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

from phase1_agent.config import GROQ_API_KEY, GROQ_MODEL, GROQ_API_URL, OUTPUT_DIR
from phase1_agent.models import Person, Briefing, SearchResult, ScrapedContent
from phase1_agent.tools import TavilySearch, FirecrawlScrape, FileSave
from phase1_agent.prompts import SYSTEM_PROMPT, get_user_prompt, format_search_results_for_claude, format_scraped_content_for_claude
from phase1_agent.cache import BriefingCache
from phase1_agent.validator import ResultValidator, SearchRefinement, AmbiguityResolver
from phase1_agent.recovery import RetryStrategy, SearchRecovery, ContentRecovery
from phase1_agent.quality import BriefingValidator, BriefingRepair
import os

class IntelAgent:
    """Main agent that orchestrates research"""
    
    def __init__(self):
        self.cache = BriefingCache()
        self.search_tool = TavilySearch()
        self.scrape_tool = FirecrawlScrape()
        self.file_tool = FileSave()
        self.conversation_history = []
    
    def _call_groq(self, prompt: str, system: str = SYSTEM_PROMPT) -> str:
        """Call Groq API for fast LLM inference"""
        try:
            headers = {
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                GROQ_API_URL,
                json={
                    "model": GROQ_MODEL,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 2000
                },
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"[GROQ ERROR] {str(e)}")
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
        
        search_plan = self._call_groq(search_plan_prompt)
        print(f"Research plan:\n{search_plan}\n")
        
        # Step 2: Execute searches
        print("[STEP 2] Executing smart searches...")
        all_search_results = []
        
        # Generate specific queries that include person's context
        specific_queries = SearchRefinement.generate_specific_queries(person)
        generic_queries = [
            f"{person.company} recent news",
            f"{person.company} latest announcements"
        ]
        
        all_queries = specific_queries + generic_queries
        
        # Search and validate
        for query in all_queries[:3]:  # Limit to save credits
            print(f"  [SEARCH] {query}")
            results = self.search_tool.search(query, count=3)
            
            # Validate results match the person (for person-specific queries)
            if person.name in query:
                # Filter by relevance to this person
                validated = ResultValidator.filter_results(results, person, min_score=0.4)
                all_search_results.extend(validated)
                
                # Check for ambiguity
                has_conflict, conflict_msg = AmbiguityResolver.has_conflict(validated, person)
                if has_conflict:
                    print(f"  [CONFLICT DETECTED] {conflict_msg}")
                    print(f"  [RETRY] Searching more specifically...")
            else:
                # Company/org queries - accept all
                all_search_results.extend(results)
        
        if not all_search_results:
            print("[WARNING] No search results found")
            return None
        
        # Remove duplicates
        seen_urls = set()
        unique_results = []
        for result in all_search_results:
            if result.url not in seen_urls:
                seen_urls.add(result.url)
                unique_results.append(result)
        all_search_results = unique_results
        
        print(f"[SEARCH COMPLETE] Validated {len(all_search_results)} unique results")
        
        # Step 3: Decide which URLs to scrape
        print("[STEP 3] Analyzing which sources to scrape...")
        results_formatted = format_search_results_for_claude(all_search_results[:5])
        
        scrape_decision_prompt = f"""Based on these search results, which URLs are most valuable to scrape for understanding {person.name}'s current thinking and their company's situation?

{results_formatted}

List the top 3-4 URLs to scrape, in order of usefulness."""
        
        scrape_decision = self._call_groq(scrape_decision_prompt)
        print(f"URLs to scrape:\n{scrape_decision}\n")
        
        # Step 4 & 5: Use search results as primary content source
        print("[STEP 4] Processing search results as content...")
        scraped_contents = []
        
        # Convert search results directly to content with fallback scraping
        for result in all_search_results[:8]:
            # Try scraping first
            scraped = self.scrape_tool.scrape(result.url, fallback_snippet=result.description)
            
            # If scraping failed or returned empty, use search snippet
            if not scraped or not scraped.content or len(scraped.content) < 20:
                scraped_content = ScrapedContent(
                    url=result.url,
                    title=result.title,
                    content=result.description,  # Use search snippet as content
                    timestamp=datetime.now().isoformat()
                )
            else:
                scraped_content = scraped
            
            if scraped_content.content:
                scraped_contents.append(scraped_content)
        
        print(f"[CONTENT READY] Collected {len(scraped_contents)} sources with content")
        
        if not scraped_contents:
            print("[ERROR] Completely unable to gather content")
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
        
        briefing_json_str = self._call_groq(synthesis_prompt)
        
        # Parse JSON from response (handle markdown wrapping)
        try:
            # Try direct JSON parsing
            briefing_data = json.loads(briefing_json_str)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            try:
                if "```json" in briefing_json_str:
                    json_part = briefing_json_str.split("```json")[1].split("```")[0].strip()
                elif "```" in briefing_json_str:
                    json_part = briefing_json_str.split("```")[1].split("```")[0].strip()
                else:
                    # Try to find JSON object between { and }
                    start = briefing_json_str.find("{")
                    end = briefing_json_str.rfind("}") + 1
                    json_part = briefing_json_str[start:end]
                
                briefing_data = json.loads(json_part)
            except:
                print("[ERROR] Could not parse briefing JSON:")
                print(briefing_json_str[:500])
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
        
        # Step 7: Validate briefing quality
        print("[STEP 7] Validating briefing quality...")
        is_valid, issues = BriefingValidator.validate_briefing(briefing)
        quality_score = BriefingValidator.get_quality_score(briefing)
        print(f"[QUALITY] Score: {quality_score:.0f}/100")
        
        # If quality too low, attempt to improve
        should_retry, retry_reason = BriefingValidator.should_retry(briefing, min_quality=65.0)
        
        if should_retry and len(all_search_results) >= 4:
            print(f"[RETRY NEEDED] {retry_reason}")
            print("[ATTEMPTING RECOVERY] Re-synthesizing with expanded context...")
            
            # Gather more detailed context
            extended_context = "Additional guidance:\n"
            for issue in issues[:3]:
                extended_context += f"- {issue}\n"
            
            retry_synthesis_prompt = synthesis_prompt + f"\n\nIMPORTANT: {extended_context}"
            retry_json_str = self._call_groq(retry_synthesis_prompt)
            
            try:
                if "```json" in retry_json_str:
                    json_part = retry_json_str.split("```json")[1].split("```")[0].strip()
                elif "```" in retry_json_str:
                    json_part = retry_json_str.split("```")[1].split("```")[0].strip()
                else:
                    start = retry_json_str.find("{")
                    end = retry_json_str.rfind("}") + 1
                    json_part = retry_json_str[start:end]
                
                retry_data = json.loads(json_part)
                
                # Create new briefing with retry data
                briefing = Briefing(
                    person=person,
                    who_they_are=retry_data.get("who_they_are", briefing.who_they_are),
                    what_they_care_about=retry_data.get("what_they_care_about", briefing.what_they_care_about),
                    company_situation=retry_data.get("company_situation", briefing.company_situation),
                    meeting_approach=retry_data.get("meeting_approach", briefing.meeting_approach),
                    smart_questions=retry_data.get("smart_questions", briefing.smart_questions),
                    things_to_avoid=retry_data.get("things_to_avoid", briefing.things_to_avoid),
                    icebreaker=retry_data.get("icebreaker", briefing.icebreaker),
                    sources=briefing.sources,
                    timestamp=datetime.now().isoformat()
                )
                
                # Validate again
                is_valid, issues = BriefingValidator.validate_briefing(briefing)
                quality_score = BriefingValidator.get_quality_score(briefing)
                print(f"[RECOVERY] New quality score: {quality_score:.0f}/100")
                
            except:
                print("[RECOVERY FAILED] Using original briefing")
        
        # Step 8: Save briefing
        print("[STEP 8] Saving briefing...")
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
