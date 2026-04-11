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
        self.scraped_contents = []  # Track all scraped content for synthesis
    
    def _call_groq_with_tools(self, messages: List[Dict], tools: List[Dict], system_message: str = None) -> Dict:
        """Call Groq API with tool calling support"""
        max_retries = 3
        base_wait = 2
        
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
                        print(f"[GROQ RATE LIMIT] Retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})...")
                        time.sleep(wait_time)
                        continue
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
                
                filename = f"briefing_{name.replace(' ', '_').lower()}_{datetime.now().strftime('%Y-%m-%d')}.md"
                self.file_tool.save_briefing(filename, normalized, OUTPUT_DIR)
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
        
        final_briefing_content = ""  # Store briefing from save_briefing tool call
        
        # SYSTEM INSTRUCTIONS FOR GROQ
        system_message = f"""You are an Executive Briefing Specialist AI. Your task is to research a person and create an executive briefing.

REQUIREMENTS:
1. Use tavily_search to find information about the person
2. Use jina_scrape to read the best URLs found in search results (2-3 URLs maximum)
3. After gathering information, ALWAYS call the save_briefing tool with the complete briefing
4. CRITICAL: Use ONLY the information from the tool results (scraped web content) in your briefing
5. Do NOT use training data - base EVERY fact on the scraped research provided
6. IMPORTANT: You MUST call save_briefing when ready - do NOT just generate text

BRIEFING STRUCTURE (use these EXACT headers):
# Executive Briefing: [Person Name]

## Who They Are
[1-2 sentences from scraped research about their role and background]

## What They Care About
[1-2 sentences from scraped research about their interests and focus areas]

## Current Company Situation
[1-2 sentences from scraped research about their company and current status]

## Meeting Approach
[1-2 sentences from scraped research about how to approach them]

## Smart Questions to Ask
[1-2 sentences with suggested questions based on scraped research]

## Things to Avoid
[1-2 sentences from scraped research about what to avoid]

## Icebreaker / Common Ground
[1-2 sentences from scraped research for starting the conversation]

CRITICAL: When you have gathered enough information, call save_briefing function with:
- content: the complete briefing markdown (all 8 sections, based ONLY on scraped research)
- name: the person's full name

REMINDER: Use ONLY the scraped web content provided in tool results. Do NOT rely on training data."""
        
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

YOUR TASK:
1. Search for information (call tavily_search 1-2 times)
2. Scrape URLs (call jina_scrape 2-3 times with URLs from search results)
3. Read the information you gathered
4. Create the briefing with these EXACT section headers:
   - # Executive Briefing: {person.name}
   - ## Who They Are
   - ## What They Care About
   - ## Current Company Situation
   - ## Meeting Approach
   - ## Smart Questions to Ask
   - ## Things to Avoid
   - ## Icebreaker / Common Ground
5. Call save_briefing with content and name

IMPORTANT: You MUST call save_briefing at the end. Do not just output text. Use the save_briefing function."""

        self.messages = [
            {"role": "user", "content": initial_prompt}
        ]
        
        # Agentic loop
        loop_count = 0
        max_loops = 5  # Reduced - should be able to complete in 2-3 loops
        max_msg_history = 4  # Keep only most recent messages to minimize payload
        
        while loop_count < max_loops:
            loop_count += 1
            print(f"[LOOP {loop_count}] Calling Groq...")
            
            # Trim messages to prevent payload too large errors
            msgs_to_send = self.messages[-max_msg_history:] if len(self.messages) > max_msg_history else self.messages
            
            # Pass system message on EVERY call
            response = self._call_groq_with_tools(msgs_to_send, tools, system_message)
            
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
                
                return briefing
            
            # Execute tool calls
            print(f"[TOOLS] Executing {len(tool_calls)} tool calls...")
            tool_results = []
            
            for tool_call in tool_calls:
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
            scraped_text = "\n\n".join([
                f"SOURCE: {s.url}\nCONTENT: {s.content[:2000]}"
                for s in self.scraped_contents
                if s.content and len(s.content) > 100
            ])
            
            print(f"[DEBUG SYNTHESIS] {len(self.scraped_contents)} sources, {len(scraped_text)} total chars collected")
            if len(scraped_text) < 500:
                print("[WARNING] Very little research content - briefing may be low quality")
            print(f"[DEBUG TOTAL CONTENT] {total_scrape_chars} chars of research now in messages sent to Groq")
            
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
