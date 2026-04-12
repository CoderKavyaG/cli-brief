#!/usr/bin/env python3
"""Test alert rendering with Priya Kapoor (founder)"""
import requests
import time

test_name = "Priya Kapoor"
test_role = "Founder"
test_company = "CloudSync"
test_context = "cloud infrastructure partnership"

print(f"\n🧪 Testing {test_name} ({test_role} at {test_company})")
print("=" * 60)

try:
    response = requests.post('http://localhost:5000/research', json={
        'name': test_name,
        'role': test_role,
        'company': test_company,
        'context': test_context
    }, timeout=180)

    print(f"✅ Response Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        alerts = data.get('alerts', [])
        md = data.get('markdown', '')
        
        print(f"\n🔔 Alerts Detected: {len(alerts)}")
        for i, alert in enumerate(alerts, 1):
            print(f"  {i}. {alert['emoji']} {alert['label']}")
        
        print(f"\n📄 Markdown Content Check:")
        print(f"   - Contains '🔔': {('🔔' in md)}")
        print(f"   - Contains 'Critical Meeting Intel': {('Critical Meeting Intel' in md)}")
        print(f"   - Length: {len(md)} chars")
        
        print(f"\n📋 First 500 chars of markdown:")
        print(md[:500])
        
        if '🔔' in md:
            print(f"\n✅ SUCCESS! Alerts are in markdown!")
        else:
            print(f"\n❌ ISSUE: Alerts not found in markdown despite JSON having {len(alerts)} alerts")
            
    else:
        print(f"❌ Error: {response.json()}")
        
except Exception as e:
    print(f"❌ Exception: {str(e)}")
