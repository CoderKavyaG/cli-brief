# Multi-Agent Platform-Specific Research Strategy

## Current Status
- **Phase 1 Agent**: Generalist research (searches + scrapes + synthesis)
- **Issue**: Misses platform-specific deep data (LinkedIn bio links, GitHub projects, Twitter engagement)
- **Solution**: Deploy specialized agents for each platform

---

## Proposed Multi-Agent Architecture

```
                    ┌─────────────────────────┐
                    │   Orchestrator Agent    │
                    │  (Route & Synthesize)   │
                    └────────────┬────────────┘
                                 │
                ┌────────────────┼────────────────┐
                │                │                │
        ┌───────▼────────┐ ┌─────▼──────┐ ┌─────▼──────┐
        │ LinkedInAgent  │ │ GitHubAgent│ │ TwitterAgent│
        │  (Deep Profile)│ │(Projects & │ │(Thoughts & │
        │  • Job History │ │  Code)     │ │ Engagement)│
        │  • Skills      │ │  • Repos   │ │  • Tweets  │
        │  • Bio Links   │ │  • Stars   │ │  • Followers
        │  • Endorsements│ │  • Contrib │ │ • Interests │
        └────────────────┘ └────────────┘ └────────────┘
                │                │                │
        ┌───────▼────────┐ ┌─────▼──────┐ ┌─────▼──────┐
        │ PersonalSite   │ │ CompanyAgent│ │ NewsAgent  │
        │ Agent          │ │ (Company    │ │(Press,     │
        │  • Bio         │ │  Deep Dive) │ │ Mentions)  │
        │  • Social      │ │  • Team     │ │  • Articles│
        │  • Projects    │ │  • Funding  │ │  • Coverage│
        │  • Contact     │ │  • Products │ │  • Awards  │
        └────────────────┘ └────────────┘ └────────────┘
                │                │                │
                └────────────────┼────────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │  Synthesis Agent        │
                    │  (Combine All Findings) │
                    │  • Create Briefing      │
                    │  • Link Intelligence    │
                    │  • Generate Alerts      │
                    └────────────────────────┘
```

---

## Agent Specifications

### 1. **LinkedInAgent**
**Goal**: Extract complete professional profile  
**Searches**:
```
- "{person.name} LinkedIn"
- "site:linkedin.com {person.name}"
```
**Data to Extract**:
- Current role & company
- Job history (dates, titles, descriptions)
- Skills & endorsements
- Education & certifications
- Recommendations
- Bio summary & headline
- Open to work status
- Activity/recent interactions

**Deep Links**:
- Follow bio links to personal site/portfolio
- Scan experience descriptions for company patterns

---

### 2. **GitHubAgent**
**Goal**: Understand technical skills, projects, contributions  
**Searches**:
```
- "site:github.com {person.name}"
- "{person.name} github repositories"
```
**Data to Extract**:
- Profile bio & location
- Public repositories (stars, forks, language)
- Contribution activity (commits, PR reviews)
- Technical skills (by language distribution)
- Open source involvement
- Gists & code snippets
- Followers & following

**Deep Links**:
- Check README files for projects
- Analyze recent commits for current work
- Follow links to deployed projects

---

### 3. **TwitterAgent**
**Goal**: Understand thoughts, expertise, network, engagement  
**Searches**:
```
- "site:twitter.com {person.name}"
- "{person.name} @twitter"
```
**Data to Extract**:
- Bio (concise expertise indicator)
- Tweet topics & themes (last 50 tweets)
- Engagement metrics (likes, retweets, replies)
- Followers count & quality
- Following (who do they follow?)
- Responses to major events/news
- Personal interests & opinions

**Deep Links**:
- Identify key topics they discuss
- Find linked URLs in tweets
- Track recent retweets for interests

---

### 4. **PersonalSiteAgent**
**Goal**: Self-presentation, portfolio, values  
**Searches**:
```
- "{person.name} site"
- "link from ':{person.linkedin_url}'"
```
**Data to Extract**:
- "About" page (mission, background)
- Project portfolio
- Blog posts (topics, frequency)
- Contact info & social links
- Resume/CV
- Speaking engagements
- Publications

**Deep Links**:
- Follow to blog (content analysis)
- Download & scan resume
- Visit linked projects/companies

---

### 5. **CompanyAgent**
**Goal**: Company context, culture, position  
**Searches**:
```
- "{company.name} about"
- "{company.name} team"
- "{company.name} LinkedIn"
```
**Data to Extract**:
- Company mission & values
- Team structure (find person in org)
- Funding & growth stage
- Products/services
- Recent news & press
- Company culture signals
- Innovation areas

**Deep Links**:
- Find person's role in company hierarchy
- Understand company challenges they might address
- Check recent company announcements

---

### 6. **NewsAgent**
**Goal**: Recent activity, mentions, achievements  
**Searches**:
```
- "{person.name}" news 2024 2025 2026
- "{person.name}" achievement award recognition
- "{person.name}" announcement launch
```
**Data to Extract**:
- Press mentions
- Speaking engagements
- Published interviews
- Awards & recognition
- Product launches
- Company announcements
- Recent activity

**Deep Links**:
- Read full articles for context
- Check publication dates & credibility
- Find direct quotes

---

### 7. **SynthesisAgent**
**Goal**: Combine all findings into executive briefing  
**Inputs**: Data from all 6 agents  
**Process**:
```
1. Deduplicate findings
2. Cross-reference to verify facts
3. Create timeline of key events
4. Identify key themes & interests
5. Detect alerts (role changes, funding, launches)
6. Generate smart questions
7. Identify meeting approach
```
**Output**: Executive briefing with full context

---

## Implementation Phases

### Phase 1: Build Agent Infrastructure
- Create `BaseAgent()` class with common scraping/searching
- Implement agent result structure
- Create async execution framework
- Test with single agent first (LinkedIn)

### Phase 2: Specialized Agents
- Implement LinkedIn, GitHub, Twitter agents
- Test each independently
- Optimize search queries for coverage
- Handle rate limiting per platform

### Phase 3: Company & News Agents
- Build company research module
- Implement news detection
- Add alert triggers

### Phase 4: Synthesis & Orchestration
- Build orchestrator to manage all agents
- Implement result merging
- Create final briefing generation
- Add confidence scoring

### Phase 5: Audit & Optimization
- Full project audit (test on 10+ people)
- Performance metrics
- Quality scoring
- Edge case handling

---

## Expected Improvements

| Area | Current | Target |
|------|---------|--------|
| **Data Sources Found** | 2-3 | 8-12 |
| **Depth of Info** | Shallow | Multi-layered |
| **LinkedIn Profile Found** | 60% | 95% |
| **Bio/Personal Site Found** | 20% | 85% |
| **Relevant Alerts** | 30% accurate | 90% accurate |
| **Research Time** | 30-60s | 120-180s |
| **Briefing Quality Score** | 6/10 | 9/10 |

---

## Quick Start: LinkedIn Agent First

```python
# phase1_agent/agents/linkedin_agent.py
class LinkedInAgent:
    def search_profile(self, person_name: str):
        """Search for LinkedIn profile"""
        queries = [
            f'"{person_name}" site:linkedin.com/in/',
            f'{person_name} LinkedIn profile',
        ]
        
    def scrape_profile(self, url: str):
        """Extract all profile data"""
        # Use Jina to get profile HTML
        # Parse job history, skills, bio
        # Extract all linked URLs in bio
        
    def extract_deep_links(self, bio: str):
        """Find & follow links in bio"""
        # Personal site
        # Portfolio
        # Social media
        # Contact info

if __name__ == "__main__":
    agent = LinkedInAgent()
    agent.search_profile("Kavya Goel")
```

---

## Files to Create/Modify

```
phase1_agent/
├── agents/
│   ├── __init__.py
│   ├── base_agent.py          (NEW)
│   ├── linkedin_agent.py       (NEW)
│   ├── github_agent.py         (NEW)
│   ├── twitter_agent.py        (NEW)
│   ├── personal_site_agent.py  (NEW)
│   ├── company_agent.py        (NEW)
│   ├── news_agent.py           (NEW)
│   └── synthesis_agent.py      (NEW)
├── orchestrator.py             (NEW)
├── main.py                      (MODIFY - add orchestrator mode)
└── ...existing files...
```

---

## Success Metrics

After implementation, re-test with "Kavya Goel" and verify:

✅ LinkedIn profile found with all job history  
✅ Personal site (coderkavyag.me) discovered  
✅ GitHub projects & skills identified  
✅ Twitter engagement analyzed  
✅ DevLearn company info gathered  
✅ Complete briefing with 8+ sources  
✅ No generic tech news contamination  
✅ Accurate founding member status identified

---

## Next Steps

1. Finalize this architecture ✓
2. Implement BaseAgent class
3. Test LinkedInAgent independently
4. Integrate & chain agents
5. Full project audit
6. Deploy to Railway

