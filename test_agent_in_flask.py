#!/usr/bin/env python3
"""Test what agent_url actually is in Flask context"""

import sys
import os
from dotenv import load_dotenv

# Load env FIRST
load_dotenv()

from flask import Flask, jsonify, request

# Test 1: After loading env
print(f"ENV after load_dotenv: GEMINI_API_KEY = {os.getenv('GEMINI_API_KEY')}")

# Test 2: Import and create agent in Flask app
from phase1_agent.agent import IntelAgent

app = Flask(__name__)

@app.route('/test-agent', methods=['GET'])
def test_agent():
    agent = IntelAgent()
    return jsonify({
        "gemini_url": agent.gemini_url,
        "gemini_key": agent.gemini_key[:20] if agent.gemini_key else "None",
        "python_version": sys.version
    })

if __name__ == '__main__':
    print("\n" + "="*60)
    print("Testing agent in Flask context")
    print("="*60)
    
    # Make a test request
    with app.test_client() as client:
        response = client.get('/test-agent')
        print(response.get_json())
