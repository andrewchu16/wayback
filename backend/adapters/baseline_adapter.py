"""Baseline adapter for walk/bike/drive using MCP server"""
from typing import List
from utils.models import NormalizedOption, Location
from utils.mcp_client import MCPClient


async def get_baseline_options(
    origin: Location,
    destination: Location
) -> List[NormalizedOption]:
    """Get baseline walk/bike/drive options via MCP server"""
    client = MCPClient()
    options = []
    
    modes = ["walk", "bike", "drive"]
    
    try:
        for mode in modes:
            result = client.call_tool(
                "get_baseline_eta",
                mode=mode,
                origin={"lat": origin.lat, "lng": origin.lng},
                destination={"lat": destination.lat, "lng": destination.lng}
            )
            
            if result and result.get("id"):
                options.append(NormalizedOption(
                    id=result["id"],
                    mode=result.get("mode", mode),
                    provider=result.get("provider", "baseline"),
                    duration_min=result.get("duration_min", 0),
                    walk_min=result.get("walk_min", 0) if mode == "walk" else None,
                    cost_usd=result.get("cost_usd", 0.0),
                    co2_g=result.get("co2_g", 0)
                ))
    except Exception as e:
        print(f"Baseline adapter error: {e}")
    finally:
        client.close()
    
    return options

