"""
Main Entry Point: Interactive Research CLI
Makes it easy for anyone to research people
1. Search for person (sees all results with IDs)
2. Confirm which profile is correct
3. Run research on confirmed profile
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from phase1_agent.main import IntelAgent
from phase1_agent.models import Person
from phase1_agent.profile_selector import interactive_profile_search
from phase2_enhanced_briefing.generator import EnhancedBriefingGenerator


def main():
    """Interactive research workflow"""
    
    print(f"\n{'=' * 80}")
    print("AADMI DHUNDHO YOJANA - RESEARCH SYSTEM")
    print(f"{'=' * 80}\n")
    print("Easy way to research anyone: Just give us their name, role, company")
    print("We'll find them, show you the profiles, and you confirm!\n")
    
    # Get input from user
    if len(sys.argv) >= 4:
        name = sys.argv[1]
        role = sys.argv[2]
        company = sys.argv[3]
        context = sys.argv[4] if len(sys.argv) > 4 else ""
    else:
        print("📝 Tell us about the person you want to research:\n")
        name = input("Name: ").strip()
        role = input("Role (e.g., CEO, Student, VP Product): ").strip()
        company = input("Company/Organization: ").strip()
        context = input("Meeting context (optional): ").strip()
    
    if not name or not role or not company:
        print("❌ Name, role, and company are required")
        sys.exit(1)
    
    # Step 1: Search and show results
    print("\n[STEP 1] Searching for profiles...")
    profile = interactive_profile_search(name, role, company, context)
    
    if not profile:
        print("\n❌ No profile selected. Exiting.")
        sys.exit(1)
    
    # Step 2: Run research
    print("\n[STEP 2] Running research on confirmed profile...")
    print("(This will take 50-80 seconds)\n")
    
    # Ask which phase
    print("\nWhich research would you like?")
    print("  1) Quick Research (Phase 1) - 50 seconds")
    print("  2) Deep Research (Phase 2) - 60-85 seconds")
    print("  3) Both\n")
    
    if len(sys.argv) > 5:
        choice = sys.argv[5]
    else:
        choice = input("Choice (1/2/3, default 1): ").strip() or "1"
    
    # Create person object
    person = Person(name=name, role=role, company=company, context=context)
    
    # Run requested research
    if choice in ["1", "3"]:
        print("\n" + "=" * 80)
        print("PHASE 1: QUICK RESEARCH")
        print("=" * 80 + "\n")
        agent = IntelAgent()
        briefing_p1 = agent.research(person)
        
        if briefing_p1:
            print("✓ Phase 1 complete!")
            print(f"  Briefing saved to: /output/briefing_{name.lower().replace(' ', '_')}_{briefing_p1.timestamp.split('T')[0]}.md")
    
    if choice in ["2", "3"]:
        print("\n" + "=" * 80)
        print("PHASE 2: DEEP RESEARCH (Multi-source)")
        print("=" * 80 + "\n")
        generator = EnhancedBriefingGenerator()
        briefing_p2 = generator.generate_context_aware_briefing(person)
        
        if briefing_p2:
            print("✓ Phase 2 complete!")
            print(f"  Social handles found: {len(briefing_p2.social_handles or {})}")
            if briefing_p2.social_handles:
                for platform, handle in briefing_p2.social_handles.items():
                    print(f"    • {platform}: {handle}")
    
    print("\n" + "=" * 80)
    print("✓ RESEARCH COMPLETE")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
