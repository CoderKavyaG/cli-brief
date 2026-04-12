# Meeting Intelligence Agent - API Documentation

## Base URL
```
http://localhost:5000
https://yourdomain.com  # Production
```

## Authentication
Current version supports no auth. Production deployments should add API key authentication.

---

## Endpoints

### 1. Health Check
```
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "groq_api": "connected",
  "tavily_api": "connected",
  "uptime_seconds": 3600,
  "timestamp": "2026-04-12T10:30:00Z"
}
```

**Use For:** Monitoring, load balancer health checks

---

### 2. Research & Generate Briefing
```
POST /research
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "Deepinder Goyal",
  "role": "CEO",
  "company": "Blinkit",
  "context": "Pitch supply chain optimization tool"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "html": "<h1>Executive Briefing: Deepinder Goyal</h1>...",
  "markdown": "# Executive Briefing: Deepinder Goyal\n\n## Who They Are\n...",
  "person": "Deepinder Goyal",
  "company": "Blinkit",
  "context": "Pitch supply chain optimization tool",
  "alerts": [
    {
      "type": "role_change",
      "emoji": "🚨",
      "label": "ROLE CHANGE DETECTED",
      "text": "Deepinder Goyal stepped down as CEO in February 2026",
      "source": "en.wikipedia.org",
      "url": "https://en.wikipedia.org/wiki/Deepinder_Goyal"
    },
    {
      "type": "funding",
      "emoji": "💰",
      "label": "FUNDING EVENT",
      "text": "Blinkit raised $100+ million in Series funding",
      "source": "techcrunch.com",
      "url": "https://techcrunch.com/2026/blinkit-funding"
    }
  ]
}
```

**Response (400 Bad Request):**
```json
{
  "error": "All fields are required"
}
```

**Response (500 Server Error):**
```json
{
  "error": "Research failed - Groq API returned 429 Too Many Requests"
}
```

**Response Time:** 60-120 seconds (depends on Groq rate limiting)

**Use For:** Generating briefings, getting alerts, exporting

---

### 3. Download Briefing (Future)
```
GET /download/<filename>
```

**Response:** File download (markdown or HTML)

---

## Request/Response Examples

###Example 1: CEO Research
```bash
curl -X POST http://localhost:5000/research \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Satya Nadella",
    "role": "CEO",
    "company": "Microsoft",
    "context": "Cloud partnership discussion"
  }' \
  --max-time 180
```

### Example 2: HR Manager Research
```bash
curl -X POST http://localhost:5000/research \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sarah Chen",
    "role": "Head of Talent",
    "company": "Google India",
    "context": "Pitch employee wellness platform"
  }'
```

### Example 3: Python Client
```python
import requests
import json

response =requests.post('http://localhost:5000/research', json={
    'name': 'Priya Kapoor',
    'role': 'Founder',
    'company': 'CloudSync',
    'context': 'Cloud infrastructure partnership'
}, timeout=180)

if response.status_code == 200:
    briefing = response.json()
    print(f"Found {len(briefing['alerts'])} alerts")
    print(briefing['markdown'])
    
    # Save to file
    with open(f"briefing_{briefing['person']}.md", 'w') as f:
        f.write(briefing['markdown'])
else:
    print(f"Error: {response.json()['error']}")
```

### Example 4: Batch Processing
```python
import requests
import time

people = [
    {"name": "Deepinder Goyal", "role": "CEO", "company": "Blinkit", "context": "Partnership"},
    {"name": "Priya Kapoor", "role": "Founder", "company": "CloudSync", "context": "Cloud"},
    {"name": "Rohan Sharma", "role": "Student", "company": "IIT Delhi", "context": "Hackathon"}
]

for person in people:
    response = requests.post('http://localhost:5000/research', json=person, timeout=180)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ {person['name']}: {len(data['alerts'])} alerts")
        
        # Save briefing
        with open(f"output/{person['name']}.md", 'w') as f:
            f.write(data['markdown'])
    else:
        print(f"✗ {person['name']}: {response.json()['error']}")
    
    # Rate limiting: wait 5 seconds between requests
    time.sleep(5)
```

---

## Alert Types

### 1. Role Changes 🚨
**Type:** `role_change`  
**Triggered by:** CEO announcements, stepping down, promotions, appointments  
**Example:** "Deepinder Goyal stepped down as CEO"

### 2. Funding Events 💰
**Type:** `funding`  
**Triggered by:** Series funding, IPO, acquisitions, valuations  
**Example:** "Blinkit raised $100+ million in Series C"

### 3. Controversy ⚠️
**Type:** `controversy`  
**Triggered by:** Lawsuits, fraud allegations, scandals, prominent departures  
**Example:** "CEO fired following fraud investigation"

### 4. Product Launches 🚀
**Type:** `launch`  
**Triggered by:** New announcements, releases, unveilings  
**Example:** "Company launched new cloud platform"

---

## Response Formatting

### Markdown Format
Includes:
- Title and metadata
- Critical alerts (if any)
- Who They Are
- What They Care About
- Current Company Situation
- Meeting Approach
- Smart Questions
- Things to Avoid
- Icebreaker
- Source citations

### HTML Format
Same content as markdown, converted to styled HTML with:
- Colored alert boxes
- Source badges
- Confidence indicator
- Responsive design

---

## Error Codes & Handling

| Code | Error | Cause | Solution |
|------|-------|-------|----------|
| 400 | "All fields are required" | Missing name/role/company/context | Fill all fields |
| 429 | "Too Many Requests" | Groq API rate limited | Wait 60s, retry |
| 500 | "Research failed - insufficient data" | Person too obscure | Try different name spelling |
| 500 | "Briefing file not created" | Groq synthesis failed | Check API keys, retry |
| 503 | "Service Unavailable" | Tavily/Groq API down | Check status pages, retry |

---

## Rate Limiting

Default limits (configurable):
- 10 requests per minute (per IP)
- 500 requests per day (per IP)
- 120 second timeout per request

Adjust in `.env`:
```
MAX_REQUESTS_PER_MINUTE=10
MAX_REQUESTS_PER_DAY=500
LLM_TIMEOUT=120
```

---

## Best Practices

1. **Use per-person research** instead of batch with same request timing
2. **Implement retry logic** with exponential backoff (already done server-side for Groq 429)
3. **Cache results** - results are cached by person for 24 hours
4. **Monitor API usage** - check Groq/Tavily quotas daily
5. **Log all requests** for audit trail

---

## Integration Examples

### Slack Bot
```python
from slack_bolt import App
import requests

app = App(token=os.environ["SLACK_BOT_TOKEN"], signing_secret=os.environ["SLACK_SIGNING_SECRET"])

@app.command("/brief")
def handle_brief_command(ack, body):
    ack()
    
    # /brief John Doe CEO Company
    name = body['text'].split()[0]
    
    response = requests.post('http://localhost:5000/research', json={
        'name': name,
        'role': 'Not specified',
        'company': 'Not specified',
        'context': f'Requested by {body["user_id"]}'
    }, timeout=180)
    
    if response.status_code == 200:
        briefing = response.json()
        app.client.chat_postMessage(
            channel=body['channel_id'],
            text=briefing['markdown'],
            thread_ts=body.get('thread_ts')
        )
    else:
        app.client.chat_postMessage(
            channel=body['channel_id'],
            text=f"Error: {response.json()['error']}"
        )
```

### Salesforce Integration
See `salesforce_integration.py` for complete example

### Zapier/Make.com
Use POST endpoint directly in their interfaces

---

## Support
- **API Issues:** POST to `/issues` endpoint or GitHub Issues
- **Rate Limit Help:** Check `X-RateLimit-Remaining` header
- **Monitoring:** See `/health` endpoint for service status

