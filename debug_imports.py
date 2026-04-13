#!/usr/bin/env python3
import sys
import traceback
from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("Testing import chain...")

try:
    print("\n1. Importing agent...")
    from phase1_agent.agent import IntelAgent
    print("   ✓ agent imported")
    
    print("\n2. Creating agent...")
    agent = IntelAgent()
    print(f"   ✓ agent created")
    print(f"   gemini_url: {agent.gemini_url}")
    print(f"   gemini_key: {agent.gemini_key[:20]}..." if agent.gemini_key else "   gemini_key: None")
    
except Exception as e:
    print(f"   ✗ Error: {e}")
    traceback.print_exc()

print("\n3. Checking anthropic import...")
try:
    import anthropic
    print(f"   ✓ anthropic is installed: {anthropic.__version__}")
except ImportError:
    print("   ✗ anthropic not installed")
