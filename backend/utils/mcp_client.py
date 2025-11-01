"""MCP client wrapper for agents to call MCP server tools via stdio subprocess"""
import subprocess
import json
import sys
from typing import Dict, Any, Optional
from pathlib import Path


class MCPClient:
    """Client for communicating with MCP server via stdio"""
    
    def __init__(self, mcp_server_path: Optional[str] = None):
        """
        Initialize MCP client.
        
        Args:
            mcp_server_path: Path to MCP server main.py. Defaults to ../mcp_server/main.py
        """
        if mcp_server_path is None:
            # Assume mcp_server is sibling to backend
            backend_dir = Path(__file__).parent.parent
            mcp_server_path = str(backend_dir.parent / "mcp_server" / "main.py")
        
        self.mcp_server_path = mcp_server_path
        self.process: Optional[subprocess.Popen] = None
    
    def _ensure_process(self):
        """Start MCP server subprocess if not running"""
        if self.process is None or self.process.poll() is not None:
            self.process = subprocess.Popen(
                [sys.executable, self.mcp_server_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
    
    def call_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """
        Call an MCP tool by name with arguments.
        
        Args:
            tool_name: Name of the tool to call
            **kwargs: Tool arguments
        
        Returns:
            Tool result as dictionary
        """
        self._ensure_process()
        
        # MCP protocol: send JSON-RPC request
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": kwargs
            }
        }
        
        try:
            # Send request
            request_str = json.dumps(request) + "\n"
            self.process.stdin.write(request_str)
            self.process.stdin.flush()
            
            # Read response line by line until we get a complete JSON response
            response_line = ""
            while True:
                line = self.process.stdout.readline()
                if not line:
                    break
                response_line += line.strip()
                try:
                    response = json.loads(response_line)
                    break
                except json.JSONDecodeError:
                    continue
            
            if not response_line:
                return {}
            
            response = json.loads(response_line)
            
            if "error" in response:
                raise Exception(f"MCP tool error: {response['error']}")
            
            # Extract result - FastMCP returns result.content[0].text as JSON string
            result = response.get("result", {})
            content = result.get("content", [])
            if content and isinstance(content[0], dict):
                text = content[0].get("text", "{}")
                try:
                    return json.loads(text) if isinstance(text, str) else text
                except json.JSONDecodeError:
                    return text if isinstance(text, dict) else {}
            
            return {}
        
        except Exception as e:
            print(f"MCP client error: {e}")
            # Fallback: return empty result
            return {}
    
    def close(self):
        """Close MCP server subprocess"""
        if self.process:
            self.process.terminate()
            self.process.wait()
            self.process = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

