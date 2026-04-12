import requests
import json
from datetime import datetime

tests = [
    {
        "name": "Test 1: HR Manager - Tech Company",
        "payload": {
            "name": "Sarah Chen",
            "role": "Head of Talent",
            "company": "Google India",
            "context": "pitch employee wellness platform for tech companies"
        }
    },
    {
        "name": "Test 2: Student - University",
        "payload": {
            "name": "Rohan Sharma",
            "role": "Student",
            "company": "IIT Delhi",
            "context": "startup pitch in hackathon - AI-based study tool"
        }
    },
    {
        "name": "Test 3: Startup Founder",
        "payload": {
            "name": "Priya Kapoor",
            "role": "Founder",
            "company": "CloudSync",
            "context": "pitch cloud infrastructure partnership"
        }
    },
    {
        "name": "Test 4: Project Manager",
        "payload": {
            "name": "Amit Patel",
            "role": "Project Manager",
            "company": "TCS",
            "context": "pitch project management automation tool"
        }
    }
]

print("="*80)
print("RUNNING DIVERSE TESTS - HR, Students, Different Roles")
print("="*80)

for test in tests:
    print(f"\n{'='*80}")
    print(f"{test['name']}")
    print(f"{'='*80}")
    
    payload = test['payload']
    
    try:
        response = requests.post('http://localhost:5000/research', json=payload, timeout=120)
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"\n✅ SUCCESS")
            print(f"   Name: {data.get('person')}")
            print(f"   Company: {data.get('company')}")
            print(f"   Context: {data.get('context')}")
            
            alerts = data.get('alerts', [])
            print(f"\n   Alerts Detected: {len(alerts)}")
            
            if alerts:
                for i, alert in enumerate(alerts, 1):
                    print(f"   {i}. {alert['emoji']} {alert['label']}")
                    print(f"      → {alert['text'][:80]}...")
            else:
                print(f"   No critical alerts")
            
            # Extract briefing preview
            md = data.get('markdown', '')
            lines = md.split('\n')
            
            # Find first substantive section after intro
            print(f"\n   Briefing Preview:")
            in_section = False
            line_count = 0
            for line in lines:
                if '## Who' in line or '## What' in line:
                    in_section = True
                if in_section:
                    print(f"   {line}")
                    line_count += 1
                    if line_count > 6:
                        break
            
            print(f"\n   ✓ Full briefing generated successfully")
        else:
            print(f"\n❌ FAILED - Status {response.status_code}")
            print(f"   Error: {response.json().get('error', 'Unknown error')}")
    
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")

print(f"\n{'='*80}")
print("ALL TESTS COMPLETE")
print(f"{'='*80}")
