import requests
import json

r = requests.post(
    'http://localhost:5000/research',
    json={
        'name': 'Ishan Kumar',
        'role': 'CEO',
        'company': 'InTheBox',
        'context': 'I want to discuss a packaging business plan'
    },
    timeout=120
)

print(f'Status: {r.status_code}')
data = r.json()

# Print key fields
print(f"\nConfidence: {data.get('confidence')}")
print(f"Identity: {data.get('identity')}")
print(f"Sources count: {len(data.get('sources', []))}")

print(f"\n--- WHO THEY ARE ---")
print(data.get('who_they_are', '[ERROR]')[:500])

print(f"\n--- WHAT THEY CARE ABOUT ---")
for item in data.get('what_they_care_about', [])[:3]:
    print(f"  - {item}")

print(f"\n--- COMPANY SITUATION ---")
print(data.get('company_situation', '[ERROR]')[:300])

print(f"\n--- FULL RESPONSE (first 1000 chars) ---")
print(json.dumps(data, indent=2)[:1000])
