import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Groq Configuration
GROQ_MODEL = os.getenv("GROQ_MODEL", "mixtral-8x7b-32768")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Paths
CACHE_DIR = "cache"
OUTPUT_DIR = "output"

# API Endpoints
TAVILY_SEARCH_URL = "https://api.tavily.com/search"
FIRECRAWL_SCRAPE_URL = "https://api.firecrawl.dev/v0/scrape"

# Agent Settings
MAX_SEARCHES = 5
MAX_SCRAPES = 8
SEARCH_TIMEOUT = 10
SCRAPE_TIMEOUT = 15
