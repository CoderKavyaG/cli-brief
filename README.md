# Meeting Intel Agent 🕵️‍♂️

An open-source AI agent that automates deep background research on anyone before you meet them. Give it a name, role, company, and the context of your meeting, and it will autonomously search the web, scrape their digital footprint (LinkedIn, GitHub, Twitter, Personal Sites), synthesize the data, and deliver a comprehensive, fact-checked briefing within 60 seconds.

## Features

- **3-Point Identity Lock**: Uses name, company, and role to cross-reference and verify the target's identity across platforms, preventing wrong-person hallucinations.
- **Deep Digital Footprint Scraping**: Uses Playwright and Jina to bypass blocks and extract content from LinkedIn, GitHub, Twitter, Instagram, and personal websites concurrently.
- **Strict Verification**: LLM synthesis (via Groq/Llama 3.3 and Gemini) is instructed to use *only* scraped data and append inline citations to every factual claim.
- **Actionable Insights**: Generates smart questions, meeting approach tactics, and tailored icebreakers based entirely on verified research.
- **Exportable Briefings**: Instantly download the synthesized briefing as a Markdown file.

## Prerequisites

You need a few free API keys to run this project:
- **Tavily API**: For high-quality web searching (Free tier available)
- **Groq API**: For lightning-fast LLM synthesis (Free tier available)
- **Gemini API**: Used as a reliable fallback for synthesis (Free tier available)

## Quick Start

### 1. Clone & Install Dependencies
Make sure you have Python 3.10+ installed.

```bash
git clone https://github.com/yourusername/meeting-intel-agent.git
cd meeting-intel-agent
pip install -r requirements.txt
```

### 2. Install Playwright Browsers
The agent uses Playwright for robust scraping (e.g., LinkedIn). You need to install the browser binaries:
```bash
playwright install chromium
```

### 3. Setup Environment Variables
Copy the template and add your API keys:
```bash
cp .env.example .env
```
Edit `.env` and fill in your keys:
```env
TAVILY_API_KEY=your_tavily_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
GROQ_API_KEY=your_groq_api_key_here
PORT=5000
```

### 4. Run the Application
Start the Flask application:
```bash
python app.py
```

Then open your browser and navigate to `http://localhost:5000`.

## Architecture Overview

- `app.py`: The lightweight Flask backend and single-page HTML/CSS frontend.
- `phase1_agent/agent.py`: The orchestrator that coordinates research, compilation, and LLM synthesis.
- `phase1_agent/researcher.py`: The identity-locking and web-searching engine using Tavily.
- `phase1_agent/advanced_scraper.py`: Manages concurrent scraping via Playwright, Puppeteer, and Jina Reader.
- `phase1_agent/email_finder.py`: Validates and extracts emails purely from the scraped content.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. If you find a bug, please open an issue.

## License
MIT License. Free for open source use.
