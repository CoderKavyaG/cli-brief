import os
import requests
from dotenv import load_dotenv

load_dotenv()
gemini_key = os.getenv('GEMINI_API_KEY')

# Test lite model
r = requests.post(
    f'https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash-lite:generateContent?key={gemini_key}',
    json={
        'contents': [{'parts': [{'text': 'Say hello in one sentence.'}]}],
        'generationConfig': {'maxOutputTokens': 100}
    },
    headers={'Content-Type': 'application/json'},
    timeout=15
)
print(f'Status: {r.status_code}')
if r.status_code == 200:
    data = r.json()
    response_text = data['candidates'][0]['content']['parts'][0]['text']
    print(f'Response: {response_text}')
else:
    print(f'Error: {r.text[:300]}')
