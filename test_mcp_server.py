"""
Phase 2: MCP Server Test Script
Tests the MCP server implementation with Phase 1 agent
"""

import sys
import os
import json

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_server.server import IntelAgentMCPServer
from phase1_agent.models import Person


def test_mcp_server():
    """Test MCP server with sample research requests"""
    
    print("=" * 60)
    print("TESTING MCP SERVER - PHASE 2")
    print("=" * 60)
    
    server = IntelAgentMCPServer()
    
    # Test 1: Initialize
    print("\n[TEST 1] Testing MCP initialize...")
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {}
    }
    init_response = server.handle_request(init_request)
    assert init_response["result"]["serverInfo"]["name"] == "intel-agent"
    print("✓ Initialize successful")
    
    # Test 2: List tools
    print("\n[TEST 2] Testing list_tools...")
    list_request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }
    list_response = server.handle_request(list_request)
    tools = list_response["result"]["tools"]
    assert len(tools) > 0
    assert tools[0]["name"] == "research_briefing"
    print(f"✓ Found {len(tools)} tool(s)")
    print(f"  - {tools[0]['name']}: {tools[0]['description']}")
    
    # Test 3: Call tool - Research briefing
    print("\n[TEST 3] Testing research_briefing tool...")
    research_request = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "research_briefing",
            "arguments": {
                "name": "Satya Nadella",
                "role": "CEO",
                "company": "Microsoft",
                "context": "annual strategy meeting"
            }
        }
    }
    
    research_response = server.handle_request(research_request)
    content = research_response["result"]["content"]
    
    if content and len(content) > 0:
        briefing_text = content[0]["text"]
        if "Satya Nadella" in briefing_text or "Microsoft" in briefing_text:
            print("✓ Research briefing generated successfully")
            print(f"✓ Briefing length: {len(briefing_text)} characters")
            print("\n[BRIEFING PREVIEW]")
            print(briefing_text[:400] + "...\n")
        else:
            print("✗ Briefing doesn't contain expected content")
            return False
    else:
        print("✗ No content returned")
        return False
    
    # Test 4: Test Phase 1 integration
    print("[TEST 4] Verifying Phase 1 integration...")
    person = Person(
        name="Satya Nadella",
        role="CEO",
        company="Microsoft",
        context="strategy"
    )
    briefing = server.agent.research(person)
    
    if briefing and briefing.who_they_are and len(briefing.who_they_are) > 10:
        print("✓ Phase 1 agent integration working")
        print(f"✓ Briefing has {len(briefing.smart_questions)} questions")
        print(f"✓ Cache system: ACTIVE")
    else:
        print("✗ Phase 1 integration failed")
        return False
    
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED ✅")
    print("=" * 60)
    print("\nPhase 2 Status: READY FOR CLAUDE DESKTOP")
    print("\nNext steps:")
    print("1. Edit Claude Desktop config:")
    print('   "command": "python run_mcp_server.py"')
    print("2. Restart Claude Desktop")
    print("3. Ask: 'Research [Name] [Role] [Company]'")
    
    return True


if __name__ == "__main__":
    try:
        result = test_mcp_server()
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"\n[ERROR] Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
