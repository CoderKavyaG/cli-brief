import requests

r = requests.post('http://localhost:5000/research', json={
    'name': 'Ishan Kumar',
    'role': 'CEO',  
    'company': 'InTheBox',
    'context': 'packaging business'
}, timeout=120)

data = r.json()
print(f'Status: {r.status_code}')
if r.status_code != 200:
    print(f'Error: {data.get("error")}')
else:
    print(f'Confidence: {data.get("confidence")}')
    print(f'Sources: {len(data.get("sources", []))}')
    print(f'Who they are: {data.get("who_they_are", "")[:100]}')
