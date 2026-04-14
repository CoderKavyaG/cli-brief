"""
IntelAgent: Research orchestrator using Google Gemini 2.5 Flash with Groq fallback
"""

import os
import re
import requests
import time
from datetime import datetime
from .researcher import Researcher


class IntelAgent:
    """Main research orchestrator with hybrid LLM fallback"""
    
    def __init__(self):
        self.researcher = Researcher()
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.gemini_url = (
            "https://generativelanguage.googleapis.com/v1/"
            "models/gemini-2.5-flash-lite:generateContent"
        )
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.groq_url = "https://api.groq.com/openai/v1/chat/completions"
    
    def research(self, name: str, role: str, company: str, 
                 context: str, rejected_urls: list = None) -> dict:
        """
        Main research method.
        
        Args:
            name: Person's name
            role: Person's role
            company: Company/institution
            context: Meeting context
            rejected_urls: List of previously tried URLs to skip (for research again)
        
        Returns dict with all briefing data.
        """
        if rejected_urls is None:
            rejected_urls = []
        
        print(f"\n{'='*60}")
        print(f"RESEARCHING: {name} ({role} at {company})")
        print(f"Context: {context}")
        if rejected_urls:
            print(f"REJECTING: {len(rejected_urls)} previous attempts")
        print(f"{'='*60}\n")
        
        # Step 1: Find person and lock identity
        print("[STEP 1] Finding digital footprint...")
        identity = self.researcher.find_person(name, company, role, rejected_urls)
        
        if not identity["verified"]:
            print("[WARNING] Could not lock identity — proceeding with caution")
        
        # Step 2: Scrape all sources
        print("[STEP 2] Scraping sources...")
        sources = self.researcher.scrape_all(identity, name, company)
        
        if not sources:
            print("[ERROR] No sources scraped! Cannot proceed.")
            print("[DEBUG] Check:")
            print(f"  1. Is TAVILY_API_KEY set? {bool(os.getenv('TAVILY_API_KEY'))}")
            print(f"  2. Did find_person lock identity? {identity.get('verified')}")
            print(f"  3. Are there URLs to scrape? {any(identity.values())}")
        
        # Step 3: Search for recent news
        print("[STEP 3] Searching for recent news...")
        news_results = self.researcher.search.search(
            f'"{name}" "{company}" 2025 OR 2026 OR latest OR recent', 
            count=3
        )
        
        # Compile research text for Claude
        research_text = self._compile_research(
            sources, news_results, name, company
        )
        
        # Step 4: Synthesize with Claude Haiku
        print("[STEP 4] Synthesizing with Claude Haiku 4.5...")
        briefing = self._synthesize(
            name, role, company, context, 
            identity, sources, research_text
        )
        
        return briefing
    
    def _compile_research(self, sources, news_results, name, company):
        """Compile all research into text for Claude"""
        
        research_text = ""
        
        # Add scraped sources
        for i, source in enumerate(sources, 1):
            domain = source["url"].split("/")[2].replace("www.", "")
            research_text += f"\n\n=== SOURCE {i}: {domain.upper()} ===\n"
            research_text += f"URL: {source['url']}\n\n"
            research_text += source["content"][:3000]
        
        # Add recent news snippets
        if news_results:
            research_text += "\n\n=== RECENT NEWS ===\n"
            for r in news_results:
                research_text += f"- [{r['title']}]({r['url']})\n"
                research_text += f"  {r['content'][:200]}...\n\n"
        
        return research_text
    
    def _synthesize(self, name, role, company, context, 
                    identity, sources, research_text) -> dict:
        """Synthesize briefing using Groq (primary) with Gemini fallback"""
        
        has_research = len(research_text.strip()) > 300
        confidence = "HIGH" if len(research_text) > 3000 else \
                    "MEDIUM" if len(research_text) > 500 else "LOW"
        
        # Build prompt for synthesis
        prompt = self._build_synthesis_prompt(name, role, company, context, research_text, has_research)
        
        # Try Groq first (more reliable than Gemini for now)
        print("[MODEL] Attempting Groq Llama 3.3...")
        raw_response = self._synthesize_with_groq(prompt)
        
        if raw_response:
            print(f"[GROQ SUCCESS] Got {len(raw_response)} chars")
        else:
            # Fallback to Gemini
            print("[FALLBACK] Groq failed, trying Gemini...")
            result = self._try_gemini(prompt)
            if result:
                raw_response = result
                print(f"[GEMINI SUCCESS] Got {len(raw_response)} chars")
            else:
                raise Exception("Both Groq and Gemini failed")
        
        # Parse the structured response
        parsed = self._parse_response(raw_response)
        
        return {
            "name": name,
            "role": role,
            "company": company,
            "context": context,
            "confidence": confidence,
            "identity": identity,
            "photo_url": identity.get("photo_url"),
            "linkedin_handle": identity.get("handle"),
            "who_they_are": parsed.get("WHO_THEY_ARE", "[Not found in research]"),
            "what_they_care_about": self._parse_list(
                parsed.get("WHAT_THEY_CARE_ABOUT", "")
            ),
            "company_situation": parsed.get(
                "COMPANY_SITUATION", "[Not found in research]"
            ),
            "meeting_approach": parsed.get(
                "MEETING_APPROACH", "[Not found in research]"
            ),
            "smart_questions": self._parse_list(
                parsed.get("SMART_QUESTIONS", "")
            ),
            "icebreaker": parsed.get("ICEBREAKER", "[Not found in research]"),
            "sources": [s["url"] for s in sources],
            "timestamp": datetime.now().isoformat()
        }
    
    def _build_synthesis_prompt(self, name, role, company, context, research_text, has_research):
        """Build the synthesis prompt"""
        return f"""You are writing an executive briefing for a business meeting.

PERSON TO RESEARCH:
Name: {name}
Role: {role}
Company: {company}
Meeting context: {context}

RESEARCH DATA (use ONLY this information — no prior knowledge or training data):
{research_text if has_research else "[NO RESEARCH DATA FOUND]"}

YOUR TASK: Write a complete, verified executive briefing using ONLY the research above.

CRITICAL RULES:
1. Every sentence must be COMPLETE — never cut off mid-thought
2. Use ONLY facts from the research data above
3. After each specific fact, write the source domain like [domain.com]
4. If you cannot find data for a section, write exactly: [Not found in research]
5. Never use information about other people — ONLY {name}
6. Smart questions must reference specific things you found in research
7. Icebreaker must reference ONE specific real thing from the research
8. End every section with a period

WRITE IN THIS FORMAT (complete each section fully):

WHO_THEY_ARE:
[2-3 complete sentences about {name} as a real person. Include their background, role, and what makes them unique. End with a period.]

WHAT_THEY_CARE_ABOUT:
[Write 4 bullet points. Each point should be a complete sentence with a specific thing they care about, based on research. Include source domains.]

COMPANY_SITUATION:
[2-3 complete sentences about {company}. Include specific numbers, status, recent announcements if found. End with a period.]

MEETING_APPROACH:
[3 specific tactical tips for approaching THIS meeting about "{context}". Each tip must be a complete sentence based on research findings. End with periods.]

SMART_QUESTIONS:
[Write 3 numbered questions. Each must be specific and personalized based on research. No generic questions. Each ends with ?]

ICEBREAKER:
[One specific, genuine thing from research that shows you've done homework. Quote something real or reference a specific achievement. Must be engaging and end with ? or !]

Now write the complete briefing. Do not truncate. Do not use template language."""

    def _try_gemini(self, prompt):
        """Try Gemini with exponential backoff for rate limits"""
        max_retries = 2
        
        for attempt in range(max_retries):
            try:
                payload = {
                    "contents": [{
                        "parts": [{"text": prompt}]
                    }],
                    "generationConfig": {
                        "maxOutputTokens": 2000
                    }
                }
                
                response = requests.post(
                    f"{self.gemini_url}?key={self.gemini_key}",
                    headers={"Content-Type": "application/json"},
                    json=payload,
                    timeout=30
                )
                
                # Check for rate limit
                if response.status_code == 429:
                    print(f"[GEMINI 429] Rate limited (attempt {attempt+1}/{max_retries})")
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s
                        print(f"[BACKOFF] Waiting {wait_time}s before retry...")
                        time.sleep(wait_time)
                        continue
                    return None  # Failed after retries
                
                response.raise_for_status()
                data = response.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]
                
            except requests.exceptions.HTTPError as e:
                if response.status_code == 429:
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt
                        print(f"[BACKOFF] Waiting {wait_time}s before retry...")
                        time.sleep(wait_time)
                        continue
                    return None
                else:
                    print(f"[GEMINI ERROR] {response.status_code}: {response.text[:100]}")
                    return None
            except Exception as e:
                print(f"[GEMINI EXCEPTION] {str(e)[:100]}")
                return None
        
        return None
    
    def _synthesize_with_groq(self, prompt):
        """Fallback: Use Groq API for synthesis"""
        try:
            response = requests.post(
                self.groq_url,
                headers={
                    "Authorization": f"Bearer {self.groq_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 2000,
                    "temperature": 0.7
                },
                timeout=30
            )
            
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
            
        except requests.exceptions.HTTPError as e:
            print(f"[GROQ ERROR] {response.status_code}: {response.text[:100]}")
            return None
        except Exception as e:
            print(f"[GROQ EXCEPTION] {str(e)[:100]}")
            return None
    
    def _parse_response(self, text: str) -> dict:
        """Parse Claude's structured response"""
        
        sections = [
            "WHO_THEY_ARE", "WHAT_THEY_CARE_ABOUT",
            "COMPANY_SITUATION", "MEETING_APPROACH",
            "SMART_QUESTIONS", "ICEBREAKER"
        ]
        
        parsed = {}
        
        for i, section in enumerate(sections):
            # Find section header
            pattern = f"{section}:\\s*(.*?)(?={'|'.join(sections[i+1:] if i+1 < len(sections) else [])}|$)"
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            
            if match:
                content = match.group(1).strip()
                parsed[section] = content
            else:
                parsed[section] = "[Not found in research]"
        
        return parsed
    
    def _parse_list(self, text: str) -> list:
        """Parse list items from text"""
        
        if not text or "[Not found" in text:
            return ["[Not found in research]"]
        
        # Split by newlines
        lines = text.split("\n")
        items = []
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 5:
                continue
            
            # Remove numbering, bullets, dashes
            clean = re.sub(r'^[\d\.\)\-\*\•\s]+', '', line)
            
            if clean and len(clean) > 5:
                items.append(clean)
        
        return items if items else ["[Not found in research]"]
