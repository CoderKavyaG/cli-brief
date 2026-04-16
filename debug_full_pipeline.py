#!/usr/bin/env python3
"""
Full pipeline debugger - trace data from search → scrape → extract → synthesis
"""

import json
import sys
import os
from dotenv import load_dotenv

load_dotenv()

from phase1_agent.researcher import Researcher
from phase1_agent.agent import IntelAgent

# Test case
NAME = "Ishan Kumar"
ROLE = "CMO"
COMPANY = "InTheBox"
CONTEXT = "discuss packaging products"

print("\n" + "=" * 80)
print(f"DEBUG PIPELINE: {NAME} ({ROLE} at {COMPANY})")
print("=" * 80 + "\n")

# Step 1: Find person
print("[STEP 1] FINDING PERSON - find_person()")
print("-" * 80)
researcher = Researcher()
identity = researcher.find_person(NAME, COMPANY, ROLE, [])

print(f"\nIdentity after find_person():")
print(json.dumps({
    "handle": identity.get("handle"),
    "linkedin_url": identity.get("linkedin_url"),
    "personal_site": identity.get("personal_site"),
    "github": identity.get("github"),
    "twitter": identity.get("twitter"),
    "instagram": identity.get("instagram"),
    "email": identity.get("email"),  # Should be None here
    "verified": identity.get("verified"),
}, indent=2))

# Step 2: Scrape all
print("\n[STEP 2] SCRAPING - scrape_all()")
print("-" * 80)
sources = researcher.scrape_all(identity, NAME, COMPANY)

print(f"\nIdentity after scrape_all():")
print(json.dumps({
    "handle": identity.get("handle"),
    "linkedin_url": identity.get("linkedin_url"),
    "personal_site": identity.get("personal_site"),
    "github": identity.get("github"),
    "twitter": identity.get("twitter"),
    "instagram": identity.get("instagram"),
    "email": identity.get("email"),  # Should have email now!
    "email_source": identity.get("email_source"),
    "extracted_identifiers": identity.get("extracted_identifiers"),
}, indent=2))

print(f"\nSources collected: {len(sources)}")
for i, src in enumerate(sources, 1):
    print(f"  {i}. {src['url'][:60]} - {len(src['content'])} chars")

# Step 3: Check agent.py's synthesize
print("\n[STEP 3] SYNTHESIS - agent._synthesize()")
print("-" * 80)

agent = IntelAgent()
# Manually build what agent.py does
print(f"\nWhat agent returns for Connect fields:")
print(json.dumps({
    "email": identity.get("email"),
    "email_source": identity.get("email_source"),
    "linkedin_handle": identity.get("handle"),
    "twitter_url": identity.get("twitter"),
    "github_url": identity.get("github"),
    "personal_site_url": identity.get("personal_site"),
    "instagram_url": identity.get("instagram"),
}, indent=2))

print("\n" + "=" * 80)
print("END DEBUG")
print("=" * 80)
