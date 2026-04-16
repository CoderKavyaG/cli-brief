"""
Email Finder: Proactive email discovery using Hunter.io API + scrape fallback
Finds contact emails for people using their name, company, and domain
"""

import os
import requests
import re
from typing import Optional, Dict, List


class EmailFinder:
    """Find emails using Hunter.io API with local fallback extraction"""
    
    def __init__(self):
        self.hunter_api_key = os.getenv("HUNTER_API_KEY")
        self.hunter_enabled = bool(self.hunter_api_key)
        
        if self.hunter_enabled:
            print("[EMAIL FINDER] Hunter.io API enabled")
        else:
            print("[EMAIL FINDER] Hunter.io API not configured - using fallback extraction only")
    
    def find_email(self, name: str, company: str, domain: Optional[str] = None) -> Dict[str, any]:
        """
        Find email for a person using multiple strategies.
        
        Args:
            name: Person's full name
            company: Company name  
            domain: Company domain (e.g. "google.com"). If not provided, will search for it.
        
        Returns:
            {
                "email": "john@google.com" or None,
                "source": "hunter" | "extracted" | "none",
                "confidence": 0.0-1.0,
                "variants": ["j.smith@company.com", ...] (alternative formats)
            }
        """
        result = {
            "email": None,
            "source": "none",
            "confidence": 0.0,
            "variants": [],
            "finder_method": "none"
        }
        
        # STRATEGY 1: Hunter.io API (most reliable)
        if self.hunter_enabled and domain:
            hunter_result = self._hunter_find(name, domain)
            if hunter_result:
                return hunter_result
        
        # STRATEGY 2: Common email patterns (fallback)
        if domain:
            pattern_result = self._try_common_patterns(name, domain)
            if pattern_result:
                return pattern_result
        
        return result
    
    def _hunter_find(self, name: str, domain: str) -> Optional[Dict]:
        """Query Hunter.io API for email"""
        try:
            # Clean domain - remove www and protocol
            clean_domain = domain.replace("www.", "").replace("https://", "").replace("http://", "").split("/")[0]
            
            # Parse name
            name_parts = name.strip().split()
            first_name = name_parts[0] if name_parts else ""
            last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
            
            print(f"[HUNTER] Searching for {first_name} {last_name} @ {clean_domain}")
            
            # Query Hunter API
            url = "https://api.hunter.io/v2/email-finder"
            params = {
                "domain": clean_domain,
                "first_name": first_name,
                "last_name": last_name,
                "api_key": self.hunter_api_key
            }
            
            response = requests.get(url, params=params, timeout=5)
            data = response.json()
            
            if data.get("data") and data["data"].get("email"):
                email = data["data"]["email"]
                confidence = data["data"].get("confidence", 0) / 100.0  # Convert to 0-1
                sources = data["data"].get("sources", [])
                
                print(f"[HUNTER] ✓ Found: {email} (confidence: {confidence:.1%})")
                
                return {
                    "email": email,
                    "source": "hunter",
                    "confidence": confidence,
                    "variants": self._generate_variants(first_name, last_name, clean_domain),
                    "finder_method": "hunter_api"
                }
            else:
                print(f"[HUNTER] Not found in Hunter database")
                return None
                
        except Exception as e:
            print(f"[HUNTER] Error: {str(e)[:60]}")
            return None
    
    def _try_common_patterns(self, name: str, domain: str) -> Optional[Dict]:
        """Try common email patterns based on name + domain"""
        # Clean domain
        clean_domain = domain.replace("www.", "").replace("https://", "").replace("http://", "").split("/")[0]
        
        # Parse name
        name_clean = name.strip().lower()
        name_parts = name_clean.split()
        
        if not name_parts or len(name_parts) < 1:
            return None
        
        first = name_parts[0]
        last = name_parts[-1] if len(name_parts) > 1 else ""
        
        # Common patterns to try (in order of likelihood)
        patterns = [
            f"{first}.{last}@{clean_domain}",      # first.last@company.com
            f"{first}{last}@{clean_domain}",        # firstlast@company.com
            f"{first}@{clean_domain}",              # first@company.com
            f"{first}_{last}@{clean_domain}",       # first_last@company.com
            f"{first}-{last}@{clean_domain}",       # first-last@company.com
        ]
        
        print(f"[PATTERNS] Trying common formats for {name} @ {clean_domain}")
        
        # Generate all variants to return even if we don't verify
        variants = list(set(patterns))
        
        # For now, return all patterns as possibilities (could add SMTP verification here)
        return {
            "email": patterns[0],  # Most likely pattern
            "source": "pattern",
            "confidence": 0.6,     # Lower confidence than verified
            "variants": variants,
            "finder_method": "common_patterns"
        }
    
    def _generate_variants(self, first_name: str, last_name: str, domain: str) -> List[str]:
        """Generate email format variants for a person"""
        variants = [
            f"{first_name}.{last_name}@{domain}",
            f"{first_name}{last_name}@{domain}",
            f"{first_name}@{domain}",
            f"{first_name[0]}{last_name}@{domain}",
            f"{first_name}_{last_name}@{domain}",
            f"{first_name}-{last_name}@{domain}",
        ]
        return list(set(variants))
    
    def extract_email_from_content(self, content: str) -> Optional[str]:
        """Extract email from scraped content using regex"""
        if not content:
            return None
        
        # Email regex
        emails = re.findall(r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b', content)
        
        if emails:
            # Filter out common noreply and support emails
            filtered = [e for e in emails if not any(
                x in e.lower() for x in ['noreply', 'support', 'info@', 'contact@', 
                                         'hello@', 'no-reply', 'donotreply', 'notification']
            )]
            
            if filtered:
                return filtered[0]
        
        return None
    
    def find_domain_from_company(self, company: str) -> Optional[str]:
        """
        Try to find company domain from company name.
        Note: This is a fallback - better to have domain from LinkedIn scrape
        """
        # Common patterns
        domain_map = {
            "google": "google.com",
            "microsoft": "microsoft.com",
            "amazon": "amazon.com",
            "apple": "apple.com",
            "meta": "meta.com",
            "facebook": "facebook.com",
            "netflix": "netflix.com",
            "tesla": "tesla.com",
            "twitter": "twitter.com",
            "linkedin": "linkedin.com",
            "ibm": "ibm.com",
            "oracle": "oracle.com",
            "salesforce": "salesforce.com",
        }
        
        company_lower = company.lower()
        
        # Direct lookup
        if company_lower in domain_map:
            return domain_map[company_lower]
        
        # Try variations
        for company_key, domain in domain_map.items():
            if company_key in company_lower:
                return domain
        
        return None
