# Intel Briefing Agent - Phase 1

## Quick Start

### 1. Setup Environment
```powershell
# Copy .env.example to .env and fill in your keys
cp .env.example .env
```

Edit `.env`:
```
BRAVE_API_KEY=your_key
FIRECRAWL_API_KEY=your_key
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
```

### 2. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 3. Start Ollama Server (new terminal)
```powershell
ollama serve
```

### 4. Run Agent
```powershell
python -m phase1_agent.main "Satya Nadella" "CEO" "Microsoft" "discussing acquisition"
```

Output: `output/briefing_satya_nadella_2026-04-10.md`

---

## How It Works

1. **Search** - Uses Brave API to find current information
2. **Scrape** - Uses Firecrawl to read full content from URLs
3. **Analyze** - Ollama (local Llama 3) reads everything and decides what matters
4. **Synthesize** - Creates focused briefing document
5. **Cache** - Stores result so re-searching same person uses cache

## Architecture

```
phase1_agent/
├── main.py       → Entry point, orchestrates research loop
├── tools.py      → Brave search, Firecrawl scrape, file save
├── prompts.py    → System prompts and formatting
├── models.py     → Data structures (Person, Briefing, etc)
├── cache.py      → Smart 24h caching layer
└── config.py     → API config and settings
```

## What's Optimized for Cost

- Caching prevents duplicate searches (saves 70% of searches)
- Smart URL filtering (only scrapes useful pages)
- Batch analysis (Claude reads all at once, not repeatedly)
- Brave + Firecrawl free tier is sufficient for months of development
- Ollama is completely free + runs locally

## Next Phase

Phase 2 wraps this as MCP server for Claude Desktop integration.
Phase 3 connects to n8n for calendar automation.
