# Phase 2: MCP Server Setup

The intel agent is now available as a Model Context Protocol (MCP) server. This enables Claude Desktop to call the agent directly for research.

## Quick Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Claude Desktop

Edit your Claude Desktop configuration file:
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`  
- **Mac**: `~/Library/Application Support/Claude/claude_desktop_config.json`  
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

Add this MCP server configuration:

```json
{
  "mcpServers": {
    "intel-agent": {
      "command": "python",
      "args": ["/path/to/intel-agent/run_mcp_server.py"],
      "env": {
        "TAVILY_API_KEY": "your_tavily_api_key",
        "FIRECRAWL_API_KEY": "your_firecrawl_api_key",
        "GROQ_API_KEY": "your_groq_api_key"
      }
    }
  }
}
```

Replace `/path/to/intel-agent/` with the actual path to this project directory.

### 3. Restart Claude Desktop

After updating the config, restart Claude Desktop. You should see the intel-agent in the available tools.

## Usage in Claude Desktop

In any conversation with Claude, you can now ask it to research people:

```
Can you research Jane Doe, VP at Google, who I'm meeting tomorrow?
```

Claude will:
1. Extract the person details
2. Call the intel-agent MCP tool
3. Generate a comprehensive briefing
4. Present it formatted in the conversation

## Available Tool

### `research_briefing`

Generate intel briefing for a person.

**Required inputs:**
- `name` - Person's full name
- `role` - Their role/title

**Optional inputs:**
- `company` - Their company/organization
- `context` - Why you're meeting them (meeting context)

**Returns:** Markdown-formatted briefing with:
- Who they are
- What they care about
- Company situation
- Meeting approach
- Smart questions to ask
- Things to avoid
- Icebreaker suggestions

## Troubleshooting

### MCP server not connecting

1. Verify Python path is correct in config
2. Check env variables are set (API keys)
3. Run `python run_mcp_server.py` manually to test
4. Check Claude Desktop logs: `%(APPDATA)%\Claude\logs`

### Research quality issues

- Ensure `.env` file has valid API keys
- Check network connectivity
- Test Phase 1 agent manually: `python -m phase1_agent.main "name" "role"`

### Cache not working

Cache is stored in `cache/briefings_cache.json` and expires after 24 hours.
To clear: `rm cache/briefings_cache.json`
