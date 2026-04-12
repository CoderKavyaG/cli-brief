# Deploy to Production (5 Minutes)

## Option 1: Railway.app (Recommended - Easiest)

### Step 1: Create Account
Go to https://railway.app - Sign in with GitHub

### Step 2: Deploy
1. Click "Create Project"
2. Select "Deploy from GitHub repo"
3. Choose `cli-brief` repository
4. Click Deploy ✓

### Step 3: Add Environment Variables
1. Go to project settings
2. Add variables:
   ```
   GROQ_API_KEY = your_key
   TAVILY_SEARCH_API_KEY = your_key
   FIRECRAWL_API_KEY = your_key (optional)
   FLASK_ENV = production
   ```

### Step 4: Share Link
Get your deployment URL (e.g., `https://cli-brief-prod.up.railway.app`)
Share with friends!

---

## Option 2: Render.com (Free Tier)

### Step 1: Sign Up
Go to https://render.com - Sign in with GitHub

### Step 2: Create Web Service
1. Click "New +" → "Web Service"
2. Connect GitHub repo
3. Settings:
   - **Name:** cli-brief
   - **Runtime:** Python
   - **Build Command:** `pip install -r requirements.txt && pip install gunicorn`
   - **Start Command:** `gunicorn --bind 0.0.0.0:$PORT --timeout 120 app:app`

### Step 3: Set Environment Variables
In "Environment" section:
```
GROQ_API_KEY = your_key
TAVILY_SEARCH_API_KEY = your_key
FIRECRAWL_API_KEY = your_key (optional)
FLASK_ENV = production
```

### Step 4: Deploy
Click "Deploy" - Wait ~2 min
Access at: `https://your-service-name.onrender.com`

---

## Troubleshooting

### "Build failed"
- Check Procfile exists
- Check requirements.txt has all dependencies
- Check Python version in runtime.txt

### "502 Bad Gateway"
- API keys not set → Add to environment variables
- Research taking too long → Normal (60-120s)
- Restart service → Check logs

### "Research failed"
- Check GROQ_API_KEY is valid
- Check TAVILY_SEARCH_API_KEY is valid
- View logs to see exact error

---

## Share with Friends

Once deployed, share this message:

```
Hey! Try this meeting briefing tool:
https://your-deployment-url.com

Enter a person's name + role + company
It researches them & generates executive briefing in 1 minute

Free to try!
```

---

## Monitor Usage

### View Logs
- **Railway:** Dashboard → Logs tab
- **Render:** Dashboard → Logs tab

### Check Performance
Add `/health` endpoint to URL:
`https://your-url/health`

Response shows:
- API connectivity
- Uptime
- Last request time

---

## Upgrade Later

If friends use it heavily:
- **Railway:** Pay as you go ($5/month minimum)
- **Render:** Upgrade to paid tier (~$7/month)

Both handle unlimited API calls with your keys.
