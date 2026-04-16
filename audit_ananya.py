#!/usr/bin/env python3
"""
COMPREHENSIVE AUDIT: Why Ananya Malhotra returns wrong data
"""

import os
import json
from dotenv import load_dotenv
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()

from phase1_agent.researcher import Researcher

NAME = "Ananya Malhotra"
COMPANY = "DevLearn"
ROLE = "Campus Lead"

print("\n" + "="*80)
print("AUDIT: Ananya Malhotra from DevLearn")
print("="*80)

print("\n[STEP 1] FIND_PERSON - Check if correct identity is locked")
print("-" * 80)

researcher = Researcher()
identity = researcher.find_person(NAME, COMPANY, ROLE, [])

print(f"\nIdentity after find_person():")
print(f"  Handle: {identity.get('handle')}")
print(f"  LinkedIn URL: {identity.get('linkedin_url')}")
print(f"  Verified: {identity.get('verified')}")
print(f"  Verification Source: {identity.get('verification_source')}")
print(f"  Twitter: {identity.get('twitter')}")
print(f"  Instagram: {identity.get('instagram')}")
print(f"  Personal Site: {identity.get('personal_site')}")

print("\n[STEP 2] SCRAPE_ALL - Check what sources are being scraped")
print("-" * 80)

sources = researcher.scrape_all(identity, NAME, COMPANY)

print(f"\nTotal sources scraped: {len(sources)}")
print("\nSources by type:")
for source in sources:
    print(f"  - {source['url'][:80]}")

print(f"\nIdentity after scrape_all():")
print(f"  Email: {identity.get('email')}")
print(f"  Email Source: {identity.get('email_source')}")
print(f"  LinkedIn URL: {identity.get('linkedin_url')}")
print(f"  Personal Site: {identity.get('personal_site')}")
print(f"  Extracted Identifiers:")
for key, val in identity.get('extracted_identifiers', {}).items():
    print(f"    {key}: {val}")

print("\n[STEP 3] CHECK LINKEDIN SCRAPE CONTENT")
print("-" * 80)

# Find LinkedIn source
linkedin_source = None
for source in sources:
    if 'linkedin.com' in source['url']:
        linkedin_source = source
        break

if linkedin_source:
    print(f"LinkedIn URL scraped: {linkedin_source['url']}")
    print(f"Content length: {len(linkedin_source['content'])} chars")
    print(f"\nFirst 500 chars:")
    print(linkedin_source['content'][:500])
    print(f"\nLooking for email pattern in content:")
    import re
    emails = re.findall(r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b', linkedin_source['content'])
    print(f"  Found emails: {emails}")
    print(f"\nLooking for person name mentions:")
    print(f"  'Ananya' in content: {'Ananya' in linkedin_source['content']}")
    print(f"  'Malhotra' in content: {'Malhotra' in linkedin_source['content']}")
else:
    print("No LinkedIn source found!")

print("\n[STEP 4] DEEP LINKING ANALYSIS")
print("-" * 80)
print(f"Linked platforms: {identity.get('linkage', {}).get('linked_platforms', [])}")
print(f"All identifiers: {identity.get('linkage', {}).get('all_identifiers', [])}")
print(f"Cross-platform matches: {identity.get('linkage', {}).get('cross_platform_matches', {})}")

print("\n" + "="*80)
print("END AUDIT")
print("="*80)
