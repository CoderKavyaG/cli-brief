import os
import requests
from dotenv import load_dotenv

load_dotenv()

gemini_key = os.getenv('GEMINI_API_KEY')
gemini_url = "https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash-lite:generateContent"

payload = {
    'contents': [{
        'parts': [{'text': 'Say hello in one sentence.'}]
    }],
    'generationConfig': {
        'maxOutputTokens': 50
    }
}

print(f"Testing: {gemini_url}")
print(f"With key: {gemini_key[:20]}...")

r = requests.post(
    f'{gemini_url}?key={gemini_key}',
    json=payload,
    headers={'Content-Type': 'application/json'},
    timeout=30
)

print(f"\nStatus: {r.status_code}")
print(f"Response: {r.text[:250]}")
