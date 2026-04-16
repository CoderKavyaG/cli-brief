#!/usr/bin/env python3
"""
Debug tracer to see what data is being extracted at each stage
"""

import json
import sys
from phase1_agent.advanced_scraper import DeepProfileExtractor

# Sample content from a personal website
personal_site_content = """
Ishan Kumar
CMO - InTheBox

Email: ishan@inthebox.co
Contact: +91-9876543210

Twitter: https://twitter.com/ishankumax
GitHub: https://github.com/ishankumax
Instagram: https://www.instagram.com/ishankumax

InTheBox - Custom Premium Packaging Solutions

About:
I'm Ishan Kumar, CMO at InTheBox. We specialize in creating unique unboxing experiences.

Contact me at: hello@inthebox.co or ishan.kumar@chitkara.ac.in
"""

print("=" * 60)
print("CONTACT INFO EXTRACTION TEST")
print("=" * 60)

extractor = DeepProfileExtractor()
result = extractor.extract_contact_info(personal_site_content)

print("\nExtracted Emails:")
print(json.dumps(result.get("emails", []), indent=2))

print("\nExtracted Phones:")
print(json.dumps(result.get("phones", []), indent=2))

print("\nExtracted Links:")
print(json.dumps(result.get("links", []), indent=2))

print("\nExtracted Social Handles:")
print(json.dumps(result.get("social_handles", {}), indent=2))

print("\n" + "=" * 60)
