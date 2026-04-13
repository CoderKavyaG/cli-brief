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
    footprint: dict = field(default_factory=dict)  # CHANGE 5: Personal site data (photo, bio, email, etc)
    
    def to_markdown(self) -> str:
        """Convert briefing to professional markdown format with photo, table and identity info"""
        
        # CHANGE 3: Photo display with HTML layout if photo_url exists
        photo_html = ""
        if self.footprint and self.footprint.get("photo_url"):
            photo_html = f"""<div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:24px;">
<div>
<h1>{self.person.name}</h1>
<h2>{self.person.role} at {self.person.company or 'n/a'}</h2>
</div>
<img src="{self.footprint['photo_url']}" style="width:80px; height:80px; border-radius:50%; object-fit:cover; border:3px solid #e5e7eb;" onerror="this.style.display='none'"/>
</div>"""
        else:
            photo_html = f"""# {self.person.name}
## {self.person.role} at {self.person.company or 'n/a'}"""
        
        md = photo_html + "\n\n---\n\n"
        
        md += """### At a Glance

| Property | Value |
|---|---|
"""
        md += f"| **Role** | {self.person.role} |\n"
        md += f"| **Company** | {self.person.company or 'Unknown'} |\n"
        md += f"| **Context** | {self.person.context or 'General meeting'} |\n"
        md += f"| **Generated** | {self.timestamp} |\n\n"
        
        md += "---\n\n"
        md += f"### Why You're Meeting\n> {self.person.context or 'No specific context provided'}\n\n---\n\n"
        
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
        
        # CHANGE 3: Add Connect With Them section from footprint and social_links
        has_connect_data = False
        connect_rows = []
        
        if self.footprint:
            if self.footprint.get("linkedin"):
                connect_rows.append(f"| LinkedIn | [{self.footprint.get('handle', 'Profile')}]({self.footprint['linkedin']}) |")
                has_connect_data = True
            if self.footprint.get("github"):
                github_handle = self.footprint['github'].split('/')[-1]
                connect_rows.append(f"| GitHub | [{github_handle}]({self.footprint['github']}) |")
                has_connect_data = True
            if self.footprint.get("twitter"):
                twitter_handle = self.footprint['twitter'].split('/')[-1]
                connect_rows.append(f"| Twitter/X | [@{twitter_handle}]({self.footprint['twitter']}) |")
                has_connect_data = True
            if self.footprint.get("instagram"):
                instagram_handle = self.footprint['instagram'].split('/')[-2]
                connect_rows.append(f"| Instagram | [@{instagram_handle}]({self.footprint['instagram']}) |")
                has_connect_data = True
            if self.footprint.get("personal_site"):
                site_domain = self.footprint['personal_site'].replace('https://', '').replace('http://', '').rstrip('/')
                connect_rows.append(f"| Personal Site | [{site_domain}]({self.footprint['personal_site']}) |")
                has_connect_data = True
            if self.footprint.get("email"):
                connect_rows.append(f"| Email | {self.footprint['email']} |")
                has_connect_data = True
        
        if self.social_links and any(self.social_links.values()):
            for platform, url in sorted(self.social_links.items()):
                if url and platform.lower() not in [r.split('|')[1].strip().lower() for r in connect_rows]:
                    connect_rows.append(f"| {platform.upper()} | {url} |")
                    has_connect_data = True
        
        if has_connect_data:
            md += "---\n\n## Connect With Them\n\n| Platform | Link |\n|----------|------|\n"
            md += "\n".join(connect_rows)
            md += "\n\n"
        
        md += "---\n\n## Research Confidence\n\n"
        md += f"**Sources**: {', '.join(self.sources)}\n"
        
        return md
    
    def to_dict(self):
        return asdict(self)
