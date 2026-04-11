#!/usr/bin/env python3
"""Test the interactive profile selector"""

from phase1_agent.profile_selector import ProfileSelector
from phase1_agent.models import Person

def test_selector():
    person = Person(name='Ananya Malhotra', role='Student', company='Chitkara University')
    selector = ProfileSelector()
    
    print("\n[TEST] Interactive Profile Selector - Ananya Malhotra\n")
    results = selector.search_profiles(person, limit=5)
    
    print(f"\n{'=' * 80}")
    print(f"SEARCH RESULTS: Found {len(results)} profiles")
    print(f"{'=' * 80}\n")
    
    for i, result in enumerate(results[:5], 1):
        print(f"[{i}] {result['title']}")
        print(f"    Profile ID: {result['profile_id']}")
        print(f"    URL: {result['url']}")
        print(f"    Confidence: {result['confidence']}%")
        print(f"    Summary: {result['description'][:80]}...")
        print()

if __name__ == "__main__":
    test_selector()
