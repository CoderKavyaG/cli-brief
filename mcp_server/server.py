"""
Phase 2: Intel Agent MCP Server
Exposes Phase 1 agent as Model Context Protocol tools for Claude Desktop

Simplified MCP implementation using JSON-RPC over stdio.
"""

import json
import sys
from typing import Optional, Any, Dict
from phase1_agent.main import IntelAgent
from phase1_agent.models import Person


class IntelAgentMCPServer:
    """Simplified MCP Server for intel agent"""
    
    def __init__(self):
        self.agent = IntelAgent()
        self.request_id = None
    
    def handle_initialize(self, params: Dict) -> Dict:
        """Handle MCP initialize request"""
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "intel-agent",
                "version": "1.0.0"
            }
        }
    
    def handle_list_tools(self) -> Dict:
        """Handle list_tools request"""
        return {
            "tools": [
                {
                    "name": "research_briefing",
                    "description": "Research and generate intel briefing for a person before a meeting. Provides background, interests, company context, and meeting strategy.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Person's full name"
                            },
                            "role": {
                                "type": "string",
                                "description": "Their role/title (CEO, Engineer, Founder, etc.)"
                            },
                            "company": {
                                "type": "string",
                                "description": "Company or organization (optional)"
                            },
                            "context": {
                                "type": "string",
                                "description": "Meeting context: Why are you meeting them? (optional)"
                            }
                        },
                        "required": ["name", "role"]
                    }
                }
            ]
        }
    
    def handle_call_tool(self, params: Dict) -> Dict:
        """Handle call_tool request"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name == "research_briefing":
            return self._research_briefing(arguments)
        else:
            return {
                "content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}],
                "isError": True
            }
    
    def _research_briefing(self, args: Dict) -> Dict:
        """Execute research_briefing tool"""
        try:
            name = args.get("name")
            role = args.get("role")
            company = args.get("company")
            context = args.get("context")
            
            if not name or not role:
                return {
                    "content": [{"type": "text", "text": "ERROR: name and role are required"}],
                    "isError": True
                }
            
            # Create person and research
            person = Person(
                name=name,
                role=role,
                company=company,
                context=context
            )
            
            briefing = self.agent.research(person)
            
            if briefing:
                return {
                    "content": [{"type": "text", "text": briefing.to_markdown()}],
                    "isError": False
                }
            else:
                return {
                    "content": [{"type": "text", "text": f"Failed to generate briefing for {name}"}],
                    "isError": True
                }
        
        except Exception as e:
            return {
                "content": [{"type": "text", "text": f"ERROR: {str(e)}"}],
                "isError": True
            }
    
    def handle_request(self, message: Dict) -> Optional[Dict]:
        """Handle incoming MCP request"""
        self.request_id = message.get("id")
        method = message.get("method")
        params = message.get("params", {})
        
        if method == "initialize":
            result = self.handle_initialize(params)
        elif method == "tools/list":
            result = self.handle_list_tools()
        elif method == "tools/call":
            result = self.handle_call_tool(params)
        else:
            result = {"error": f"Unknown method: {method}"}
        
        return {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "result": result if "error" not in result else None,
            "error": result if "error" in result else None
        }
    
    def run(self):
        """Start MCP server - read from stdin, write to stdout"""
        print("[MCP] Intel Agent Server started", file=sys.stderr)
        
        try:
            while True:
                line = sys.stdin.readline()
                if not line:
                    break
                
                try:
                    message = json.loads(line.strip())
                    response = self.handle_request(message)
                    
                    if response:
                        print(json.dumps(response))
                        sys.stdout.flush()
                
                except json.JSONDecodeError:
                    pass
                except Exception as e:
                    print(f"[ERROR] {str(e)}", file=sys.stderr)
        
        except KeyboardInterrupt:
            print("[MCP] Server stopped", file=sys.stderr)


if __name__ == "__main__":
    server = IntelAgentMCPServer()
    server.run()
