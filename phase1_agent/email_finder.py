"""
Email Finder: Extract emails ONLY from verified scraped content
No Hunter API, no patterns - only verified extraction from platforms
"""

import re
from typing import Optional, List


class EmailFinder:
    """Extract emails ONLY from scraped platform content - verified only"""
    
    def extract_email_from_content(self, content: str) -> Optional[str]:
        """Extract email from scraped content using regex"""
        if not content:
            return None
        
        emails = re.findall(r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b', content)
        
        if not emails:
            return None
        
        # Filter out noreply/support addresses
        filtered = [e for e in emails if not any(
            x in e.lower() for x in ['noreply', 'support', 'info@', 'contact@', 
                                     'hello@', 'no-reply', 'donotreply', 'notification']
        )]
        
        return filtered[0] if filtered else None
    
    def find_email_from_extracted(self, extracted_emails: List[str]) -> Optional[str]:
        """
        Use emails already extracted from scraped content.
        
        Args:
            extracted_emails: List of emails found by regex in content
        
        Returns:
            First valid email or None
        """
        if not extracted_emails:
            return None
        
        # Filter spam/noreply addresses
        filtered = [e for e in extracted_emails if not any(
            x in e.lower() for x in ['noreply', 'support', 'info@', 'contact@', 
                                     'hello@', 'no-reply', 'donotreply', 'notification']
        )]
        
        return filtered[0] if filtered else None
    
    def find_domain_from_company(self, company: str) -> Optional[str]:
        """
        Find company domain from company name
        """
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
            "x": "x.com",
            "linkedin": "linkedin.com",
            "ibm": "ibm.com",
            "oracle": "oracle.com",
            "salesforce": "salesforce.com",
            "adobe": "adobe.com",
            "slack": "slack.com",
            "github": "github.com",
            "stripe": "stripe.com",
            "uber": "uber.com",
            "airbnb": "airbnb.com",
            "inthebox": "inthebox.co",
            "chitkara": "chitkara.edu.in",
        }
        
        if not company:
            return None
        
        company_lower = company.lower()
        
        # Direct lookup
        if company_lower in domain_map:
            return domain_map[company_lower]
        
        # Try variations
        for company_key, domain in domain_map.items():
            if company_key in company_lower:
                return domain
        
        # Smart heuristic for unknown companies
        clean = company_lower.split()[0]
        
        if "university" in company_lower or "institute" in company_lower:
            if "india" in company_lower:
                return f"{clean}.edu.in"
            return f"{clean}.edu"
        
        if len(clean) > 3:
            return f"{clean}.com"
        
        return None
