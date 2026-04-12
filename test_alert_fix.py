#!/usr/bin/env python3
"""Quick test for alert rendering"""
import requests
import json

response = requests.post('http://localhost:5000/research', json={
    'name': 'Deepinder Goyal',
    'role': 'CEO',
    'company': 'Blinkit',
    'context': 'supply chain pitch'
}, timeout=120)

if response.status_code == 200:
    data = response.json()
    
    print('🔔 ALERTS IN JSON RESPONSE:')
    print(f'Count: {len(data["alerts"])}')
    if data['alerts']:
        print(f'First alert: {data["alerts"][0]["emoji"]} {data["alerts"][0]["label"]}')
    print()
    print('📄 MARKDOWN FIRST 1000 CHARS:')
    print(data['markdown'][:1000])
    print()
    print('✅ contains 🔔:', '🔔' in data['markdown'])
    print('✅ contains Critical Meeting Intel:', 'Critical Meeting Intel' in data['markdown'])
else:
    print('Error:', response.json())
