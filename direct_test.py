#!/usr/bin/env python3
"""Direct test of research without Flask"""

import sys
sys.path.insert(0, '/Users/Kavya/Projects/aadmi dhundho yojna')

from dotenv import load_dotenv
load_dotenv()

from phase1_agent.agent import IntelAgent

# Test directly
agent = IntelAgent()
result = agent.research(
    name="Ishan Kumar",
    role="CEO",
    company="InTheBox",
    context="I want to discuss a packaging business plan"
)

print("\n\n=== RESULT ===")
print(f"Confidence: {result['confidence']}")
print(f"Sources: {len(result['sources'])}")
print(f"\nWho they are: {result['who_they_are'][:200]}")
