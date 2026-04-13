#!/usr/bin/env python3
"""Test /research endpoint using Flask test client"""

import json
import sys

# Add current directory to path
sys.path.insert(0, '.')

# Import app
import app as app_module

# Create test client
client = app_module.app.test_client()

print("="*60)
print("Testing /research endpoint")
print("="*60)

# Make request
data = {
    'name': 'Ishan Kumar',
    'role': 'CEO',
    'company': 'InTheBox',
    'context': 'I want to discuss a packaging business plan'
}

print(f"\nSending request with data: {data}\n")

response = client.post(
    '/research',
    data=json.dumps(data),
    content_type='application/json'
)

print(f"Response status: {response.status_code}")
result = response.get_json()

if response.status_code == 200:
    print(f"✓ Success!")
    print(f"\nConfidence: {result.get('confidence')}")
    print(f"Sources: {len(result.get('sources', []))}")
    print(f"\nWho they are: {result.get('who_they_are', '')[:200]}...")
else:
    print(f"✗ Error")
    print(f"Error: {result.get('error')}")
