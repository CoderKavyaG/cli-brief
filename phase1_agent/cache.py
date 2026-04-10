import json
import os
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from phase1_agent.config import CACHE_DIR

class BriefingCache:
    """Smart cache to avoid duplicate searches"""
    
    def __init__(self):
        os.makedirs(CACHE_DIR, exist_ok=True)
        self.cache_file = os.path.join(CACHE_DIR, "briefings_cache.json")
        self.cache_data: Dict[str, Any] = self._load_cache()
    
    def _load_cache(self) -> Dict[str, Any]:
        if os.path.exists(self.cache_file):
            with open(self.cache_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_cache(self):
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache_data, f, indent=2)
    
    def _get_cache_key(self, name: str, role: str) -> str:
        """Generate cache key from person info"""
        return f"{name.lower()}_{role.lower()}".replace(" ", "_")
    
    def get(self, name: str, role: str) -> Optional[Dict[str, Any]]:
        """Get briefing from cache if exists and not old (24h)"""
        key = self._get_cache_key(name, role)
        if key in self.cache_data:
            cached = self.cache_data[key]
            timestamp = datetime.fromisoformat(cached['timestamp'])
            age = datetime.now() - timestamp
            
            # Cache valid for 24 hours
            if age < timedelta(hours=24):
                print(f"[CACHE HIT] Using cached briefing for {name}")
                return cached
            else:
                print(f"[CACHE EXPIRED] Briefing for {name} is older than 24h, refreshing...")
                del self.cache_data[key]
                self._save_cache()
        
        return None
    
    def set(self, name: str, role: str, briefing_dict: Dict[str, Any]):
        """Store briefing in cache"""
        key = self._get_cache_key(name, role)
        self.cache_data[key] = briefing_dict
        self._save_cache()
        print(f"[CACHE SET] Stored briefing for {name}")
    
    def clear(self):
        """Clear entire cache"""
        self.cache_data = {}
        self._save_cache()
        print("[CACHE CLEARED]")
