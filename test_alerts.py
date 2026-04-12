import requests
import json

print("\n" + "="*70)
print("TEST 1: DEEPINDER GOYAL - ROLE CHANGE ALERT EXPECTED")
print("="*70)

payload = {
    'name': 'Deepinder Goyal',
    'role': 'CEO',
    'company': 'Zomato',
    'context': 'pitch restaurant analytics tool'
}

response = requests.post('http://localhost:5000/research', json=payload, timeout=120)

if response.status_code == 200:
    data = response.json()
    
    print(f"\n📋 Context: {data.get('context')}")
    print(f"🔍 Alerts detected: {len(data.get('alerts', []))}")
    print()
    
    if data.get('alerts'):
        print("🚨 CRITICAL ALERTS FOUND:")
        print("-" * 70)
        for i, alert in enumerate(data['alerts'], 1):
            print(f"\n{i}. {alert['emoji']} {alert['label']}")
            print(f"   Text: {alert['text'][:120]}...")
            print(f"   Source: {alert['source']}")
            print(f"   URL: {alert['url'][:70]}...")
    else:
        print("⚠️  No alerts detected")
    
    # Check markdown
    md = data.get('markdown', '')
    if '## 🔔 Critical Meeting Intel' in md:
        print("\n✅ Alerts section present in markdown")
    
    print("\n" + "="*70)
else:
    print(f"❌ Error: {response.status_code}")
    print(response.text[:500])
