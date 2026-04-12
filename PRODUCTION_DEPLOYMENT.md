# Meeting Intelligence Agent - Production Deployment Guide

## Overview
The Meeting Intelligence Agent is a production-ready Python/Flask application that researches people and generates executive briefings with critical alert detection for B2B sales and corporate meetings.

**Version:** 1.0.0  
**Status:** Production Ready  
**Date:** April 12, 2026

---

## Quick Start

### Minimum Requirements
- **Python:** 3.10+
- **Memory:** 2GB RAM minimum (4GB recommended)
- **Storage:** 5GB for briefing cache
- **Internet:** Required for API calls (Groq, Tavily, Firecrawl)

### API Keys Required
```
GROQ_API_KEY          # For LLM synthesis
TAVILY_SEARCH_API_KEY # For web search
FIRECRAWL_API_KEY     # For web scraping (optional, falls back to Jina)
```

### Installation (5 minutes)

```bash
# Clone and setup
git clone https://github.com/CoderKavyaG/cli-brief.git
cd "cli-brief"

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GROQ_API_KEY="your_key_here"
export TAVILY_SEARCH_API_KEY="your_key_here"
export FIRECRAWL_API_KEY="your_key_here"  # Optional

# Run web UI
python app.py

# Or run CLI
python -m phase1_agent.main "Person Name" "Title" "Company" "Meeting Context"
```

Open http://localhost:5000 in your browser.

---

## Features Summary

### ✅ Core Capabilities
- **Research**: Finds 2-3 authoritative sources per person automatically
- **Synthesis**: Generates 500-1000 word executive briefings
- **Alerts**: Detects 4 types of critical events (role changes, funding, controversy, launches)
- **Citations**: Every fact tagged with [Source: domain.com]
- **Download**: Export briefings as markdown or HTML
- **Web UI**: Form-based interface for non-technical users
- **CLI**: Command-line access for integration

### 🎯 Alert Types
- 🚨 **Role Changes**: CEO announcements, stepping down, appointments
- 💰 **Funding Events**: Series funding, IPOs, acquisitions, valuations  
- ⚠️ **Controversy**: Lawsuits, fraud allegations, prominent departures
- 🚀 **Product Launches**: New announcements, releases, unveilings

### 📊 Tested Personas
- ✅ CEOs and Founders (high public profile)
- ✅ HR Managers (internal employees)
- ✅ Students (low public profile)
- ✅ Project Managers (corporate roles)

---

## Deployment Architectures

### Option 1: Single Server (Recommended for <50 users/day)

**Setup:**
```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install python3-pip python3-venv

# Create application user
sudo useradd -m -s /bin/bash briefing-agent
sudo su - briefing-agent

#Clone and install
git clone <repo> && cd cli-brief
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Setup systemd service (see briefing-agent.service below)
```

**Performance:**
- 1-2 min per briefing (depends on Groq rate limiting)
- ~100MB per request (network bandwidth)
- 50 daily requests = ~2.5 hours wall-clock time

### Option 2: Docker + Kubernetes (Scalable for 100+ users/day)

**Using Docker:**
```bash
docker build -t briefing-agent:1.0 .
docker run -e GROQ_API_KEY=$GROQ_KEY \
           -e TAVILY_API_KEY=$TAVILY_KEY \
           -p 5000:5000 \
           briefing-agent:1.0
```

**Using Docker Compose (with Redis cache):**
```bash
docker-compose up -d
```

### Option 3: Managed Cloud (AWS Lambda, GCP Cloud Run, Azure Functions)

**For serverless, use the provided wrapper:**
```python
# See serverless_handler.py
```

---

## Production Configuration

### Environment Variables
```bash
# Required
GROQ_API_KEY              # https://console.groq.com
TAVILY_SEARCH_API_KEY     # https://tavily.com
FIRECRAWL_API_KEY         # https://www.firecrawl.dev (optional)

# Optional
FLASK_ENV                 # Set to 'production'
LOG_LEVEL                 # DEBUG, INFO, WARNING, ERROR
MAX_REQUESTS_PER_DAY      # Rate limit (default: unlimited)
ENABLE_CACHE              # True/False (default: True)
CACHE_EXPIRY_HOURS        # Default: 24
OUTPUT_DIR                # Briefing storage directory
```

### Security Best Practices

1. **API Keys**
   - Use AWS Secrets Manager / Azure Key Vault
   - Never commit keys to Git
   - Rotate keys monthly

2. **Authentication**
   - Add API key authentication to endpoints
   - Implement rate limiting (see Flask-Limiter config)
   - Use HTTPS only in production

3. **Data**
   - Encrypt briefing cache at rest
   - Clear old briefings weekly
   - Audit logs for compliance

4. **Infrastructure**
   - Run behind load balancer (AWS ELB, Nginx)
   - Use WAF (Web Application Firewall)
   - Enable CORS restrictions

### Health Checks

```bash
# Health endpoint
curl http://localhost:5000/health

# Expected response
{  
  "status": "healthy",
  "groq_api": "connected",
  "tavily_api": "connected",
  "uptime_seconds": 3600
}
```

---

## Performance Tuning

### Response Time Optimization
```
Current: 80-120 seconds per briefing
Target: <60 seconds (with parallel requests)

Improvements:
1. Parallel search + scrape: -20s (tavily + firecrawl simultaneously)
2. Groq response caching: -10s (duplicate queries)
3. Synthesis truncation: -5s (1200 char limit already applied)
```

### Memory Management
```
Per request: ~50-100MB
Concurrent capacity: 100 requests / (available_RAM_GB * 10)

Example: 8GB RAM = max 80 concurrent requests
Recommendation: Use connection pooling + request queuing
```

### Database for Production

**Recommended:** PostgreSQL (for caching + audit logs)

```sql
-- Briefing cache table
CREATE TABLE briefing_cache (
    id SERIAL PRIMARY KEY,
    person_hash VARCHAR(32) UNIQUE,
    briefing_json JSONB,
    alerts JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    expired_at TIMESTAMP
);

-- Audit log table
CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100),
    person_researched VARCHAR(255),
    alert_count INT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Monitoring & Alerting

### Key Metrics to Track
```
1. Avg response time: Should be 60-120s
2. Error rate: Should be <1%
3. API quota usage: Monitor Groq/Tavily daily limits
4. Alert detection: % with 1+ alerts (baseline: 30% for public figures)
5. Source quality: % with 3+ sources per briefing
```

### Log Monitoring (via CloudWatch / ELK Stack)
```
Errors to watch for:
- 429 Too Many Requests (Groq rate limit) -> Add backoff
- 403 Unauthorized (API key issue) -> Rotate keys
- 404 Not Found (Website changes) -> Update search queries
- TimeoutError (network) -> Increase timeout to 180s
```

### Alert Thresholds
```
WARNING if:
- Avg response > 150s
- Error rate > 2%
- <50% of briefings have 1+ alert

CRITICAL if:
- API endpoint down
- Error rate > 5%
- 0 successful briefings in last 100 requests
```

---

## Deployment Checklist

### Pre-Production
- [ ] All API keys configured securely
- [ ] Database initialized (if using PostgreSQL)
- [ ] SSL certificate installed
- [ ] CORS/CSRF enabled
- [ ] Rate limiting configured
- [ ] Log aggregation setup
- [ ] Backups configured (daily)
- [ ] Tested with 5+ diverse personas

### Production Launch
- [ ] Load test completed (100+ concurrent requests)
- [ ] Health checks passing
- [ ] Monitoring dashboard created
- [ ] On-call runbook prepared
- [ ] Incident response playbook ready
- [ ] Database backups verified
- [ ] Rollback procedure tested

### Post-Launch
- [ ] Monitor error logs for 24 hours
- [ ] Check API quota usage daily (first week)
- [ ] Alert quality review (false positives?)
- [ ] Response time baseline established
- [ ] User feedback collected

---

## Troubleshooting

### Issue: "429 Too Many Requests"
**Cause:** Groq API rate limiting  
**Fix:** Add exponential backoff (already configured, see `main.py` line 265)

### Issue: "No sources found"
**Cause:** Person is too obscure or search queries weak  
**Fix:** Search uses 2026 dates + signal words (see `prompts.py`)

### Issue: "Alerts not appearing"
**Status:** Known issue in UI rendering (fix in progress)  
**Workaround:** Alerts available in JSON response (`/research` endpoint)

### Issue: "Briefing is very short ([NOT FOUND] everywhere)"
**Cause:** Person has minimal public presence  
**Fix:** Normal for students, early-stage employees (system working as designed)

### Issue: "Out of memory after 50 requests"
**Cause:** Memory leak in scraper or LLM context  
**Fix:** Restart Flask process every 1000 requests (see `supervisor.conf`)

---

## Scaling Strategy

### Phase 1: Pilot (0-10 daily users)
- Single server (t3.medium)
- Manual monitoring
- Groq free tier sufficient

### Phase 2: Early Adoption (10-100 daily users)
- 2-3 servers behind load balancer
- Redis caching layer
- Upgrade to Groq Pro plan

### Phase 3: Scale (100-1000 daily users)
- Kubernetes cluster (3+ nodes)
- PostgreSQL with replicas
- Content Delivery Network for static assets
- Multiple API key quotas

### Phase 4: Enterprise (1000+ daily users)
- Auto-scaling group with load balancing
- Dedicated database replicas
- Message queue (RabbitMQ/SQS) for async processing
- Regional deployment

---

## Support & Maintenance

### Regular Tasks
- **Daily:** Monitor error logs, check API quotas
- **Weekly:** Review alert quality, check performance metrics
- **Monthly:** Update dependencies, security patches
- **Quarterly:** Review & optimize database indices

### Update Procedure
```bash
1. Test on staging environment
2. Create database backup
3. Deploy update (blue-green deployment)
4. Health check validation
5. Monitor for 4 hours
6. Document any changes
```

### Contact & Support
- **Issues:** GitHub Issues
- **Roadmap:** GitHub Discussions
- **Critical:** PagerDuty escalation

---

## Next Steps

1. **Choose deployment option** (Single Server / Docker / Cloud)
2. **Configure environment variables** (see .env.example)
3. **Run deployment script** (see `deploy.sh`)
4. **Execute deployment checklist** (above)
5. **Monitor production** (first 24 hours intensive)

See `DEPLOYMENT_SCRIPTS.md` for detailed commands for each option.
