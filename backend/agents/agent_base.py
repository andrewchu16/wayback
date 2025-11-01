"""Base agent class with MCP client initialization"""
from typing import List, Optional
from utils.models import NormalizedOption, AgentRecommendation
from utils.mcp_client import MCPClient


class BaseAgent:
    """Base class for route planning agents"""
    
    def __init__(self, mcp_client: Optional[MCPClient] = None):
        """
        Initialize agent with MCP client.
        
        Args:
            mcp_client: MCP client instance. If None, creates a new one.
        """
        self.mcp_client = mcp_client or MCPClient()
    
    def score(self, options: List[NormalizedOption]) -> AgentRecommendation:
        """
        Score options and return top recommendation.
        
        Args:
            options: List of normalized route options
        
        Returns:
            Agent recommendation with top option ID, score, and rationale
        
        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError
    
    def _normalize_score(self, value: float, min_val: float, max_val: float) -> float:
        """Normalize score to 0.0-1.0 range"""
        if max_val == min_val:
            return 1.0
        normalized = (value - min_val) / (max_val - min_val)
        return max(0.0, min(1.0, normalized))
    
    def close(self):
        """Close MCP client"""
        if self.mcp_client:
            self.mcp_client.close()

