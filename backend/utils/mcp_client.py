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
        import time
        
        self._ensure_process()
        
        # Check if process is still alive
        if self.process.poll() is not None:
            print(f"MCP process died, restarting...")
            self.process = None
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
            try:
                self.process.stdin.write(request_str)
                self.process.stdin.flush()
            except (BrokenPipeError, OSError) as e:
                print(f"MCP client write error: {e}")
                # Restart process
                self.process = None
                self._ensure_process()
                self.process.stdin.write(request_str)
                self.process.stdin.flush()
            
            # Read response with timeout (5 seconds)
            response_line = ""
            start_time = time.time()
            timeout = 5.0
            
            while time.time() - start_time < timeout:
                # Try to read a line (non-blocking on Windows requires different approach)
                try:
                    # On Windows, we can't use select, so read with timeout handling
                    line = self.process.stdout.readline()
                    if line:
                        response_line += line.strip()
                        # Try to parse as JSON
                        try:
                            response = json.loads(response_line)
                            # Successfully parsed JSON
                            break
                        except json.JSONDecodeError:
                            # Continue reading
                            continue
                    elif self.process.poll() is not None:
                        # Process ended
                        print(f"MCP process ended unexpectedly")
                        break
                except Exception as e:
                    print(f"MCP read error: {e}")
                    break
            else:
                # Timeout
                print(f"MCP tool call timeout for {tool_name}")
                return {}
            
            if not response_line:
                return {}
            
            try:
                response = json.loads(response_line)
            except json.JSONDecodeError as e:
                print(f"MCP JSON decode error: {e}, response_line: {response_line[:200]}")
                return {}
            
            if "error" in response:
                error_msg = response.get("error", {})
                error_detail = error_msg.get("message", str(error_msg)) if isinstance(error_msg, dict) else str(error_msg)
                print(f"MCP tool error: {error_detail}")
                # Don't raise, return empty dict to allow fallback
                return {}
            
            # Extract result - FastMCP returns result.content[0].text as JSON string
            result = response.get("result", {})
            content = result.get("content", [])
            if content and len(content) > 0:
                first_content = content[0]
                if isinstance(first_content, dict):
                    text = first_content.get("text", "{}")
                    try:
                        if isinstance(text, str):
                            return json.loads(text)
                        elif isinstance(text, dict):
                            return text
                    except json.JSONDecodeError:
                        # If text is not valid JSON, return it as is or empty dict
                        return text if isinstance(text, dict) else {}
            
            return {}
        
        except Exception as e:
            print(f"MCP client error: {e}")
            import traceback
            print(traceback.format_exc())
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

