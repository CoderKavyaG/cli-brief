"""
Phase 3: Web Dashboard
Flask web app to view, search, and manage person profiles
"""

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from phase3_integration.datastore import get_datastore, PersonProfile
from phase3_integration.automation import ResearchAutomationEngine
from phase1_agent.models import Person
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Initialize services
datastore = get_datastore()
engine = ResearchAutomationEngine()


@app.route("/")
def dashboard():
    """Main dashboard view"""
    profiles = datastore.get_all_profiles()
    stats = datastore.get_stats()
    
    return jsonify({
        "status": "running",
        "total_profiles": stats["total_profiles"],
        "latest_profiles": [
            {
                "name": p.name,
                "role": p.role,
                "company": p.company,
                "meeting_count": p.meeting_count,
                "last_updated": p.last_updated
            }
            for p in profiles[-5:]  # Last 5
        ],
        "stats": stats
    })


@app.route("/api/profiles", methods=["GET"])
def list_profiles():
    """List all profiles with pagination"""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    
    profiles = datastore.get_all_profiles()
    total = len(profiles)
    
    start = (page - 1) * per_page
    end = start + per_page
    
    return jsonify({
        "total": total,
        "page": page,
        "per_page": per_page,
        "profiles": [
            {
                "name": p.name,
                "role": p.role,
                "company": p.company,
                "email": p.email,
                "linkedin": p.linkedin_url,
                "twitter": p.twitter_handle,
                "meeting_count": p.meeting_count,
                "last_updated": p.last_updated
            }
            for p in profiles[start:end]
        ]
    })


@app.route("/api/profile/<name>/<role>", methods=["GET"])
def get_profile(name, role):
    """Get specific profile"""
    profile = datastore.get_profile(name, role)
    
    if not profile:
        return jsonify({"error": "Profile not found"}), 404
    
    return jsonify({
        "name": profile.name,
        "role": profile.role,
        "company": profile.company,
        "email": profile.email,
        "linkedin": profile.linkedin_url,
        "twitter": profile.twitter_handle,
        "who_they_are": profile.who_they_are,
        "what_they_care": profile.what_they_care_about,
        "company_situation": profile.company_situation,
        "smart_questions": profile.smart_questions,
        "recent_news": profile.recent_news,
        "briefing": profile.briefing,
        "notes": profile.notes,
        "meeting_count": profile.meeting_count,
        "research_date": profile.research_date,
        "last_updated": profile.last_updated
    })


@app.route("/api/search", methods=["GET"])
def search():
    """Search profiles"""
    query = request.args.get("q", "")
    
    if not query:
        return jsonify({"results": []})
    
    results = datastore.search_profiles(query)
    
    return jsonify({
        "query": query,
        "results": [
            {
                "name": p.name,
                "role": p.role,
                "company": p.company,
                "meeting_count": p.meeting_count
            }
            for p in results
        ]
    })


@app.route("/api/research", methods=["POST"])
def trigger_research():
    """Trigger new research"""
    data = request.json
    
    result = engine.execute_research_workflow(
        name=data.get("name"),
        role=data.get("role"),
        company=data.get("company"),
        context=data.get("context"),
        email=data.get("email"),
        notify_email=data.get("notify_email")
    )
    
    return jsonify(result)


@app.route("/api/stats", methods=["GET"])
def get_stats():
    """Get database statistics"""
    stats = datastore.get_stats()
    profiles = datastore.get_all_profiles()
    
    # Additional stats
    recent = sorted(profiles, key=lambda p: p.last_updated, reverse=True)[:5]
    
    return jsonify({
        "total_profiles": stats["total_profiles"],
        "companies": stats["companies"],
        "with_linkedin": stats["with_linkedin"],
        "with_twitter": stats["with_twitter"],
        "total_meetings": stats["total_meetings"],
        "recent_profiles": [
            {
                "name": p.name,
                "role": p.role,
                "company": p.company,
                "last_updated": p.last_updated
            }
            for p in recent
        ]
    })


@app.route("/api/profile/<name>/<role>", methods=["POST"])
def update_profile(name, role):
    """Update profile notes"""
    profile = datastore.get_profile(name, role)
    
    if not profile:
        return jsonify({"error": "Profile not found"}), 404
    
    data = request.json
    
    if "notes" in data:
        profile.notes = data["notes"]
    
    if "email" in data:
        profile.email = data["email"]
    
    if "linkedin" in data:
        profile.linkedin_url = data["linkedin"]
    
    if "twitter" in data:
        profile.twitter_handle = data["twitter"]
    
    profile.last_updated = datetime.now().isoformat()
    datastore.save_profile(profile)
    
    return jsonify({"status": "updated", "profile": {
        "name": profile.name,
        "role": profile.role
    }})


@app.route("/api/profile/<name>/<role>", methods=["DELETE"])
def delete_profile_endpoint(name, role):
    """Delete profile"""
    success = datastore.delete_profile(name, role)
    
    if success:
        return jsonify({"status": "deleted"})
    else:
        return jsonify({"error": "Profile not found"}), 404


def run_dashboard(host="127.0.0.1", port=3000, debug=True):
    """Start web dashboard"""
    print(f"\n{'='*70}")
    print(f"[DASHBOARD] Starting web interface")
    print(f"{'='*70}")
    print(f"Access at: http://{host}:{port}")
    print(f"APIs available:")
    print(f"  GET  /api/profiles       - List all profiles")
    print(f"  GET  /api/search?q=...   - Search profiles")
    print(f"  GET  /api/profile/<name>/<role>  - Get specific profile")
    print(f"  POST /api/profile/<name>/<role>  - Update profile")
    print(f"  POST /api/research       - Trigger new research")
    print(f"  GET  /api/stats          - Database statistics")
    print(f"{'='*70}\n")
    
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    run_dashboard()
