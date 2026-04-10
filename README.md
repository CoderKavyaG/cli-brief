# Intel Briefing Agent - Phase 1

## Quick Start

### 1. Setup Environment
```powershell
# Copy .env.example to .env and fill in your keys
cp .env.example .env
```

Edit `.env`:
```
TAVILY_API_KEY=your_tavily_key
FIRECRAWL_API_KEY=your_firecrawl_key
GROQ_API_KEY=your_groq_key
GROQ_MODEL=mixtral-8x7b-32768
```

### 2. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 3. Run Agent
```powershell
python -m phase1_agent.main "Kavya Goel" "Student" "Chitkara University" "networking meeting"
```

Output: `output/briefing_kavya_goel_2026-04-10.md`

---

## How It Works

1. **Search** - Tavily API finds real information (fast, free)
2. **Analyze** - Groq LLM decides which URLs to read
3. **Scrape** - Firecrawl reads full page content
4. **Synthesize** - Creates focused briefing document
5. **Cache** - Stores result so re-searching same person uses cache

## Architecture

```
phase1_agent/
├── main.py       → Entry point, orchestrates research loop
├── tools.py      → Tavily search, Firecrawl scrape, file save
├── prompts.py    → System prompts and formatting
├── models.py     → Data structures (Person, Briefing, etc)
├── cache.py      → Smart 24h caching layer
└── config.py     → API config and settings
```

## API Stack (Completely Free)

- **Tavily Search** - Real-time web search, 10k searches/month free
- **Firecrawl** - Web scraping, 500 scrapes/month free  
- **Groq** - Lightning-fast LLM, 10k tokens/day free

## What's Optimized for Cost

- Caching prevents duplicate searches (saves 70%)
- Smart URL filtering (only scrapes valuable pages)
- Groq is 10x faster than local LLMs, free tier sufficient
- Batch analysis (Claude reads all at once)

## Testing Commands

```powershell
# Test Tavily Search + Firecrawl
python -m phase1_agent.tools

# Test full agent with real person
python -m phase1_agent.main "Name" "Role" "Organization" "Context"

# View cache
cat cache/briefings_cache.json
```

## Next Phase

Phase 2 wraps this as MCP server for Claude Desktop integration.
Phase 3 connects to n8n for calendar automation.

