"""Uber adapter using MCP server"""
from typing import Optional
from utils.models import NormalizedOption, Location
from utils.mcp_client import MCPClient


async def get_uber_options(
    origin: Location,
    destination: Location
) -> Optional[NormalizedOption]:
    """Get Uber deeplink and estimate via MCP server"""
    client = MCPClient()
    
    try:
        result = client.call_tool(
            "get_uber_deeplink",
            origin={"lat": origin.lat, "lng": origin.lng},
            destination={"lat": destination.lat, "lng": destination.lng}
        )
        
        if result and result.get("id"):
            return NormalizedOption(
                id=result["id"],
                mode=result.get("mode", "ridehail"),
                provider=result.get("provider", "uber"),
                product=result.get("product"),
                eta_pickup_min=result.get("eta_pickup_min"),
                duration_min=result.get("duration_min", 0),
                cost_usd=result.get("cost_usd", 0.0),
                deeplink=result.get("deeplink")
            )
    except Exception as e:
        print(f"Uber adapter error: {e}")
    finally:
        client.close()
    
    return None

