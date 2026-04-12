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
        """Convert briefing to markdown format"""
        md = f"""# Briefing: {self.person.name}

**Role:** {self.person.role}
**Company:** {self.person.company or 'Unknown'}
**Context:** {self.person.context or 'General meeting'}
**Generated:** {self.timestamp}

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
        
        md += """## Who They Are

{who_they_are}

---

## What They Care About Right Now

{what_they_care_about}

---

## Their Company's Current Situation

{company_situation}

---

## How To Approach This Meeting

{meeting_approach}

---

## Three Smart Questions

""".format(
            who_they_are=self.who_they_are,
            what_they_care_about=self.what_they_care_about,
            company_situation=self.company_situation,
            meeting_approach=self.meeting_approach
        )
        for i, q in enumerate(self.smart_questions, 1):
            md += f"{i}. {q}\n"
        
        md += "\n---\n\n## Two Things To Avoid\n\n"
        for i, a in enumerate(self.things_to_avoid, 1):
            md += f"{i}. {a}\n"
        
        md += f"\n---\n\n## Icebreaker\n\n{self.icebreaker}\n\n"
        
        # Add social links if available
        if self.social_links and any(self.social_links.values()):
            md += "---\n\n## Connect With Them\n\n"
            for platform, handles in sorted(self.social_links.items()):
                if handles:
                    for handle in handles[:2]:  # Show top 2
                        md += f"- **{platform.upper()}**: {handle}\n"
            md += "\n"
        
        # Add recent activity if available
        if self.recent_activity:
            md += "---\n\n## Recent Activity\n\n"
            for activity in self.recent_activity:
                md += f"- {activity}\n"
            md += "\n"
        
        md += "---\n\n## Sources\n\n"
        for source in self.sources:
            md += f"- {source}\n"
        
        return md
    
    def to_dict(self):
        return asdict(self)
