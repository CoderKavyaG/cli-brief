"""
Retry and recovery logic for resilient operations
Handles timeouts, failures, and degraded service gracefully
"""

import time
from typing import Optional, List, Callable, Any
from phase1_agent.models import SearchResult

class RetryStrategy:
    """Manages retries with exponential backoff"""
    
    @staticmethod
    def with_backoff(func: Callable, max_retries: int = 3, initial_delay: float = 1.0) -> Any:
        """
        Execute function with exponential backoff retry
        
        Args:
            func: Function to execute
            max_retries: Maximum number of attempts
            initial_delay: Starting delay in seconds (doubles each retry)
        
        Returns: Function result or None if all retries fail
        """
        delay = initial_delay
        last_error = None
        
        for attempt in range(max_retries):
            try:
                result = func()
                if attempt > 0:
                    print(f"  [RECOVERED] Success on attempt {attempt + 1}/{max_retries}")
                return result
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    print(f"  [RETRY {attempt + 1}] Failed: {str(e)[:50]}... (waiting {delay}s)")
                    time.sleep(delay)
                    delay *= 2  # Exponential backoff
                else:
                    print(f"  [FAILED] All {max_retries} retries exhausted")
        
        return None


class SearchRecovery:
    """Fallback search strategies when primary searches fail"""
    
    @staticmethod
    def generate_fallback_queries(person_name: str, company: str, role: str) -> List[str]:
        """
        Generate progressively broader queries for fallback searches
        
        Fallback strategy (progressively broader):
        1. Specific: "Name Company Role"
        2. Broader: "Name Company"
        3. Broad: "Name Role"
        4. Generic: Just name
        """
        fallbacks = [
            f'"{person_name}" {company}',           # Specific to company
            f'{person_name} {role}',                # Role-based search
            f'{person_name} {company} recent',      # Recent activity
            f'{person_name}',                       # Just name
        ]
        return fallbacks
    
    @staticmethod
    def execute_with_fallback(primary_search_func: Callable, person_name: str, 
                            company: str, role: str, min_results: int = 3) -> List[SearchResult]:
        """
        Execute search with automatic fallback to broader queries
        
        Args:
            primary_search_func: Function that takes query and returns results
            person_name: Person's name
            company: Organization/company
            role: Person's role
            min_results: Minimum results needed before considering success
        
        Returns: List of search results
        """
        all_results = []
        
        # Try primary search first
        print("[SEARCH RECOVERY] Starting search sequence...")
        
        # Fallback queries, progressively broader
        fallback_queries = SearchRecovery.generate_fallback_queries(person_name, company, role)
        
        for i, query in enumerate(fallback_queries):
            print(f"  [FALLBACK {i+1}] Trying: {query}")
            
            try:
                results = primary_search_func(query)
                all_results.extend(results)
                
                if len(all_results) >= min_results:
                    print(f"  [SUCCESS] Got {len(all_results)} results, stopping fallback")
                    break
            except Exception as e:
                print(f"  [QUERY FAILED] {str(e)[:50]}...")
                continue
        
        if not all_results:
            print("[WARNING] No results from any fallback query")
            return []
        
        print(f"[RECOVERY COMPLETE] Collected {len(all_results)} results across fallback queries")
        return all_results


class ContentRecovery:
    """Handle scraping failures with built-in fallbacks"""
    
    @staticmethod
    def scrape_with_recovery(scrape_func: Callable, url: str, 
                           fallback_content: str = "") -> Optional[tuple]:
        """
        Attempt to scrape URL with graceful fallback
        
        Returns: (content, is_fallback)
        """
        try:
            content = scrape_func(url)
            if content and len(content.content.strip()) > 50:
                return content, False  # Successful scrape
            else:
                # Scrape succeeded but returned minimal content
                if fallback_content:
                    print(f"  [FALLBACK] Using snippet for {url[:50]}...")
                    return fallback_content, True
                return None, True
        except Exception as e:
            print(f"  [SCRAPE ERROR] {str(e)[:40]}...")
            # Fallback to snippet
            if fallback_content:
                print(f"  [FALLBACK] Using snippet as fallback")
                return fallback_content, True
            return None, True


class TimeoutHandler:
    """Manages timeouts gracefully"""
    
    @staticmethod
    def should_retry_on_timeout(attempt: int, max_retries: int = 3) -> bool:
        """Determine if timeout warrants a retry"""
        return attempt < max_retries
    
    @staticmethod
    def adaptive_timeout(base_timeout: float, attempt: int, max_timeout: float = 60.0) -> float:
        """
        Calculate adaptive timeout that increases with retry attempts
        (Some services are slow, but recover if given more time)
        """
        # Increase timeout with each retry: 10s → 15s → 20s
        timeout = base_timeout + (attempt * 5)
        return min(timeout, max_timeout)
