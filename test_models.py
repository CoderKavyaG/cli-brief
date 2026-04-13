import os
import requests
from dotenv import load_dotenv

load_dotenv()
gemini_key = os.getenv('GEMINI_API_KEY')

# List available models
r = requests.get(
    f'https://generativelanguage.googleapis.com/v1/models?key={gemini_key}',
    timeout=10
)
print(f'Status: {r.status_code}')
import json
data = r.json()
# Print all models
print("Available models:")
for model in data.get('models', []):
    name = model.get('name', '').replace('models/', '')
    if 'flash' in name or '2.5' in name:
        print(f"  - {name}")
