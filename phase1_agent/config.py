import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")

# Ollama Configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

# Paths
CACHE_DIR = "cache"
OUTPUT_DIR = "output"

# API Endpoints
BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"
FIRECRAWL_SCRAPE_URL = "https://api.firecrawl.dev/v0/scrape"
OLLAMA_GENERATE_URL = f"{OLLAMA_BASE_URL}/api/generate"

# Agent Settings
MAX_SEARCHES = 5
MAX_SCRAPES = 8
SEARCH_TIMEOUT = 10
SCRAPE_TIMEOUT = 15
