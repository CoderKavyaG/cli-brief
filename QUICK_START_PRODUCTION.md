# Quick Start: Meeting Intelligence Agent Production Deployment

## 5-Minute Setup (Linux Server)

### 1. **Prepare System** (1 min)
```bash
sudo apt-get update && sudo apt-get install -y git python3-pip curl

git clone https://github.com/CoderKavyaG/cli-brief.git
cd cli-brief
```

### 2. **Run Deployment Script** (2 min)
```bash
sudo bash deploy.sh
```
This automatically:
- Creates application user
- Sets up directories
- Installs Python dependencies
- Configures systemd service

### 3. **Configure API Keys** (1 min)
```bash
sudo nano /opt/briefing-agent/.env
```

Add these (required):
```
GROQ_API_KEY=your_key_here
TAVILY_SEARCH_API_KEY=your_key_here
```

### 4. **Start Service** (1 min)
```bash
sudo systemctl start briefing-agent
sudo systemctl enable briefing-agent  # Auto-start on reboot

# Verify it's running
sudo systemctl status briefing-agent
```

### ✅ Done! Access at: http://server-ip:5000

---

## Verify It's Working

```bash
# Check health
curl http://localhost:5000/health

# Test research
curl -X POST http://localhost:5000/research \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Deepinder Goyal",
    "role": "CEO",
    "company": "Blinkit",
    "context": "Test"
  }'

# View logs
sudo journalctl -u briefing-agent -f
```

---

## Using Docker (Alternative)

```bash
# Set API keys
export GROQ_API_KEY=your_key
export TAVILY_SEARCH_API_KEY=your_key

# Run with Docker Compose
docker-compose up -d

# Done! Access at http://localhost:5000
```

---

## Common Tasks

### Restart Service
```bash
sudo systemctl restart briefing-agent
```

### Check Logs
```bash
sudo journalctl -u briefing-agent -n 100  # Last 100 lines
sudo tail -f /var/log/briefing-agent/error.log
```

### Update Code
```bash
cd /opt/briefing-agent
sudo -u briefing-agent git pull origin main
sudo systemctl restart briefing-agent
```

### Monitor Performance
```bash
# Watch metrics
watch -n 5 'curl -s http://localhost:5000/health | jq'

# Check CPU/Memory
top -p $(pidof gunicorn | head -1)
```

### Health Dashboard
Visit: `http://localhost:5000/health` for:
- Service status
- API connectivity
- Uptime
- Last request time

---

## Troubleshooting

### "Connection refused"
```bash
# Check if service is running
sudo systemctl status briefing-agent

# Start it
sudo systemctl start briefing-agent
```

### "429 Too Many Requests"
```bash
# This is rate limiting (expected)
# Groq enforces 30 requests/minute
# System automatically retries with backoff
```

### "API key invalid"
```bash
# Verify key is set
cat /opt/briefing-agent/.env | grep GROQ_API_KEY

# Re-add if missing
nano /opt/briefing-agent/.env
sudo systemctl restart briefing-agent
```

### "Out of memory"
```bash
# Restart the service
sudo systemctl restart briefing-agent

# Check available RAM
free -h

# For <2GB RAM, consider:
# - Adding swap space
# - Using cloud instance with more memory
```

---

## Production Checklist

Before going live:

- [ ] API keys configured securely (not in git!)
- [ ] Systemd service enabled and starting correctly
- [ ] Health endpoint responding (200 OK)
- [ ] Test request successful (generated briefing)
- [ ] Logs being written to `/var/log/briefing-agent/`
- [ ] Firewall allows port 5000 (or 80/443 if behind proxy)
- [ ] Backups configured (database if using PostgreSQL)
- [ ] Monitoring alerts set up (email on service down)
- [ ] SSL certificate installed (if using HTTPS)
- [ ] Rate limiting tuned for your API quotas

---

## Next: Enable Analytics

### Track key metrics in logs
```bash
# See request patterns
tail -f /var/log/briefing-agent/access.log | grep POST

# Monitor errors
tail -f /var/log/briefing-agent/error.log
```

### Set up email alerts
```bash
# Edit: /etc/briefing-agent/monitoring.conf
ERROR_ALERT_EMAIL=admin@yourdomain.com
ALERT_THRESHOLD_ERROR_RATE=0.05  # 5%
ALERT_THRESHOLD_LATENCY=120  # seconds
```

---

## Scale Up: Load Balancing

Once you need more capacity:

```bash
# Run multiple instances
for i in {1..3}; do
  docker run -p 500$i:5000 briefing-agent:1.0 &
done

# Use Nginx as load balancer (see nginx.conf.template)
```

---

## Support & Help

- **Logs:** `journalctl -u briefing-agent`
- **GitHub:** https://github.com/CoderKavyaG/cli-brief/issues
- **Docs:** See `PRODUCTION_DEPLOYMENT.md` for detailed guide

---

## One-Liner Quick Start
```bash
sudo bash -c "apt-get update -y && apt-get install -y git python3-pip && git clone https://github.com/CoderKavyaG/cli-brief.git /opt/briefing-agent && cd /opt/briefing-agent && bash deploy.sh"
```

Then edit `.env` with your API keys and run `sudo systemctl start briefing-agent`

---

**Ready to deploy? Start with step 1 above!** ✅
