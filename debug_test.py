#!/usr/bin/env python3
"""
Quick test to verify email extraction is working
"""

import os
import json
from dotenv import load_dotenv

load_dotenv()

# Set UTF-8 encoding for output on Windows
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from phase1_agent.researcher import Researcher

NAME = "Ishan Kumar"
COMPANY = "InTheBox"
ROLE = "CMO"

print("\n" + "=" * 80)
print(f"Testing: {NAME} ({ROLE} at {COMPANY})")
print("=" * 80 + "\n")

print("[1] Finding person...")
researcher = Researcher()
identity = researcher.find_person(NAME, COMPANY, ROLE, [])

print("\nAfter find_person():")
print(f"  LinkedIn Handle: {identity.get('handle')}")
print(f"  Personal Site: {identity.get('personal_site')}")
print(f"  GitHub: {identity.get('github')}")
print(f"  Twitter: {identity.get('twitter')}")
print(f"  Instagram: {identity.get('instagram')}")
print(f"  Email: {identity.get('email')}")
print(f"  Verified: {identity.get('verified')}")

print("\n[2] Scraping sources...")
sources = researcher.scrape_all(identity, NAME, COMPANY)

print(f"\nAfter scrape_all():")
print(f"  Sources collected: {len(sources)}")
print(f"  Email: {identity.get('email')}")
print(f"  Email Source: {identity.get('email_source')}")
print(f"  GitHub: {identity.get('github')}")
print(f"  Twitter: {identity.get('twitter')}")
print(f"  Instagram: {identity.get('instagram')}")
print(f"  Extracted IDs: {json.dumps(identity.get('extracted_identifiers', {}), indent=2)}")

print("\n[3] What app.py will return:")
result = {
    "email": identity.get("email"),
    "email_source": identity.get("email_source"),
    "linkedin_handle": identity.get("handle"),
    "twitter_url": identity.get("twitter"),
    "github_url": identity.get("github"),
    "personal_site_url": identity.get("personal_site"),
    "instagram_url": identity.get("instagram"),
}
print(json.dumps(result, indent=2))

print("\n" + "=" * 80)
