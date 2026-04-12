from typing import List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict, field
import json

@dataclass
class SearchResult:
    title: str
    url: str
    description: str
    source: str
    
    def to_dict(self):
        return asdict(self)

@dataclass
class ScrapedContent:
    url: str
    title: str
    content: str
    timestamp: str
    
    def to_dict(self):
        return asdict(self)

@dataclass
class Person:
    name: str
    role: str
    company: Optional[str] = None
    context: Optional[str] = None  # Why you're meeting them
    
    def to_dict(self):
        return asdict(self)

@dataclass
class Briefing:
    person: Person
    who_they_are: str
    what_they_care_about: str
    company_situation: str
    meeting_approach: str
    smart_questions: List[str]
    things_to_avoid: List[str]
    icebreaker: str
    sources: List[str]
    timestamp: str
    social_links: Optional[dict] = None  # LinkedIn, Twitter, Instagram, etc.
    social_handles: Optional[dict] = None  # (deprecated - use social_links)
    recent_activity: Optional[List] = None  # (deprecated)
    deep_insights: Optional[dict] = None    # (deprecated)
    alerts: List[dict] = field(default_factory=list)  # Critical meeting intel alerts
    
    def to_markdown(self) -> str:
        """Convert briefing to professional markdown format with table and identity info"""
        md = f"""# {self.person.name}
## {self.person.role} at {self.person.company or 'n/a'}

---

### At a Glance

| Property | Value |
|---|---|
| **Role** | {self.person.role} |
| **Company** | {self.person.company or "Unknown"} |  
| **Context** | {self.person.context or "General meeting"} |
| **Generated** | {self.timestamp} |

---

### Why You're Meeting
> {self.person.context or "No specific context provided"}

---

"""
        
        # Add critical alerts if present
        if self.alerts:
            md += "## 🔔 Critical Meeting Intel\n"
            md += "> Read these before anything else\n\n"
            for alert in self.alerts:
                md += f"**{alert['emoji']} {alert['label']}**\n"
                md += f"{alert['text']}\n"
                md += f"[Source: {alert['source']}]({alert['url']})\n\n"
            md += "---\n\n"
        
        md += f"""### Who They Are

{self.who_they_are}

---

### What They're Working On Right Now

{self.what_they_care_about}

---

### Their Company

{self.company_situation}

---

### How To Approach This Meeting

{self.meeting_approach}

---

### Three Smart Questions

"""
        for i, q in enumerate(self.smart_questions, 1):
            md += f"{i}. {q}\n"
        
        md += "\n---\n\n### Don't Do This\n\n"
        for i, a in enumerate(self.things_to_avoid, 1):
            md += f"{i}. {a}\n"
        
        md += f"\n---\n\n### Icebreaker\n\n{self.icebreaker}\n\n"
        
        # Add social links if available  
        if self.social_links and any(self.social_links.values()):
            md += "---\n\n### Connect With Them\n\n"
            for platform, url in sorted(self.social_links.items()):
                if url:
                    md += f"- **{platform.upper()}**: {url}\n"
            md += "\n"
        
        md += "---\n\n## Research Confidence\n\n"
        md += f"**Sources**: {', '.join(self.sources)}\n"
        
        return md
    
    def to_dict(self):
        return asdict(self)
