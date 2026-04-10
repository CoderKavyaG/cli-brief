"""
Validation and disambiguation layer
Ensures search results actually match the person you're researching
"""

from typing import List, Optional, Tuple
from phase1_agent.models import SearchResult, Person

class ResultValidator:
    """Validates search results match the input person"""
    
    @staticmethod
    def score_result(result: SearchResult, person: Person) -> float:
        """
        Score how well a search result matches the person.
        Returns 0.0 to 1.0 (higher = better match)
        
        Checks:
        - Person's name present
        - Organization matches (Chitkara, DevLearn, etc)
        - Role matches (Student, Founder, etc)
        """
        
        text = (result.title + " " + result.description).lower()
        person_lower = person.name.lower()
        
        score = 0.0
        
        # Base: name must be present
        if person_lower in text:
            score = 0.3  # Name present = baseline
        else:
            return 0.0  # Name not there = reject
        
        # Boost: organization mentioned
        if person.company and person.company.lower() in text:
            score += 0.4  # Strong signal
        
        # Boost: role mentioned
        if person.role and person.role.lower() in text:
            score += 0.2
        
        # Deduction: conflicting org (wrong university)
        conflicting = {
            "delhi university": ["chitkara", "iit", "bits"],
            "iit": ["chitkara", "delhi university"],
            "bits": ["chitkara", "delhi university"],
        }
        
        for org, conflicts in conflicting.items():
            if org in text:
                for conflict in conflicts:
                    if conflict in text and person.company and conflict not in person.company.lower():
                        score -= 0.3  # Likely wrong person
        
        return max(0.0, min(1.0, score))
    
    @staticmethod
    def filter_results(results: List[SearchResult], person: Person, min_score: float = 0.5) -> List[SearchResult]:
        """
        Filter and rank results by relevance to the person.
        Returns sorted list, best matches first.
        """
        scored = [
            (result, ResultValidator.score_result(result, person))
            for result in results
        ]
        
        # Sort by score descending
        scored.sort(key=lambda x: x[1], reverse=True)
        
        # Return only good matches
        filtered = [result for result, score in scored if score >= min_score]
        
        if filtered:
            print(f"[VALIDATION] Kept {len(filtered)}/{len(results)} results")
            for result, score in scored[:len(filtered)]:
                print(f"  → {result.title[:50]}... (score: {score:.2f})")
        else:
            print(f"[VALIDATION WARNING] No high-confidence matches found")
            print(f"  Top result scored: {scored[0][1]:.2f}")
            print(f"  Lowering threshold for next search...")
        
        return filtered if filtered else [results[0]]  # Fallback to top result if nothing good


class SearchRefinement:
    """Improves search queries based on context"""
    
    @staticmethod
    def generate_specific_queries(person: Person) -> List[str]:
        """
        Generate targeted search queries that include context
        to disambiguate the person.
        """
        queries = [
            # Query 1: Name + specific organization
            f'"{person.name}" "{person.company}"',
            
            # Query 2: Name + role + organization  
            f'"{person.name}" {person.role} {person.company}',
            
            # Query 3: Name + any work context if mentioned
            f'{person.name} {person.company}',
            
            # Query 4: Broader but with role
            f'{person.name} {person.role}',
        ]
        
        return queries


class AmbiguityResolver:
    """Detects and handles ambiguous/conflicting results"""
    
    @staticmethod
    def has_conflict(results: List[SearchResult], person: Person) -> Tuple[bool, str]:
        """
        Detect if results show conflicting information
        (e.g., person found at different organization than expected)
        
        Returns: (has_conflict, description)
        """
        
        orgs_found = set()
        
        for result in results[:5]:
            text = (result.title + " " + result.description).lower()
            
            # Extract organization mentions
            if "delhi" in text and "university" in text:
                orgs_found.add("Delhi University")
            if "chitkara" in text:
                orgs_found.add("Chitkara University")
            if "iit" in text:
                orgs_found.add("IIT")
            if "bits" in text:
                orgs_found.add("BITS")
            if "devlearn" in text:
                orgs_found.add("DevLearn")
        
        # Check for conflict
        if len(orgs_found) > 1 and person.company:
            expected_org = person.company
            found_different = [o for o in orgs_found if expected_org.lower() not in o.lower()]
            
            if found_different:
                msg = f"Found results showing {person.name} at different orgs: {found_different}. "
                msg += f"Expected: {expected_org}"
                return True, msg
        
        return False, ""
