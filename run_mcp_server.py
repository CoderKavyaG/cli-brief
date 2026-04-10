#!/usr/bin/env python3
"""
Phase 2: Intel Agent MCP Server - Entry Point
Run this to start the MCP server for Claude Desktop integration
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_server.server import IntelAgentMCPServer


def main():
    """Start MCP server"""
    server = IntelAgentMCPServer()
    server.run()


if __name__ == "__main__":
    main()
