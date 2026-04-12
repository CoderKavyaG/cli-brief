#!/usr/bin/env python3
"""
Test Web UI Alert Rendering
Makes HTTP requests to verify alert rendering and web UI functionality
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000"

# Test cases with expected alert counts
test_cases = [
    {
        "name": "Deepinder Goyal",
        "role": "CEO",
        "company": "Blinkit",
        "context": "pitch supply chain optimization tool",
        "expected_alerts_min": 1,
        "label": "High-profile founder (should have alerts)"
    },
    {
        "name": "Priya Kapoor",
        "role": "Founder",
        "company": "CloudSync",
        "context": "cloud infrastructure partnership",
        "expected_alerts_min": 1,
        "label": "Known founder (should have alerts)"
    },
    {
        "name": "Sarah Chen",
        "role": "HR Manager",
        "company": "Google India",
        "context": "pitch employee wellness platform",
        "expected_alerts_min": 0,
        "label": "Low-profile HR (fewer alerts expected)"
    }
]

print("🧪 Testing Web UI Alert Rendering")
print("=" * 70)

for i, test in enumerate(test_cases, 1):
    print(f"\n{'='*70}")
    print(f"Test {i}: {test['label']}")
    print(f"{'='*70}")
    print(f"Name: {test['name']}")
    print(f"Role: {test['role']}")
    print(f"Company: {test['company']}")
    print(f"Context: {test['context']}")
    
    try:
        print("\n📤 Sending research request...")
        response = requests.post(
            f"{BASE_URL}/research",
            json={
                "name": test['name'],
                "role": test['role'],
                "company": test['company'],
                "context": test['context']
            },
            timeout=120
        )
        
        print(f"✅ Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Check required fields
            required_fields = ['html', 'markdown', 'context', 'alerts']
            print(f"\n📋 Response Fields:")
            for field in required_fields:
                has_field = field in data
                print(f"  {'✅' if has_field else '❌'} {field}")
            
            # Check context
            if 'context' in data:
                print(f"\n📝 Context: {data['context']}")
            
            # Check alerts
            if 'alerts' in data:
                alerts = data['alerts']
                print(f"\n🔔 Alerts Detected: {len(alerts)}")
                
                if len(alerts) > 0:
                    print(f"   Expected minimum: {test['expected_alerts_min']}")
                    print(f"   Result: {'✅ PASS' if len(alerts) >= test['expected_alerts_min'] else '⚠️ FEWER THAN EXPECTED'}")
                    
                    print(f"\n   Alert Details:")
                    for j, alert in enumerate(alerts, 1):
                        print(f"   {j}. {alert.get('emoji', '?')} {alert.get('label', 'Unknown')}")
                        print(f"      Type: {alert.get('type', 'N/A')}")
                        print(f"      Text: {alert.get('text', 'N/A')[:80]}...")
                        print(f"      Source: {alert.get('source', 'N/A')}")
                else:
                    print(f"   ⚠️ No alerts detected (expected minimum: {test['expected_alerts_min']})")
            
            # Check HTML rendering
            if 'html' in data:
                html_len = len(data['html'])
                print(f"\n🎨 HTML Content: {html_len:,} characters")
                
                # Check for alert box CSS classes
                alert_classes = ['alert-role', 'alert-funding', 'alert-controversy', 'alert-launch']
                has_alerts_in_html = any(cls in data['html'] for cls in alert_classes)
                print(f"   Alert CSS classes found: {'✅' if has_alerts_in_html else '❌'}")
                
                # Check for context banner
                has_context_banner = 'context-banner' in data['html']
                print(f"   Context banner: {'✅' if has_context_banner else '❌'}")
            
            # Check markdown
            if 'markdown' in data:
                md_len = len(data['markdown'])
                print(f"\n📄 Markdown Content: {md_len:,} characters")
                has_sources = '[Source:' in data['markdown']
                print(f"   Source citations found: {'✅' if has_sources else '❌'}")
                has_alerts_section = '🔔' in data['markdown']
                print(f"   Alerts section in markdown: {'✅' if has_alerts_section else '❌'}")
        
        else:
            error_data = response.json() if response.text else {}
            print(f"❌ Error: {error_data.get('error', 'Unknown error')}")
    
    except requests.exceptions.Timeout:
        print("❌ Request timed out (>120s)")
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - Flask server not running")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    # Small delay between tests
    if i < len(test_cases):
        print("\n⏳ Waiting 3 seconds before next test...")
        time.sleep(3)

print(f"\n{'='*70}")
print("✅ Web UI Test Complete!")
print("=" * 70)
