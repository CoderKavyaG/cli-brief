"""
Clean Flask web UI for Meeting Intelligence Agent
"""

from flask import Flask, request, jsonify, render_template_string
import os
import re
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Meeting Intel</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; color: #333; }
.wrap { max-width: 720px; margin: 0 auto; padding: 24px 16px; }
h1 { font-size: 24px; margin-bottom: 4px; font-weight: 700; }
.sub { color: #666; font-size: 13px; margin-bottom: 28px; }
.card { background: white; border-radius: 10px; padding: 24px; box-shadow: 0 1px 4px rgba(0,0,0,.08); }
label { display: block; font-size: 13px; font-weight: 500; margin-bottom: 6px; color: #222; }
input, textarea { width: 100%; padding: 10px 12px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; margin-bottom: 16px; font-family: inherit; }
input:focus, textarea:focus { outline: none; border-color: #333; box-shadow: 0 0 0 3px rgba(0,0,0,.05); }
textarea { min-height: 80px; resize: vertical; }
button { width: 100%; padding: 12px; background: #111; color: white; border: none; border-radius: 6px; font-size: 14px; font-weight: 600; cursor: pointer; transition: background 0.2s; }
button:hover { background: #333; }
button:disabled { background: #888; cursor: default; }
.loader { display: none; text-align: center; padding: 40px; }
.spinner { width: 40px; height: 40px; border: 3px solid #eee; border-top-color: #111; border-radius: 50%; animation: spin 0.8s linear infinite; margin: 0 auto 12px; }
@keyframes spin { to { transform: rotate(360deg); } }
.result { display: none; margin-top: 20px; }
.briefing { background: white; border-radius: 10px; padding: 28px; box-shadow: 0 1px 4px rgba(0,0,0,.08); }
.profile-top { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px; padding-bottom: 20px; border-bottom: 1px solid #f0f0f0; }
.profile-info h2 { font-size: 26px; margin-bottom: 4px; font-weight: 700; }
.profile-info p { color: #666; font-size: 14px; margin-bottom: 8px; }
.profile-photo { width: 80px; height: 80px; border-radius: 50%; object-fit: cover; border: 3px solid #eee; flex-shrink: 0; }
.badges { margin-bottom: 0; }
.badge { display: inline-block; padding: 4px 10px; border-radius: 20px; font-size: 11px; font-weight: 600; margin-right: 6px; }
.conf-high { background: #dcfce7; color: #166534; }
.conf-medium { background: #fef9c3; color: #854d0e; }
.conf-low { background: #fee2e2; color: #991b1b; }
.meta-box { background: #f0f7ff; border-left: 3px solid #3b82f6; padding: 12px 14px; margin-bottom: 20px; border-radius: 0 6px 6px 0; }
.meta-box strong { color: #1e40af; }
.meta-table { width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 14px; }
.meta-table tr { border-bottom: 1px solid #f0f0f0; }
.meta-table td { padding: 8px 0; }
.meta-table td:first-child { font-weight: 600; width: 120px; color: #666; }
.meta-table td:last-child { color: #333; }
.section { margin-bottom: 24px; }
.section h3 { font-size: 13px; font-weight: 700; color: #111; text-transform: uppercase; letter-spacing: .05em; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 2px solid #f0f0f0; }
.section p { font-size: 15px; line-height: 1.65; color: #333; }
.section ul { padding-left: 20px; margin-top: 8px; }
.section li { font-size: 15px; line-height: 1.7; color: #333; margin-bottom: 8px; }
.section ol { padding-left: 20px; margin-top: 8px; }
.section ol li { font-size: 15px; line-height: 1.7; color: #333; margin-bottom: 10px; }
.connect-links { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }
.link-btn { display: inline-flex; align-items: center; padding: 6px 12px; background: #f5f5f5; border: 1px solid #ddd; border-radius: 6px; font-size: 13px; text-decoration: none; color: #2563eb; transition: background 0.2s; }
.link-btn:hover { background: #f0f0f0; }
.icebreaker-box { background: #fffbeb; border-left: 3px solid #f59e0b; padding: 12px 14px; border-radius: 0 6px 6px 0; font-size: 15px; line-height: 1.6; color: #333; }
.actions { display: flex; gap: 10px; margin-top: 24px; }
.btn-outline { flex: 1; padding: 10px; border: 1px solid #ddd; background: white; border-radius: 6px; font-size: 13px; font-weight: 500; cursor: pointer; color: #333; transition: background 0.2s; }
.btn-outline:hover { background: #f5f5f5; }
</style>
</head>
<body>
<div class="wrap">
  <h1>🔍 Meeting Intel</h1>
  <p class="sub">Research anyone before a meeting. Real verified facts in 60 seconds.</p>
  
  <div class="card" id="form-card">
    <div id="form-wrap">
      <label>Person's name *</label>
      <input id="inp-name" placeholder="e.g. Ishan Kumar" />
      
      <label>Their role *</label>
      <input id="inp-role" placeholder="e.g. CEO, Co-founder, Student" />
      
      <label>Their company or institution *</label>
      <input id="inp-company" placeholder="e.g. InTheBox, Chitkara University" />
      
      <label>Why you're meeting them *</label>
      <textarea id="inp-context" placeholder="e.g. I want to discuss a partnership on packaging..."></textarea>
      
      <button id="btn" onclick="go()">Research this person</button>
    </div>
    
    <div class="loader" id="loader">
      <div class="spinner"></div>
      <p style="color:#666;font-size:14px;">
        Searching the web, scraping sources, synthesizing...<br>
        <span style="font-size:12px;color:#999;">Takes about 30–60 seconds</span>
      </p>
    </div>
  </div>
  
  <div class="result" id="result"></div>
</div>

<script>
let mdContent = '';
let personName = '';
let personRole = '';
let personCompany = '';
let personContext = '';
let rejectedUrls = [];

async function go() {
  const name = document.getElementById('inp-name').value.trim();
  const role = document.getElementById('inp-role').value.trim();
  const company = document.getElementById('inp-company').value.trim();
  const ctx = document.getElementById('inp-context').value.trim();
  
  if (!name || !role || !company || !ctx) {
    alert('Please fill in all fields');
    return;
  }
  
  rejectedUrls = [];
  personName = name;
  personRole = role;
  personCompany = company;
  personContext = ctx;
  
  document.getElementById('form-wrap').style.display = 'none';
  document.getElementById('loader').style.display = 'block';
  document.getElementById('btn').disabled = true;
  
  performResearch(name, role, company, ctx, []);
}

async function researchAgain() {
  if (!personName) {
    alert('No previous research found');
    return;
  }
  
  const resultDiv = document.getElementById('result');
  let identity = {};
  if (resultDiv.dataset.identity) {
    try {
      identity = JSON.parse(resultDiv.dataset.identity);
    } catch(e) {
      console.log('Could not parse identity');
    }
  }
  
  if (identity.linkedin_url) rejectedUrls.push(identity.linkedin_url);
  if (identity.personal_site) rejectedUrls.push(identity.personal_site);
  if (identity.github) rejectedUrls.push(identity.github);
  if (identity.twitter) rejectedUrls.push(identity.twitter);
  if (identity.instagram) rejectedUrls.push(identity.instagram);
  
  console.log('Researching again, rejecting', rejectedUrls.length, 'URLs');
  resultDiv.style.display = 'none';
  document.getElementById('loader').style.display = 'block';
  
  performResearch(personName, personRole, personCompany, personContext, rejectedUrls);
}

async function performResearch(name, role, company, ctx, rejected) {
  try {
    const res = await fetch('/research', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({name, role, company, context: ctx, rejected_urls: rejected})
    });
    
    const data = await res.json();
    
    if (!res.ok) {
      throw new Error(data.error || 'Research failed');
    }
    
    mdContent = data.markdown || '';
    renderBriefing(data);
    
  } catch(e) {
    document.getElementById('loader').style.display = 'none';
    document.getElementById('form-wrap').style.display = 'block';
    document.getElementById('result').style.display = 'block';
    document.getElementById('btn').disabled = false;
    alert('Error: ' + e.message);
  }
}

function renderBriefing(d) {
  document.getElementById('loader').style.display = 'none';
  document.getElementById('result').style.display = 'block';
  
  const identity = d.identity || {};
  const conf = d.confidence || 'LOW';
  const confClass = conf === 'HIGH' ? 'conf-high' : 
                    conf === 'MEDIUM' ? 'conf-medium' : 'conf-low';
  
  const photoUrl = d.photo_url || identity.photo_url;
  const photoHtml = photoUrl 
    ? `<img src="${photoUrl}" class="profile-photo" onerror="this.style.display='none'" alt="${d.name}" />`
    : '';
  
  let connectHtml = '';
  if (identity.linkedin_url) {
    const handle = identity.handle || d.linkedin_handle || 'Profile';
    connectHtml += `<a href="${identity.linkedin_url}" target="_blank" class="link-btn">LinkedIn @${handle}</a>`;
  }
  if (identity.github) {
    const gh = identity.github.split('/').pop();
    connectHtml += `<a href="${identity.github}" target="_blank" class="link-btn">GitHub ${gh}</a>`;
  }
  if (identity.twitter) {
    const tw = identity.twitter.split('/').pop();
    connectHtml += `<a href="${identity.twitter}" target="_blank" class="link-btn">Twitter @${tw}</a>`;
  }
  if (identity.instagram) {
    const ig = identity.instagram.split('/').pop();
    connectHtml += `<a href="${identity.instagram}" target="_blank" class="link-btn">Instagram @${ig}</a>`;
  }
  if (identity.personal_site) {
    const site = identity.personal_site.replace(/https?:\\/\\/www\\./, '').replace(/\\/$/, '');
    connectHtml += `<a href="${identity.personal_site}" target="_blank" class="link-btn">Website →</a>`;
  }
  if (identity.email) {
    connectHtml += `<span class="link-btn"><strong>${identity.email}</strong></span>`;
  }
  
  const careItems = Array.isArray(d.what_they_care_about) 
    ? d.what_they_care_about.map(i => `<li>${i}</li>`).join('')
    : `<li>${d.what_they_care_about}</li>`;
  
  const questions = Array.isArray(d.smart_questions)
    ? d.smart_questions.map((q,i) => `<li>${q}</li>`).join('')
    : `<li>${d.smart_questions}</li>`;
  
  const resultDiv = document.getElementById('result');
  resultDiv.dataset.identity = JSON.stringify(identity);
  
  resultDiv.innerHTML = `
  <div class="briefing">
    <div class="profile-top">
      <div class="profile-info">
        <h2>${d.name}</h2>
        <p>${d.role} at <strong>${d.company}</strong></p>
        <div class="badges">
          <span class="badge ${confClass}">${conf} confidence</span>
          <span class="badge" style="background:#f0f0f0;color:#666;">${(d.sources||[]).length} sources</span>
        </div>
      </div>
      ${photoHtml}
    </div>
    
    <div class="meta-box">
      <strong>📋 Meeting context:</strong> ${d.context}
    </div>
    
    <table class="meta-table">
      <tr><td>Role</td><td>${d.role}</td></tr>
      <tr><td>Company</td><td>${d.company}</td></tr>
      <tr><td>Generated</td><td>${new Date(d.timestamp).toLocaleString()}</td></tr>
    </table>
    
    ${connectHtml ? `<div class="section"><h3>Connect</h3><div class="connect-links">${connectHtml}</div></div>` : ''}
    
    <div class="section">
      <h3>Who They Are</h3>
      <p>${d.who_they_are}</p>
    </div>
    
    <div class="section">
      <h3>What They Care About</h3>
      <ul>${careItems}</ul>
    </div>
    
    <div class="section">
      <h3>Company Situation</h3>
      <p>${d.company_situation}</p>
    </div>
    
    <div class="section">
      <h3>How To Approach</h3>
      <p>${d.meeting_approach}</p>
    </div>
    
    <div class="section">
      <h3>Smart Questions</h3>
      <ol>${questions}</ol>
    </div>
    
    <div class="section">
      <h3>Icebreaker</h3>
      <div class="icebreaker-box">${d.icebreaker}</div>
    </div>
    
    <div class="actions">
      <button class="btn-outline" onclick="downloadMd()">Download Markdown</button>
      <button class="btn-outline" onclick="researchAgain()">Wrong person? Research again</button>
      <button class="btn-outline" onclick="location.reload()">Research Someone Else</button>
    </div>
  </div>`;
}

function downloadMd() {
  if (!mdContent) return;
  const a = document.createElement('a');
  a.href = 'data:text/markdown;charset=utf-8,' + encodeURIComponent(mdContent);
  a.download = personName.replace(/\\s+/g,'_').toLowerCase() + '_briefing.md';
  a.click();
}
</script>
</body>
</html>"""


@app.route('/')
def index():
    """Show web UI"""
    return render_template_string(HTML)


@app.route('/research', methods=['POST'])
def research():
    """Execute research and return briefing"""
    try:
        print(f"\n{'='*60}")
        print(f"[FLASK] /research endpoint called")
        
        from phase1_agent.agent import IntelAgent
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        name = data.get('name', '').strip()
        role = data.get('role', '').strip()
        company = data.get('company', '').strip()
        context = data.get('context', '').strip()
        rejected_urls = data.get('rejected_urls', [])
        
        if not all([name, role, company, context]):
            return jsonify({"error": "All fields are required"}), 400
        
        # Run research
        print(f"[FLASK] Creating agent...")
        agent = IntelAgent()
        print(f"[FLASK] Agent created, calling research()...")
        result = agent.research(name, role, company, context, rejected_urls)
        print(f"[FLASK] Research complete, building response...")
        
        # Build markdown for download
        md_lines = [
            f"# {result['name']}",
            f"",
            f"**{result['role']}** at **{result['company']}**",
            f"",
            f"*Meeting context: {result['context']}*",
            f"*Generated: {result['timestamp']}*",
            f"",
            "---",
            "",
            "## Who They Are",
            "",
            result['who_they_are'],
            "",
            "## What They Care About",
            "",
        ]
        
        for item in (result['what_they_care_about'] 
                     if isinstance(result['what_they_care_about'], list) 
                     else [result['what_they_care_about']]):
            md_lines.append(f"- {item}")
        
        md_lines += [
            "",
            "## Company Situation",
            "",
            result['company_situation'],
            "",
            "## How To Approach This Meeting",
            "",
            result['meeting_approach'],
            "",
            "## Smart Questions",
            "",
        ]
        
        for i, q in enumerate(result['smart_questions'], 1):
            md_lines.append(f"{i}. {q}")
        
        md_lines += [
            "",
            "## Icebreaker / Common Ground",
            "",
            result['icebreaker'],
            "",
            "---",
            "",
            "## Digital Profiles",
            "",
        ]
        
        # Add discovered platforms
        if result.get('linkedin_handle'):
            md_lines.append(f"- **LinkedIn**: https://linkedin.com/in/{result['linkedin_handle']}")
        if result.get('twitter_url'):
            md_lines.append(f"- **Twitter/X**: {result['twitter_url']}")
        if result.get('github_url'):
            md_lines.append(f"- **GitHub**: {result['github_url']}")
        if result.get('personal_site_url'):
            md_lines.append(f"- **Personal Site**: {result['personal_site_url']}")
        if result.get('instagram_url'):
            md_lines.append(f"- **Instagram**: {result['instagram_url']}")
        
        md_lines += [
            "",
            "## Sources",
            "",
        ]
        
        for s in result.get('sources', []):
            md_lines.append(f"- {s}")
        
        result['markdown'] = "\n".join(md_lines)
        
        return jsonify(result)
    
    except Exception as e:
        import traceback
        import sys
        print(f"\n[ERROR] Exception in research endpoint:", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        print(f"[ERROR] Exception str: {str(e)}", file=sys.stderr)
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
