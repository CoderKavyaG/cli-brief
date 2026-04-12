# Meeting Intelligence Agent

**Research anyone before a meeting in 60 seconds—get executive briefings with sources from LinkedIn, Twitter, GitHub, personal sites, and company data.**

![Meeting Intelligence Agent](https://img.shields.io/badge/Status-Production%20Ready-green?style=flat-square) ![Python 3.11](https://img.shields.io/badge/Python-3.11-blue?style=flat-square) ![License MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)

## 🎯 The Problem It Solves

You're about to pitch someone, interview a candidate, or meet a potential partner. You have 60 seconds to research them—but Google won't tell you what they actually care about, what they've built, or their recent moves. You end up scrolling LinkedIn, checking GitHub, finding old blog posts... **wasting 30+ minutes.**

**Meeting Intelligence Agent** automates the entire research process:
- **5-platform deep research**: LinkedIn, GitHub, Twitter, personal websites, company info
- **60-second turnaround**: Real research data in under a minute
- **Executive briefing**: Clean markdown output with sources cited
- **Alert detection**: Flags funding rounds, job changes, new projects
- **Web UI + CLI**: Use it in your browser or from the terminal

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **Runtime** | Python 3.11 |
| **Web Framework** | Flask 3.0 |
| **Search Engine** | Tavily API (free, no credit card) |
| **Web Scraping** | Jina AI + Firecrawl (free tiers) |
| **LLM (optional)** | Groq (llama-3.1-8b-instant) |
| **Deployment** | Railway.app |
| **WSGI Server** | Gunicorn |

## 🚀 Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/CoderKavyaG/cli-brief.git
cd cli-brief
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Get your free API keys (no credit card needed)

#### Tavily Search API
1. Go to https://tavily.com
2. Sign up (free tier = 1,000 searches/month)
3. Copy your API key from the dashboard

#### Firecrawl API
1. Go to https://www.firecrawl.dev
2. Sign up (free tier available)
3. Copy your API key

#### Groq API (Optional - for synthesis)
1. Go to https://groq.com
2. Sign up (free tier = 10 req/min)
3. Copy your API key

### 4. Create `.env` file
```bash
# In the project root directory, create .env with:
TAVILY_API_KEY=tvly-dev-xxxxxx...
FIRECRAWL_API_KEY=fc-xxxxxx...
GROQ_API_KEY=gsk-xxxxxx...
GROQ_MODEL=llama-3.1-8b-instant
```

### 5. Run it!

**Via Web UI:**
```bash
python app.py
# Opens http://localhost:5000
```

**Via CLI:**
```bash
python -m phase1_agent.main "Deepinder Goyal" "CEO" "Zomato" "pitch restaurant analytics"
```

## 📋 Example Usage

### CLI Command
```bash
python -m phase1_agent.main "Satya Nadella" "CEO" "Microsoft" "Cloud partnership discussion"
```

### Output
The system will:
1. ✅ Search LinkedIn for Satya Nadella profiles
2. ✅ Scrape 2 LinkedIn profiles for role, bio, skills, education
3. ✅ Search GitHub for GitHub/dev profiles
4. ✅ Scrape GitHub profiles for programming languages, popular repos
5. ✅ Search Twitter for social media presence
6. ✅ Search Zomato company info for mission, team, funding
7. ✅ Generate audit report showing what was found

**Result:** `briefing_satya_nadella.md` with executive briefing

### What the Output Looks Like

```markdown
# Executive Briefing: Satya Nadella

**Role:** CEO | **Company:** Microsoft
**Meeting Context:** Cloud partnership discussion
**Generated:** April 12, 2026

---

## Research Summary
**Platforms Researched:** 5 platforms
**Data Points Collected:** 10 sources
**Confidence:** HIGH

---

## LinkedIn Profile
- **Current Role:** Chief Executive Officer at Microsoft
- **Location:** Seattle, Washington
- **Bio:** ...

## GitHub
- **Username:** satya-nadella
- **Languages:** C#, Python, TypeScript
- **Popular Repos:** cloud-sdk, arch-innovation-lab

## Twitter/X
- **Handle:** @satyanadella
- **Bio:** CEO at Microsoft | Cloud Enthusiast
- **Recent Tweets:** Discussion on AI, cloud infrastructure

## Company: Microsoft
- **Mission:** Empower every person and organization...
- **Recent Funding:** [Series of cloud investments]
- **Key Products:** Azure, Microsoft 365, Copilot

---

**Sources:** LinkedIn [profile_id], GitHub [username], Twitter [@handle], company.microsoft.com
```

## 📱 Web Interface

1. Navigate to `http://localhost:5000`
2. Fill in the form:
   - **Name:** Person's full name
   - **Role:** Their job title
   - **Company:** Organization name
   - **Context:** Why you're meeting (e.g., "pitch analytics tool")
3. Click "Research" button
4. Get briefing in 60 seconds with clickable source links

## 🚢 Deploy to Railway

### 1. Create Railway account
Go to https://railway.app (sign up with GitHub)

### 2. Create new project
- Click "New Project"
- Select "GitHub Repo"
- Connect your fork of this repo

### 3. Add environment variables
In Railway dashboard:
- Go to your project → Variables
- Add these:
  ```
  TAVILY_API_KEY=tvly-dev-xxxxxx
  FIRECRAWL_API_KEY=fc-xxxxxx
  GROQ_API_KEY=gsk-xxxxxx (optional)
  GROQ_MODEL=llama-3.1-8b-instant
  ```

### 4. Deploy
- Railway auto-deploys on push
- Your app is live at: `https://web-production-xxxxx.up.railway.app`

## 📊 How It Works

```
Input: Person(name, role, company, context)
    ↓
[PlatformCoordinator]
    ↓
┌─────────────────────────────────────┐
│ Specialist Agents (Parallel Ready)  │
├─────────────────────────────────────┤
│ • LinkedInAgent      → 2 profiles   │
│ • GitHub Agent       → 2 profiles   │
│ • TwitterAgent       → 2 profiles   │
│ • PersonalSiteAgent  → 2 websites   │
│ • CompanyAgent       → 2 sources    │
└─────────────────────────────────────┘
    ↓
[Extract Structured Data]
    ↓
[Generate Executive Briefing]
    ↓
Output: Markdown briefing with sources
```

## 🎯 Key Features

- ✅ **Deep Research**: 5 independent platforms researched per person
- ✅ **60-second turnaround**: Full briefing generated in under a minute
- ✅ **Source attribution**: Every fact linked to its source
- ✅ **Web UI + CLI**: Choose your interface
- ✅ **Alert system**: Highlights funding, role changes, new projects
- ✅ **Free tier**: No credit card required for any APIs
- ✅ **Production ready**: Deployed on Railway
- ✅ **Audit reports**: See exactly what was researched

## 📚 Project Structure

```
cli-brief/
├── app.py                      # Flask web UI
├── phase1_agent/
│   ├── main.py                # CLI entry point
│   ├── coordinator.py         # Orchestrates all agents
│   ├── platform_agents.py     # 5 specialist agents
│   ├── models.py              # Data models
│   ├── tools.py               # API integrations
│   ├── config.py              # Configuration
│   └── ...
├── requirements.txt           # Python dependencies
├── Procfile                   # Railway deployment config
├── runtime.txt               # Python version
└── .env                      # API keys (gitignored)
```

## 🔧 Configuration

### Environment Variables

| Variable | Required | Source |
|----------|----------|--------|
| `TAVILY_API_KEY` | ✅ Yes | https://tavily.com |
| `FIRECRAWL_API_KEY` | ✅ Yes | https://www.firecrawl.dev |
| `GROQ_API_KEY` | ⚠️ Optional | https://groq.com |
| `GROQ_MODEL` | ⚠️ Optional | Default: llama-3.1-8b-instant |

### Rate Limits

- **Tavily**: ~15 searches/day (free tier)
- **Firecrawl**: ~50 scrapes/day (free tier)
- **Groq**: 10 requests/minute (free tier)

The system is designed to work within these limits with intelligent retry logic.

## 💡 Tips for Best Results

1. **Provide full names**: "Satya Nadella" gets better results than "Satya"
2. **Be specific about role**: "CEO of Microsoft" better than "software engineer"
3. **Add meeting context**: "cloud partnership" helps filter relevant info
4. **Check sources**: Click source links to verify findings
5. **Use for recent people**: System works best for people with active online presence

## 🐛 Troubleshooting

### "API keys not found"
Make sure `.env` file exists in project root with all required keys:
```bash
ls -la .env  # Should exist
```

### "429 Too Many Requests"
You've hit Tavily rate limit. Wait a few minutes or research fewer people.

### "No results found"
- Check if person/company name is spelled correctly
- Try a more specific search (full name, not nickname)
- Some people may have minimal online presence

### Web UI not loading
```bash
# Check if Flask is running on port 5000
lsof -i :5000

# Kill and restart
python app.py
```

## 🤝 Contributing

Contributions welcome! Areas to improve:

1. **New Platforms**: Add `BlogAgent`, `PodcastAgent`, `PressAgent`
2. **Better Extraction**: Improve data extraction accuracy
3. **Performance**: Parallelize agent execution
4. **UI/UX**: Enhance web interface design
5. **Tests**: Add test coverage

### How to contribute
1. Fork the repo
2. Create a feature branch: `git checkout -b feature/new-agent`
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

MIT License - feel free to use this project for personal or commercial purposes.

## 📞 Support

- **Issues**: Open an issue on GitHub
- **Questions**: Check the FAQ section below

## ❓ FAQ

**Q: Can I use this for recruiting/screening?**
A: Yes, it's perfect for pre-interview research. Just respect candidate privacy.

**Q: How much does this cost to run?**
A: Completely free if you use free API tiers. Tavily free tier gives 1,000 searches/month.

**Q: Can I self-host instead of Railway?**
A: Yes, deploy to any Python-capable server (Heroku, PythonAnywhere, AWS, etc).

**Q: Does it track or store personal data?**
A: No. Research data is only kept in local markdown files. Nothing is shipped to us.

**Q: Why is Groq optional?**
A: The system works with pure data extraction. Groq synthesis is optional if you want AI summaries.

---

## 💬 What People Are Using This For

- **Sales teams**: Researching prospects before calls
- **HR**: Pre-interview candidate research
- **Venture capital**: Due diligence on founders
- **Recruiting**: Understanding candidate background
- **Business development**: Researching partners/acquirers
- **Journalists**: Background research on sources

---

**Made with ❤️ by Kavya Goel**

⭐ If you find this useful, please star the repo!

GitHub: https://github.com/CoderKavyaG/cli-brief

