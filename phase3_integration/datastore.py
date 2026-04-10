"""
Phase 3: Person Data Storage & Management
Local database for storing researched person profiles
API for retrieving, updating, and searching person data
"""

import json
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from dataclasses import dataclass, asdict


@dataclass
class PersonProfile:
    """Person profile stored in database"""
    name: str
    role: str
    company: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    twitter_handle: Optional[str] = None
    
    # Research data
    briefing: str = ""
    who_they_are: str = ""
    what_they_care_about: str = ""
    company_situation: str = ""
    smart_questions: List[str] = None
    recent_news: List[str] = None
    
    # Metadata
    research_date: str = ""
    last_updated: str = ""
    notes: str = ""
    meeting_count: int = 0
    
    def __post_init__(self):
        if self.smart_questions is None:
            self.smart_questions = []
        if self.recent_news is None:
            self.recent_news = []


class PersonDataStore:
    """Local JSON database for person profiles"""
    
    def __init__(self, db_path: str = "data/people_database.json"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.data = self._load_database()
    
    def _load_database(self) -> Dict:
        """Load database from JSON file"""
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_database(self):
        """Save database to JSON file"""
        with open(self.db_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
    
    def _get_key(self, name: str, role: str) -> str:
        """Generate database key from name + role"""
        return f"{name.lower()}_{role.lower()}".replace(" ", "_")
    
    def save_profile(self, profile: PersonProfile) -> bool:
        """Save person profile to database"""
        try:
            key = self._get_key(profile.name, profile.role)
            
            # Update metadata
            if key in self.data:
                profile.meeting_count = self.data[key].get("meeting_count", 0) + 1
                profile.last_updated = datetime.now().isoformat()
            else:
                profile.research_date = datetime.now().isoformat()
                profile.last_updated = datetime.now().isoformat()
            
            self.data[key] = asdict(profile)
            self._save_database()
            
            print(f"[DB] Profile saved for {profile.name}")
            return True
        except Exception as e:
            print(f"[DB ERROR] Failed to save profile: {str(e)}")
            return False
    
    def get_profile(self, name: str, role: str) -> Optional[PersonProfile]:
        """Retrieve person profile from database"""
        key = self._get_key(name, role)
        
        if key in self.data:
            profile_dict = self.data[key]
            return PersonProfile(**profile_dict)
        
        return None
    
    def search_profiles(self, query: str) -> List[PersonProfile]:
        """Search profiles by name or company"""
        query = query.lower()
        results = []
        
        for key, profile_dict in self.data.items():
            profile = PersonProfile(**profile_dict)
            if query in profile.name.lower() or (profile.company and query in profile.company.lower()):
                results.append(profile)
        
        return results
    
    def get_all_profiles(self) -> List[PersonProfile]:
        """Get all stored profiles"""
        return [PersonProfile(**p) for p in self.data.values()]
    
    def delete_profile(self, name: str, role: str) -> bool:
        """Delete person profile"""
        key = self._get_key(name, role)
        
        if key in self.data:
            del self.data[key]
            self._save_database()
            print(f"[DB] Profile deleted for {name}")
            return True
        
        return False
    
    def get_stats(self) -> Dict:
        """Get database statistics"""
        profiles = self.get_all_profiles()
        
        return {
            "total_profiles": len(profiles),
            "companies": len(set(p.company for p in profiles if p.company)),
            "with_linkedin": len([p for p in profiles if p.linkedin_url]),
            "with_twitter": len([p for p in profiles if p.twitter_handle]),
            "total_meetings": sum(p.meeting_count for p in profiles)
        }
    
    def suggest_followup(self, name: str, role: str, days: int = 30) -> bool:
        """
        Suggest if followup is needed (not updated in X days)
        """
        profile = self.get_profile(name, role)
        
        if not profile:
            return False
        
        if profile.last_updated:
            last_update = datetime.fromisoformat(profile.last_updated)
            days_ago = (datetime.now() - last_update).days
            return days_ago >= days
        
        return True


# Global instance
_datastore = None

def get_datastore() -> PersonDataStore:
    """Get or create global datastore instance"""
    global _datastore
    if _datastore is None:
        _datastore = PersonDataStore()
    return _datastore
