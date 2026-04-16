#!/usr/bin/env python3
"""
Debug test with Chitkara University company
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
COMPANY = "Chitkara University"  # <-- THIS IS THE DIFFERENCE
ROLE = "CMO"
HANDLE = "iskumar"  # Optional hint

print("\n" + "=" * 80)
print(f"Testing: {NAME} ({ROLE} at {COMPANY})")
print("=" * 80 + "\n")

print("[1] Finding person...")
researcher = Researcher()
identity = researcher.find_person(NAME, COMPANY, ROLE, [])

print("\n[RESULTS AFTER find_person():]")
print(f"  Handle: {identity.get('handle')}")
print(f"  LinkedIn: {identity.get('linkedin_url')}")
print(f"  Personal Site: {identity.get('personal_site')}")
print(f"  Company Domain: {identity.get('company_domain')}")
print(f"  Instagram: {identity.get('instagram')}")
print(f"  Twitter: {identity.get('twitter')}")
print(f"  Verified: {identity.get('verified')}")

print("\n[2] Scraping sources...")
sources = researcher.scrape_all(identity, NAME, COMPANY)

print(f"\n[RESULTS AFTER scrape_all():]")
print(f"  Email Found: {identity.get('email')}")
print(f"  Email Source: {identity.get('email_source')}")
print(f"  LinkedIn: {identity.get('linkedin_url')}")
print(f"  Personal Site: {identity.get('personal_site')}")
print(f"  Company Domain: {identity.get('company_domain')}")
print(f"  GitHub: {identity.get('github')}")
print(f"  Twitter: {identity.get('twitter')}")
print(f"  Instagram: {identity.get('instagram')}")

print(f"\n  Extracted Identifiers:")
extracted = identity.get('extracted_identifiers', {})
for key, val in extracted.items():
    print(f"    {key}: {val}")
