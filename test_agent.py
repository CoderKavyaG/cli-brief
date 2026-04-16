#!/usr/bin/env python3
"""
Test the full agent pipeline end-to-end
"""

import os
import json
from dotenv import load_dotenv

load_dotenv()

# Set UTF-8 encoding for output on Windows
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from phase1_agent.agent import IntelAgent

NAME = "Ishan Kumar"
COMPANY = "Chitkara University"
ROLE = "CMO"
CONTEXT = "Testing email extraction and personal site improvements"

print("\n" + "=" * 80)
print(f"AGENT TEST: {NAME} ({ROLE} at {COMPANY})")
print("=" * 80 + "\n")

agent = IntelAgent()
result = agent.research(NAME, ROLE, COMPANY, CONTEXT, [])

print("\n\n" + "=" * 80)
print("FINAL AGENT RESULT")
print("=" * 80)
print(f"Email: {result.get('email')}")
print(f"Email Source: {result.get('email_source')}")
print(f"Personal Site: {result.get('personal_site_url')}")
print(f"Twitter: {result.get('twitter_url')}")
print(f"LinkedIn Handle: {result.get('linkedin_handle')}")
print(f"Instagram: {result.get('instagram_url')}")
print(f"Confidence: {result.get('confidence')}")
print(f"\nIdentity Object Email: {result['identity'].get('email')}")
print(f"Identity Object Personal Site: {result['identity'].get('personal_site')}")
