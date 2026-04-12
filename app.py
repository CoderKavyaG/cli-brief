#!/usr/bin/env python3
"""
Flask Web UI for Meeting Intelligence Agent
Provides a web interface to research people and generate executive briefings
"""

from flask import Flask, render_template_string, request, jsonify, send_file
from phase1_agent.main import IntelAgent
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
            <h1>🔍 Meeting Intelligence Agent</h1>
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
    """Execute research and return briefing"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        name = data.get('name', '').strip()
        role = data.get('role', '').strip()
        company = data.get('company', '').strip()
        context = data.get('context', '').strip()
        
        if not all([name, role, company, context]):
            return jsonify({"error": "All fields are required"}), 400
        
        # Create person and run research
        person = Person(name=name, role=role, company=company, context=context)
        agent = IntelAgent()
        
        print(f"\n[WEB] Researching: {person.name} ({person.role}) at {person.company}")
        briefing = agent.research(person)
        
        if not briefing:
            return jsonify({"error": "Research failed - insufficient data found"}), 500
        
        # Get the markdown file content
        files = list(Path('output').glob(f'briefing_{name.replace(" ", "_").lower()}*.md'))
        if not files:
            return jsonify({"error": "Briefing file not created"}), 500
        
        briefing_file = sorted(files)[-1]  # Get most recent
        with open(briefing_file, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
        
        # Convert markdown to HTML
        html_content = markdown2.markdown(markdown_content, extras=['nl2br', 'tables'])
        
        # Add styling
        html_content = style_source_badges(html_content)
        html_content = add_confidence_badge(html_content)
        
        # Get alerts from briefing
        alerts_data = []
        if hasattr(briefing, 'alerts') and briefing.alerts:
            for alert in briefing.alerts:
                alerts_data.append({
                    "type": alert.get("type", ""),
                    "emoji": alert.get("emoji", ""),
                    "label": alert.get("label", ""),
                    "text": alert.get("text", ""),
                    "source": alert.get("source", ""),
                    "url": alert.get("url", "")
                })
            print(f"[DEBUG] Found {len(alerts_data)} alerts in briefing object")
        
        # Ensure alerts are in markdown if they exist
        if alerts_data and '🔔' not in markdown_content:
            print(f"[DEBUG] Alerts exist but not in markdown - prepending {len(alerts_data)} alerts")
            alerts_md = "## 🔔 Critical Meeting Intel\n> Read these before anything else\n\n"
            for alert in alerts_data:
                alerts_md += f"**{alert['emoji']} {alert['label']}**\n"
                alerts_md += f"{alert['text']}\n"
                alerts_md += f"[Source: {alert['source']}]({alert['url']})\n\n"
            alerts_md += "---\n\n"
            markdown_content = alerts_md + markdown_content
            print(f"[DEBUG] Markdown now starts with: {markdown_content[:100]}")
            
            # Re-convert to HTML with alerts
            html_content = markdown2.markdown(markdown_content, extras=['nl2br', 'tables'])
            html_content = style_source_badges(html_content)
            html_content = add_confidence_badge(html_content)
        elif alerts_data:
            print(f"[DEBUG] Alerts exist AND are already in markdown")
        else:
            print(f"[DEBUG] No alerts to add")
        
        return jsonify({
            "success": True,
            "html": html_content,
            "markdown": markdown_content,
            "person": name,
            "company": company,
            "context": context,
            "alerts": alerts_data
        })
    
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    # Create output directory if it doesn't exist
    Path('output').mkdir(exist_ok=True)
    
    # Read port from environment (Railway/Render set this)
    # Default to 5000 for local development
    port = int(os.environ.get('PORT', 5000))
    host = '0.0.0.0'  # Listen on all interfaces for production
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    print("="*60)
    print("Starting Meeting Intelligence Agent Web UI")
    print("="*60)
    print(f"\n🚀 Listening on http://{host}:{port}\n")
    print("Press Ctrl+C to stop the server\n")
    
    app.run(debug=debug, port=port, host=host)
