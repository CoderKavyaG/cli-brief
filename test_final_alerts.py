#!/usr/bin/env python3
"""Quick test for alert fix"""
import requests

response = requests.post('http://localhost:5000/research', json={
    'name': 'Priya Kapoor',
    'role': 'Founder',
    'company': 'CloudSync',
    'context': 'cloud partnership'
}, timeout=180)

if response.status_code == 200:
    data = response.json()
    alerts = data.get('alerts', [])
    md = data.get('markdown', '')
    
    print(f"✅ Response received")
    print(f"Alerts in JSON: {len(alerts)}")
    print(f"Markdown length: {len(md)}")
    print(f"Markdown has 🔔: {'🔔' in md}")
    print(f"Markdown has Critical Meeting Intel: {'Critical Meeting Intel' in md}")
    print()
    print("First 600 chars of markdown:")
    print(md[:600])
else:
    print(f"❌ Error {response.status_code}: {response.json()}")
