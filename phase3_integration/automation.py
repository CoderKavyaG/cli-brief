"""
Phase 3: n8n Integration & Email Automation
Triggers research, stores data, and sends email notifications
"""

import json
from datetime import datetime
from typing import Optional, Dict
from phase2_enhanced_briefing.generator import EnhancedBriefingGenerator
from phase3_integration.datastore import get_datastore, PersonProfile
from phase1_agent.models import Person


class ResearchAutomationEngine:
    """
    Orchestrates research → storage → email notification
    Can be triggered by n8n webhook or scheduled job
    """
    
    def __init__(self):
        self.generator = EnhancedBriefingGenerator()
        self.datastore = get_datastore()
    
    def execute_research_workflow(
        self,
        name: str,
        role: str,
        company: Optional[str] = None,
        context: Optional[str] = None,
        email: Optional[str] = None,
        notify_email: Optional[str] = None
    ) -> Dict:
        """
        Complete workflow:
        1. Generate enhanced briefing
        2. Store in database
        3. Return for email notification
        
        Args:
            name: Person's name
            role: Their role
            company: Company/org
            context: Meeting context
            email: Person's email (to store)
            notify_email: Email to send briefing to
        
        Returns:
            Result dict with briefing and metadata
        """
        
        print(f"\n{'='*70}")
        print(f"[AUTOMATION] Research Workflow Started")
        print(f"{'='*70}")
        print(f"Target: {name} ({role}) at {company or 'N/A'}")
        
        try:
            # Step 1: Generate enhanced briefing
            print(f"\n[STEP 1] Generating enhanced briefing...")
            person = Person(name=name, role=role, company=company, context=context)
            briefing = self.generator.generate_context_aware_briefing(person, context)
            
            if not briefing:
                return {
                    "success": False,
                    "error": "Failed to generate briefing",
                    "timestamp": datetime.now().isoformat()
                }
            
            # Step 2: Create profile and store
            print(f"\n[STEP 2] Storing profile in database...")
            profile = PersonProfile(
                name=name,
                role=role,
                company=company,
                email=email,
                briefing=briefing.to_markdown(),
                who_they_are=briefing.who_they_are,
                what_they_care_about=briefing.what_they_care_about,
                company_situation=briefing.company_situation,
                smart_questions=briefing.smart_questions,
                notes=f"Context: {context}" if context else ""
            )
            
            self.datastore.save_profile(profile)
            
            # Step 3: Prepare email payload
            print(f"\n[STEP 3] Preparing email notification...")
            email_payload = {
                "success": True,
                "person": {
                    "name": name,
                    "role": role,
                    "company": company,
                    "email": email
                },
                "briefing": {
                    "who_they_are": briefing.who_they_are[:200],
                    "what_they_care": briefing.what_they_care_about[:200],
                    "meeting_approach": briefing.meeting_approach[:300],
                    "smart_questions": briefing.smart_questions,
                    "things_to_avoid": briefing.things_to_avoid
                },
                "full_briefing_url": self._generate_briefing_url(name, role),
                "notify_email": notify_email,
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"\n✓ Workflow completed successfully")
            return email_payload
        
        except Exception as e:
            print(f"\n✗ Workflow failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _generate_briefing_url(self, name: str, role: str) -> str:
        """Generate URL to briefing in web dashboard"""
        key = f"{name.lower()}_{role.lower()}".replace(" ", "_")
        return f"http://localhost:3000/briefing/{key}"
    
    def batch_research(self, people: list) -> Dict:
        """
        Research multiple people
        
        Args:
            people: List of dicts with name, role, company, context
        
        Returns:
            Results dict with success count
        """
        results = {
            "total": len(people),
            "successful": 0,
            "failed": 0,
            "details": []
        }
        
        for person_data in people:
            result = self.execute_research_workflow(**person_data)
            
            if result.get("success"):
                results["successful"] += 1
                results["details"].append({
                    "name": person_data["name"],
                    "status": "✓ Success"
                })
            else:
                results["failed"] += 1
                results["details"].append({
                    "name": person_data["name"],
                    "status": f"✗ Failed: {result.get('error')}"
                })
        
        return results


def create_n8n_webhook_handler():
    """
    Returns a function that handles n8n webhook calls
    
    n8n JSON body should be:
    {
        "name": "Person Name",
        "role": "Role",
        "company": "Company",
        "context": "Meeting context",
        "email": "person@email.com",
        "notify_email": "your@email.com"
    }
    """
    
    engine = ResearchAutomationEngine()
    
    def handle_webhook(webhook_data: Dict) -> Dict:
        """Handle incoming n8n webhook"""
        return engine.execute_research_workflow(
            name=webhook_data.get("name"),
            role=webhook_data.get("role"),
            company=webhook_data.get("company"),
            context=webhook_data.get("context"),
            email=webhook_data.get("email"),
            notify_email=webhook_data.get("notify_email")
        )
    
    return handle_webhook
