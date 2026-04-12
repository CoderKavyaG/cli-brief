#!/usr/bin/env python3
"""
Flask Web UI for Meeting Intelligence Agent
Provides a web interface to research people and generate executive briefings
"""

from flask import Flask, render_template_string, request, jsonify, send_file
from phase1_agent.coordinator import PlatformCoordinator
from phase1_agent.models import Person
import markdown2
import os
import re
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# HTML Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Meeting Intelligence Agent</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            margin-bottom: 40px;
            padding: 20px 0;
        }
        
        .header h1 {
            font-size: 28px;
            margin-bottom: 8px;
            color: #222;
        }
        
        .header p {
            color: #666;
            font-size: 14px;
        }
        
        .form-section {
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 500;
            font-size: 14px;
            color: #333;
        }
        
        .form-group input,
        .form-group textarea {
            width: 100%;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 14px;
        }
        
        .form-group input:focus,
        .form-group textarea:focus {
            outline: none;
            border-color: #0066cc;
            box-shadow: 0 0 0 3px rgba(0, 102, 204, 0.1);
        }
        
        .form-group textarea {
            resize: vertical;
            min-height: 100px;
        }
        
        .button-group {
            display: flex;
            gap: 10px;
        }
        
        button {
            flex: 1;
            padding: 12px 24px;
            border: none;
            border-radius: 4px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .btn-primary {
            background: #222;
            color: white;
        }
        
        .btn-primary:hover:not(:disabled) {
            background: #111;
        }
        
        .btn-primary:disabled {
            background: #999;
            cursor: not-allowed;
            opacity: 0.7;
        }
        
        .btn-secondary {
            background: #f0f0f0;
            color: #333;
            border: 1px solid #ddd;
        }
        
        .btn-secondary:hover {
            background: #e8e8e8;
        }
        
        .loading {
            text-align: center;
            padding: 40px;
            margin-top: 20px;
        }
        
        .spinner {
            border: 3px solid #f0f0f0;
            border-top: 3px solid #222;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .loading-text {
            color: #666;
            font-size: 14px;
        }
        
        .briefing-section {
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            margin-top: 20px;
        }
        
        .briefing-content {
            margin-bottom: 20px;
        }
        
        .briefing-content h1 {
            font-size: 24px;
            margin: 20px 0 10px 0;
            margin-top: 0;
            color: #222;
        }
        
        .briefing-content h2 {
            font-size: 18px;
            margin: 20px 0 10px 0;
            color: #333;
            border-bottom: 2px solid #f0f0f0;
            padding-bottom: 8px;
        }
        
        .briefing-content h3 {
            font-size: 16px;
            margin: 15px 0 8px 0;
        }
        
        .briefing-content p,
        .briefing-content li {
            margin-bottom: 10px;
            color: #555;
        }
        
        .briefing-content ul,
        .briefing-content ol {
            margin-left: 20px;
            margin-bottom: 10px;
        }
        
        .briefing-content strong {
            font-weight: 600;
            color: #333;
        }
        
        .source-badge {
            background: #f0f0f0;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 2px 8px;
            font-size: 12px;
            color: #666;
            font-family: 'Monaco', 'Menlo', 'Courier New', monospace;
            display: inline-block;
            margin: 0 2px;
        }
        
        .confidence-badge {
            display: inline-block;
            padding: 6px 12px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
            margin-right: 10px;
        }
        
        .confidence-high {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .confidence-medium {
            background: #fff3cd;
            color: #856404;
            border: 1px solid #ffeeba;
        }
        
        .confidence-low {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        .context-banner {
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 6px;
            padding: 10px 14px;
            font-size: 13px;
            color: #495057;
            margin-bottom: 20px;
        }
        
        .alerts-container {
            margin-bottom: 24px;
        }
        
        .alert-box {
            border-radius: 8px;
            padding: 14px 16px;
            margin-bottom: 12px;
            border-left: 4px solid;
            font-size: 14px;
            line-height: 1.5;
        }
        
        .alert-role {
            background: #fef2f2;
            border-color: #ef4444;
            color: #991b1b;
        }
        
        .alert-funding {
            background: #f0fdf4;
            border-color: #22c55e;
            color: #166534;
        }
        
        .alert-controversy {
            background: #fff7ed;
            border-color: #f97316;
            color: #9a3412;
        }
        
        .alert-launch {
            background: #eff6ff;
            border-color: #3b82f6;
            color: #1e40af;
        }
        
        .alert-label {
            font-weight: 700;
            font-size: 12px;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            display: block;
            margin-bottom: 6px;
            opacity: 0.85;
        }
        
        .alert-source {
            font-size: 11px;
            opacity: 0.7;
            margin-top: 8px;
            display: block;
        }
        
        .alert-source a {
            color: inherit;
            text-decoration: underline;
        }
        
        .alert-source a:hover {
            opacity: 1;
        }
        
        .action-buttons {
            display: flex;
            gap: 10px;
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid #f0f0f0;
        }
        
        .action-buttons button {
            flex: 1;
        }
        
        .error-message {
            background: #f8d7da;
            color: #721c24;
            padding: 15px;
            border: 1px solid #f5c6cb;
            border-radius: 4px;
            margin-top: 20px;
        }
        
        .meta-info {
            background: #f9f9f9;
            padding: 12px;
            border-radius: 4px;
            margin-bottom: 20px;
            font-size: 13px;
            color: #666;
        }
        
        .meta-info **{
            color: #333;
            font-weight: 600;
        }
        
        @media (max-width: 600px) {
            .container {
                padding: 10px;
            }
            
            .form-section,
            .briefing-section {
                padding: 20px;
            }
            
            .header h1 {
                font-size: 22px;
            }
            
            .button-group {
                flex-direction: column;
            }
            
            button {
                width: 100%;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>[SEARCH] Meeting Intelligence Agent</h1>
            <p>Research anyone in seconds. Get an executive briefing with verified sources.</p>
        </div>
        
        <div id="form-container" class="form-section">
            <form id="research-form">
                <div class="form-group">
                    <label for="name">Person's Name *</label>
                    <input 
                        type="text" 
                        id="name" 
                        name="name" 
                        required
                        placeholder="e.g., Kaivalya Vohra"
                    >
                </div>
                
                <div class="form-group">
                    <label for="role">Their Role *</label>
                    <input 
                        type="text" 
                        id="role" 
                        name="role" 
                        required
                        placeholder="CEO, Co-founder, VP Engineering"
                    >
                </div>
                
                <div class="form-group">
                    <label for="company">Their Company *</label>
                    <input 
                        type="text" 
                        id="company" 
                        name="company" 
                        required
                        placeholder="e.g., Zepto"
                    >
                </div>
                
                <div class="form-group">
                    <label for="context">Your Meeting Context *</label>
                    <textarea 
                        id="context" 
                        name="context" 
                        required
                        placeholder="Why are you meeting them? What do you want to discuss?"
                    ></textarea>
                </div>
                
                <button type="submit" class="btn-primary">Research This Person</button>
            </form>
        </div>
        
        <div id="loading-container" style="display: none;">
            <div class="loading">
                <div class="spinner"></div>
                <div class="loading-text">
                    <p>Searching the web, scraping sources, synthesizing...</p>
                    <p style="font-size: 12px; margin-top: 10px; color: #999;">This takes about 60 seconds</p>
                </div>
            </div>
        </div>
        
        <div id="briefing-container" style="display: none;">
            <div class="briefing-section">
                <div id="briefing-content" class="briefing-content"></div>
                
                <div class="action-buttons">
                    <button type="button" class="btn-secondary" onclick="downloadBriefing()">
                        📥 Download as Markdown
                    </button>
                    <button type="button" class="btn-secondary" onclick="resetForm()">
                        🔄 Research Another Person
                    </button>
                </div>
            </div>
        </div>
        
        <div id="error-container" style="display: none;">
            <div class="error-message" id="error-text"></div>
            <button type="button" class="btn-primary" onclick="resetForm()" style="margin-top: 15px; width: 100%;">
                Try Again
            </button>
        </div>
    </div>
    
    <script>
        let lastBriefingMarkdown = '';
        let lastPersonName = '';
        
        document.getElementById('research-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const name = document.getElementById('name').value.trim();
            const role = document.getElementById('role').value.trim();
            const company = document.getElementById('company').value.trim();
            const context = document.getElementById('context').value.trim();
            
            if (!name || !role || !company || !context) {
                alert('Please fill in all fields');
                return;
            }
            
            // Show loading, hide others
            document.getElementById('form-container').style.display = 'none';
            document.getElementById('loading-container').style.display = 'block';
            document.getElementById('briefing-container').style.display = 'none';
            document.getElementById('error-container').style.display = 'none';
            
            try {
                const response = await fetch('/research', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ name, role, company, context })
                });
                
                const data = await response.json();
                
                if (!response.ok) {
                    throw new Error(data.error || 'Research failed');
                }
                
                // Store for download
                lastBriefingMarkdown = data.markdown;
                lastPersonName = name;
                
                // Build alerts and context HTML
                const alertTypeMap = {
                    "role_change": "alert-role",
                    "funding": "alert-funding", 
                    "controversy": "alert-controversy",
                    "launch": "alert-launch"
                };
                
                let renderHTML = '';
                
                // Add context banner
                renderHTML += `<div class="context-banner">📋 Meeting context: ${data.context}</div>`;
                
                // Render alerts
                if (data.alerts && data.alerts.length > 0) {
                    renderHTML += '<div class="alerts-container">';
                    for (const alert of data.alerts) {
                        const cssClass = alertTypeMap[alert.type] || 'alert-box';
                        renderHTML += `<div class="alert-box ${cssClass}">`;
                        renderHTML += `<span class="alert-label">${alert.emoji} ${alert.label}</span>`;
                        renderHTML += `<span>${alert.text}</span>`;
                        renderHTML += `<span class="alert-source">Source: <a href="${alert.url}" target="_blank">${alert.source}</a></span>`;
                        renderHTML += '</div>';
                    }
                    renderHTML += '</div>';
                }
                
                // Add briefing content
                renderHTML += data.html;
                
                // Show briefing
                document.getElementById('loading-container').style.display = 'none';
                document.getElementById('briefing-container').style.display = 'block';
                document.getElementById('briefing-content').innerHTML = renderHTML;
                
            } catch (error) {
                console.error('Error:', error);
                document.getElementById('loading-container').style.display = 'none';
                document.getElementById('error-container').style.display = 'block';
                document.getElementById('error-text').textContent = 
                    'Research failed: ' + error.message + '. Please try again.';
            }
        });
        
        function downloadBriefing() {
            if (!lastBriefingMarkdown) return;
            
            const element = document.createElement('a');
            element.setAttribute('href', 'data:text/markdown;charset=utf-8,' + encodeURIComponent(lastBriefingMarkdown));
            element.setAttribute('download', `briefing_${lastPersonName.replace(/\\s+/g, '_').toLowerCase()}.md`);
            element.style.display = 'none';
            document.body.appendChild(element);
            element.click();
            document.body.removeChild(element);
        }
        
        function resetForm() {
            document.getElementById('research-form').reset();
            document.getElementById('form-container').style.display = 'block';
            document.getElementById('loading-container').style.display = 'none';
            document.getElementById('briefing-container').style.display = 'none';
            document.getElementById('error-container').style.display = 'none';
            lastBriefingMarkdown = '';
            lastPersonName = '';
        }
    </script>
</body>
</html>
"""


def extract_confidence_level(html_content: str) -> str:
    """Extract confidence level from briefing content"""
    if "Confidence: HIGH" in html_content:
        return "HIGH"
    elif "Confidence: MEDIUM" in html_content:
        return "MEDIUM"
    else:
        return "LOW"


def style_source_badges(html_content: str) -> str:
    """Convert [Source: URL] tags to styled badges with just domain name"""
    # Match [Source: anything] pattern
    def replace_badge(match):
        source_text = match.group(1).strip()
        # Try to extract domain from URL
        try:
            if source_text.startswith('http'):
                domain = urlparse(source_text).netloc.replace('www.', '')
            else:
                domain = source_text
            return f'<span class="source-badge">{domain}</span>'
        except:
            return f'<span class="source-badge">{source_text}</span>'
    
    html_content = re.sub(r'\[Source: ([^\]]+)\]', replace_badge, html_content)
    return html_content


def add_confidence_badge(html_content: str) -> str:
    """Add confidence badge to briefing"""
    confidence = extract_confidence_level(html_content)
    badge_class = f"confidence-{confidence.lower()}"
    badge_html = f'<span class="confidence-badge {badge_class}">Confidence: {confidence}</span>'
    
    # Insert after the first heading
    html_content = re.sub(
        r'(<h2[^>]*>Research Confidence</h2>)',
        badge_html + r'\1',
        html_content,
        count=1
    )
    return html_content


@app.route('/')
def index():
    """Show the research form"""
    return render_template_string(HTML_TEMPLATE)


@app.route('/research', methods=['POST'])
def research():
    """Execute DEEP research across all platforms and return briefing"""
    try:
        # First, check if API keys are configured
        from phase1_agent.config import TAVILY_API_KEY, FIRECRAWL_API_KEY
        
        missing_keys = []
        if not TAVILY_API_KEY:
            missing_keys.append("TAVILY_API_KEY")
        if not FIRECRAWL_API_KEY:
            missing_keys.append("FIRECRAWL_API_KEY")
        
        if missing_keys:
            error_msg = f"Missing API keys on server: {', '.join(missing_keys)}. Server admin needs to set environment variables."
            print(f"[ERROR] {error_msg}")
            return jsonify({"error": error_msg}), 500
        
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        name = data.get('name', '').strip()
        role = data.get('role', '').strip()
        company = data.get('company', '').strip()
        context = data.get('context', '').strip()
        
        if not all([name, role, company, context]):
            return jsonify({"error": "All fields are required"}), 400
        
        # Create person and run DEEP research
        person = Person(name=name, role=role, company=company, context=context)
        coordinator = PlatformCoordinator()
        
        print(f"\n[WEB] DEEP RESEARCH: {person.name} ({person.role}) at {person.company}")
        print(f"[WEB] Researching across 5 platforms...")
        
        try:
            # Execute deep research
            research_data = coordinator.research_person_deep(person)
        except Exception as research_error:
            print(f"[ERROR] Research exception: {str(research_error)}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": f"Research error: {str(research_error)}"}), 500
        
        if not research_data:
            print(f"[ERROR] Research returned None")
            return jsonify({"error": "Research failed - no data found."}), 500
        
        # Generate markdown briefing from research data
        markdown_content = generate_briefing_from_research(research_data, person)
        
        # Convert markdown to HTML
        html_content = markdown2.markdown(markdown_content, extras=['nl2br', 'tables'])
        
        # Add styling
        html_content = style_source_badges(html_content)
        html_content = add_confidence_badge(html_content)
        
        # Extract alerts from research
        alerts_data = extract_alerts_from_research(research_data, person.name)
        
        # Add audit info to output
        audit_report = coordinator.generate_audit_report(research_data)
        print(audit_report)
        
        return jsonify({
            "success": True,
            "html": html_content,
            "markdown": markdown_content,
            "person": name,
            "company": company,
            "context": context,
            "alerts": alerts_data,
            "platforms_researched": list(research_data['platforms'].keys())
        })
    
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


def generate_briefing_from_research(research_data: dict, person: Person) -> str:
    """Generate executive briefing markdown from deep research data"""
    
    # Build briefing from extracted data
    briefing = f"""# Executive Briefing: {person.name}

**Role:** {person.role} | **Company:** {person.company}
**Meeting Context:** {person.context}
**Generated:** {datetime.now().strftime('%B %d, %Y')}

---

## Research Summary
**Platforms Researched:** {len(research_data['platforms'])} platforms
**Data Points Collected:** {sum(len(p.get('scraped_content', [])) for p in research_data['platforms'].values())} sources
**Confidence:** {'HIGH' if sum(len(p.get('scraped_content', [])) for p in research_data['platforms'].values()) >= 3 else 'MEDIUM' if sum(len(p.get('scraped_content', [])) for p in research_data['platforms'].values()) >= 1 else 'LOW'}

---

## Who They Are

"""
    
    # Extract LinkedIn data
    linkedin_data = research_data['platforms'].get('linkedin', {})
    if linkedin_data.get('scraped_content'):
        for item in linkedin_data['scraped_content'][:1]:
            extracted = item['extracted']
            if extracted.get('bio') and '[NOT FOUND]' not in extracted['bio']:
                briefing += f"{extracted['bio']} [Source: {item['url'][:50]}.../]\n\n"
            if extracted.get('current_role') and '[NOT FOUND]' not in extracted['current_role']:
                briefing += f"Role: {extracted['current_role']} [Source: {item['url'][:50]}.../]\n\n"
    
    # Extract personal site data
    personal_data = research_data['platforms'].get('personal_site', {})
    if personal_data.get('scraped_content'):
        for item in personal_data['scraped_content'][:1]:
            extracted = item['extracted']
            if extracted.get('intro') and '[NOT FOUND]' not in extracted['intro']:
                briefing += f"{extracted['intro'][:200]} [Source: {item['url'][:50]}.../]\n\n"
    
    briefing += "\n## What They Care About\n\n"
    
    # Extract Twitter/interests
    twitter_data = research_data['platforms'].get('twitter', {})
    if twitter_data.get('scraped_content'):
        for item in twitter_data['scraped_content'][:1]:
            extracted = item['extracted']
            if extracted.get('interests') and '[NOT FOUND]' not in extracted['interests']:
                briefing += f"* {extracted['interests'][:200]} [Source: twitter.com]\n"
            if extracted.get('recent_thoughts') and '[NOT FOUND]' not in extracted['recent_thoughts']:
                briefing += f"* {extracted['recent_thoughts'][:200]} [Source: twitter.com]\n"
    
    briefing += "\n## Current Company Situation\n\n"
    
    # Extract company data
    company_data = research_data['platforms'].get('company', {})
    if company_data.get('scraped_content'):
        for item in company_data['scraped_content'][:1]:
            extracted = item['extracted']
            if extracted.get('mission') and '[NOT FOUND]' not in extracted['mission']:
                briefing += f"* {extracted['mission'][:200]} [Source: {item['url'][:40]}.../]\n"
            if extracted.get('team') and '[NOT FOUND]' not in extracted['team']:
                briefing += f"* {extracted['team'][:200]} [Source: {item['url'][:40]}.../]\n"
    
    briefing += "\n## How To Approach This Meeting\n\n"
    briefing += "* Research indicates strong background in the field\n"
    briefing += "* Align discussion with their demonstrated interests\n"
    briefing += "* Reference specific projects or insights found during research\n"
    
    briefing += "\n## Smart Questions\n\n"
    briefing += "1. What aspects of your work do you find most impactful?\n"
    briefing += "2. Where do you see the industry heading in the next 5 years?\n"
    briefing += "3. How is your organization adapting to current market changes?\n"
    
    briefing += "\n## Areas To Explore\n\n"
    briefing += "* Recent initiatives and projects\n"
    briefing += "* Technical interests and expertise areas\n"
    briefing += "* Vision for the organization\n"
    
    briefing += "\n## Conversation Starters\n\n"
    briefing += f"Start with: 'I noticed you're working on [...], I'm very interested in that space.'\n"
    briefing += "This shows you've done your research and have genuine interest.\n"
    
    briefing += "\n## Sources\n\n"
    briefing += "**Research Depth:** Multi-platform verification\n"
    briefing += f"**Platforms Checked:** LinkedIn, Personal Website, Twitter/X, GitHub, Company Pages\n"
    briefing += f"**Last Updated:** {datetime.now().isoformat()}\n"
    
    return briefing


def extract_alerts_from_research(research_data: dict, person_name: str) -> list:
    """Extract high-signal alerts from research data"""
    alerts = []
    person_name_lower = person_name.lower()
    
    for platform, data in research_data['platforms'].items():
        for scraped_item in data.get('scraped_content', []):
            extracted = scraped_item['extracted']
            
            # Check for funding mentions
            if any(keyword in str(extracted).lower() for keyword in ['funding', 'raise', 'series', 'valuation']):
                if person_name_lower in str(extracted).lower():
                    alerts.append({
                        "type": "funding",
                        "emoji": "💰",
                        "label": "FUNDING",
                        "text": f"Funding activity detected related to {person_name}",
                        "source": platform,
                        "url": scraped_item['url']
                    })
            
            # Check for role changes
            if any(keyword in str(extracted).lower() for keyword in ['ceo', 'founder', 'appointed', 'chief']):
                if person_name_lower in str(extracted).lower():
                    alerts.append({
                        "type": "role",
                        "emoji": "🚨",
                        "label": "ROLE",
                        "text": f"Leadership role identified for {person_name}",
                        "source": platform,
                        "url": scraped_item['url']
                    })
    
    return alerts[:3]  # Limit to top 3 alerts


from datetime import datetime


if __name__ == '__main__':
    # Create output directory if it doesn't exist
    Path('output').mkdir(exist_ok=True)
    
    # Validate API keys at startup
    from phase1_agent.config import TAVILY_API_KEY, FIRECRAWL_API_KEY, GROQ_API_KEY, GROQ_MODEL
    
    print("\n" + "="*60)
    print("FLASK APP STARTUP CHECK")
    print("="*60)
    
    api_status = {
        "TAVILY_API_KEY": "[OK] Set" if TAVILY_API_KEY else "[MISSING]",
        "FIRECRAWL_API_KEY": "[OK] Set" if FIRECRAWL_API_KEY else "[MISSING]",
        "GROQ_API_KEY": "[OK] Set" if GROQ_API_KEY else "[MISSING]",
        "GROQ_MODEL": f"[OK] {GROQ_MODEL}" if GROQ_MODEL else "[MISSING]"
    }
    
    for key, status in api_status.items():
        print(f"  {key}: {status}")
    
    if not all([TAVILY_API_KEY, FIRECRAWL_API_KEY, GROQ_API_KEY]):
        print("\n[WARNING] Some API keys are missing!")
        print("   If deploying to Railway/Render:")
        print("   1. Go to your deployment dashboard")
        print("   2. Add environment variables:")
        print("      - TAVILY_API_KEY")
        print("      - FIRECRAWL_API_KEY")
        print("      - GROQ_API_KEY")
        print("   3. Redeploy the application")
    else:
        print("\n[OK] All API keys configured. Ready to research!")
    
    print("="*60 + "\n")
    
    # Read port from environment (Railway/Render set this)
    # Default to 5000 for local development
    port = int(os.environ.get('PORT', 5000))
    host = '0.0.0.0'  # Listen on all interfaces for production
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    print("="*60)
    print("Starting Meeting Intelligence Agent Web UI")
    print("="*60)
    print(f"\n[RUNNING] Listening on http://{host}:{port}\n")
    print("Press Ctrl+C to stop the server\n")
    
    app.run(debug=debug, port=port, host=host)
