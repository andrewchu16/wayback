"""Lime adapter using MCP server"""
from typing import Optional, List
from utils.models import NormalizedOption, Location
from utils.mcp_client import MCPClient


async def get_lime_options(
    origin: Location,
    destination: Location
) -> Optional[NormalizedOption]:
    """Get Lime route via MCP server"""
    client = MCPClient()
    
    try:
        result = client.call_tool(
            "get_lime_route",
            origin={"lat": origin.lat, "lng": origin.lng},
            destination={"lat": destination.lat, "lng": destination.lng}
        )
        
        if result and result.get("id"):
            return NormalizedOption(
                id=result["id"],
                mode=result.get("mode", "micromobility"),
                provider=result.get("provider", "lime"),
                product=result.get("product"),
                wait_min=result.get("wait_min"),
                duration_min=result.get("duration_min", 0),
                walk_min=result.get("walk_min", 0),
                cost_usd=result.get("cost_usd", 0.0),
                deeplink=result.get("deeplink")
            )
    except Exception as e:
        print(f"Lime adapter error: {e}")
    finally:
        client.close()
    
    return None

