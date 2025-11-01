"""Transit adapter using MCP server"""
from typing import List, Optional
from utils.models import NormalizedOption, Location
from utils.mcp_client import MCPClient


async def get_transit_options(
    origin: Location,
    destination: Location,
    when: Optional[str] = None
) -> List[NormalizedOption]:
    """Get transit routes via MCP server"""
    client = MCPClient()
    options = []
    
    try:
        result = client.call_tool(
            "get_transit_routes",
            origin={"lat": origin.lat, "lng": origin.lng},
            destination={"lat": destination.lat, "lng": destination.lng},
            when=when
        )
        
        # Result might be a list or single dict
        routes = result if isinstance(result, list) else [result] if result else []
        
        for route in routes:
            if route and route.get("id"):
                options.append(NormalizedOption(
                    id=route["id"],
                    mode=route.get("mode", "transit"),
                    provider=route.get("provider", "muni"),
                    line=route.get("line"),
                    wait_min=route.get("wait_min"),
                    duration_min=route.get("duration_min", 0),
                    walk_min=route.get("walk_min", 0),
                    cost_usd=route.get("cost_usd", 0.0),
                    co2_g=route.get("co2_g", 0)
                ))
    except Exception as e:
        print(f"Transit adapter error: {e}")
    finally:
        client.close()
    
    return options

