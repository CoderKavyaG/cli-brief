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
from phase1_agent.tools import TavilySearch, FirecrawlScrape, FileSave, LinkExtractor
from phase1_agent.prompts import SYSTEM_PROMPT, get_user_prompt
from phase1_agent.cache import BriefingCache
from phase1_agent.quality import BriefingValidator
import os

class IntelAgent:
    """Main agent that orchestrates research via Groq tool calling"""
    
    def __init__(self):
        self.cache = BriefingCache()
        self.search_tool = TavilySearch()
        self.scrape_tool = FirecrawlScrape()
        self.file_tool = FileSave()
        self.messages = []
        self.search_count = 0
        self.scrape_count = 0
        self.scrape_success = 0
    
    def _call_groq_with_tools(self, messages: List[Dict], tools: List[Dict]) -> Dict:
        """Call Groq API with tool calling support"""
        max_retries = 3
        base_wait = 2
        
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
                        "messages": messages,
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
                        print(f"[GROQ RATE LIMIT] Retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})...")
                        time.sleep(wait_time)
                        continue
                print(f"[GROQ ERROR] {str(e)}")
                raise
            except Exception as e:
                print(f"[GROQ ERROR] {str(e)}")
                raise
        
        raise Exception(f"[GROQ ERROR] Max retries exceeded")
    
    def _execute_tool(self, tool_name: str, arguments: Dict) -> str:
        """Execute a tool and return result as string"""
        try:
            if tool_name == "tavily_search":
                query = arguments.get("query", "")
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
                    self.scrape_success += 1
                    return json.dumps({
                        "success": True,
                        "url": url,
                        "content": scraped.content[:1000]
                    }, separators=(',', ':'))
                else:
                    return json.dumps({
                        "success": False,
                        "url": url
                    }, separators=(',', ':'))
            
            elif tool_name == "save_briefing":
                content = arguments.get("content", "")
                name = arguments.get("name", "briefing")
                
                filename = f"briefing_{name.replace(' ', '_').lower()}_{datetime.now().strftime('%Y-%m-%d')}.md"
                self.file_tool.save_briefing(filename, content, OUTPUT_DIR)
                print(f"  [SAVE] {filename}")
                
                return json.dumps({
                    "success": True,
                    "filename": filename
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
        
        # Define tools for Groq
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "tavily_search",
                    "description": "Search the web. Use for finding recent news, interviews, company info. Search queries should contain ONLY: person name + company + research keywords. Never include meeting context.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query with only person name, company, and research keywords"}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "jina_scrape",
                    "description": "Read full content of a webpage. Use after searching to read articles, blogs, company pages.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {"type": "string", "description": "URL to scrape"}
                        },
                        "required": ["url"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "save_briefing",
                    "description": "Save the completed briefing. Only call this once you have gathered enough research.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "content": {"type": "string", "description": "Full briefing markdown content"},
                            "name": {"type": "string", "description": "Person's name for filename"}
                        },
                        "required": ["content", "name"]
                    }
                }
            }
        ]
        
        # Initial system message
        initial_prompt = f"""You are researching: {person.name}
Role: {person.role}
Company: {person.company}
Meeting Context: {person.context}

Use the tools to find current information about this person. Run at least 4 searches and scrape at least 2 pages before writing the briefing.

Remember critical rules:
- Search queries contain ONLY person name, company, and research keywords - NEVER include "{person.context}" in searches
- Run searches in this order:
  1. {person.name} {person.company} 2026
  2. {person.name} interview OR podcast 2025 OR 2026
  3. {person.company} news OR announcement 2026
  4. {person.company} engineering blog OR tech blog
  5. {person.company} jobs hiring 2026
  6. site:linkedin.com {person.name} {person.company}
- Scrape at least 2 different URLs to get quality content
- Create a briefing following the exact OUTPUT STRUCTURE from your system prompt
- Include a Research Confidence section tracking searches run and pages scraped
- End by calling save_briefing with the complete markdown content"""

        self.messages = [
            {"role": "user", "content": initial_prompt}
        ]
        
        # Agentic loop
        loop_count = 0
        max_loops = 20
        max_msg_history = 8  # Trim message history to prevent 413 payload errors
        
        while loop_count < max_loops:
            loop_count += 1
            print(f"[LOOP {loop_count}] Calling Groq...")
            
            # Trim messages to prevent payload too large errors
            msgs_to_send = self.messages[-max_msg_history:] if len(self.messages) > max_msg_history else self.messages
            
            response = self._call_groq_with_tools(msgs_to_send, tools)
            
            message_content = response["choices"][0]["message"]
            
            # Add assistant response (truncated to save space)
            self.messages.append({
                "role": "assistant",
                "content": message_content.get("content", "")[:400]
            })
            
            # Check for tool calls
            tool_calls = message_content.get("tool_calls", [])
            
            if not tool_calls:
                # No more tool calls - Groq is done
                print("\n[AGENT COMPLETE] Groq finished research")
                
                # Extract final briefing from last message
                final_content = message_content.get("content", "")
                
                if final_content:
                    # Save it if not already saved via tool call
                    if "save_briefing" not in str(tool_calls):
                        filename = f"briefing_{person.name.replace(' ', '_').lower()}_{datetime.now().strftime('%Y-%m-%d')}.md"
                        self.file_tool.save_briefing(filename, final_content, OUTPUT_DIR)
                        print(f"[SAVE] {filename}")
                
                # Build briefing object with metadata
                briefing = Briefing(
                    person=person,
                    who_they_are=final_content[:500],
                    what_they_care_about=final_content[500:1000],
                    company_situation=final_content[1000:1500],
                    meeting_approach=final_content[1500:2000],
                    smart_questions=["See full briefing for details"],
                    things_to_avoid=["See full briefing for details"],
                    icebreaker=final_content[2000:2200],
                    sources=[f"Research: {self.search_count} searches, {self.scrape_success} scrapes"],
                    timestamp=datetime.now().isoformat()
                )
                
                return briefing
            
            # Execute tool calls
            print(f"[TOOLS] Executing {len(tool_calls)} tool calls...")
            tool_results = []
            
            for tool_call in tool_calls:
                tool_name = tool_call["function"]["name"]
                arguments = json.loads(tool_call["function"]["arguments"])
                
                print(f"  > {tool_name}")
                result = self._execute_tool(tool_name, arguments)
                
                tool_results.append({
                    "tool_call_id": tool_call["id"],
                    "tool_name": tool_name,
                    "result": result
                })
            
            # Add tool results to messages (size-capped to prevent bloat)
            for tool_result in tool_results:
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tool_result["tool_call_id"],
                    "content": tool_result["result"][:1200]
                })
            
            print(f"[STATS] Searches: {self.search_count}, Scrapes: {self.scrape_count}, Successful: {self.scrape_success}\n")
        
        print("[ERROR] Max loop count exceeded")
        return None


def main():
    """Entry point"""
    if len(sys.argv) < 3:
        print("Usage: python -m phase1_agent.main <name> <role> [company] [context]")
        print("Example: python -m phase1_agent.main 'Albinder Dhindsa' 'CEO' 'Blinkit' 'I want to pitch supply chain tool'")
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
        print("BRIEFING SAVED")
        print("="*60)
        print(f"Research Summary:")
        print(f"- Searches executed: {agent.search_count}")
        print(f"- Pages scraped: {agent.scrape_count}")
        print(f"- Successful scrapes: {agent.scrape_success}")
        print(f"- Confidence: {'HIGH' if agent.scrape_success >= 2 else 'MEDIUM' if agent.scrape_success >= 1 else 'LOW'}")


if __name__ == "__main__":
    main()
