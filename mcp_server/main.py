"""FastMCP server for route planning provider data"""
from fastmcp import FastMCP
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

from providers import (
    lyft_adapter,
    uber_adapter,
    lime_adapter,
    transit_adapter,
    baseline_adapter,
    safety_adapter
)

mcp = FastMCP("Route Planning Provider Server")


class LocationInput(BaseModel):
    lat: float
    lng: float


@mcp.tool()
def get_lyft_quote(
    origin: Dict[str, Any],
    destination: Dict[str, Any]
) -> Dict[str, Any]:
    """Get Lyft quote including ETA, cost, and pickup time for origin/destination"""
    import asyncio
    
    # Handle both dict and LocationInput
    origin_lat = origin.get("lat") if isinstance(origin, dict) else origin.lat
    origin_lng = origin.get("lng") if isinstance(origin, dict) else origin.lng
    dest_lat = destination.get("lat") if isinstance(destination, dict) else destination.lat
    dest_lng = destination.get("lng") if isinstance(destination, dict) else destination.lng
    
    result = asyncio.run(lyft_adapter.get_lyft_quote(
        origin_lat, origin_lng,
        dest_lat, dest_lng
    ))
    
    if result:
        return {
            "id": f"lyft-std-{hash((origin_lat, origin_lng, dest_lat, dest_lng)) % 10000}",
            "mode": "ridehail",
            **result
        }
    return {}


@mcp.tool()
def get_uber_deeplink(
    origin: LocationInput,
    destination: LocationInput
) -> Dict[str, Any]:
    """Get Uber deeplink URL and estimated ETA/cost"""
    import asyncio
    
    result = asyncio.run(uber_adapter.get_uber_deeplink(
        origin.lat, origin.lng,
        destination.lat, destination.lng
    ))
    
    if result:
        return {
            "id": f"uber-x-{hash((origin.lat, origin.lng, destination.lat, destination.lng)) % 10000}",
            "mode": "ridehail",
            **result
        }
    return {}


@mcp.tool()
def get_lime_nearby(
    origin: Dict[str, Any],
    radius_m: int = 400
) -> List[Dict[str, Any]]:
    """Get nearby Lime vehicles within specified radius in meters"""
    import asyncio
    
    origin_lat = origin.get("lat") if isinstance(origin, dict) else origin.lat
    origin_lng = origin.get("lng") if isinstance(origin, dict) else origin.lng
    
    vehicles = asyncio.run(lime_adapter.get_lime_nearby(
        origin_lat, origin_lng, radius_m
    ))
    
    return vehicles or []


@mcp.tool()
def get_lime_route(
    origin: Dict[str, Any],
    destination: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Get Lime scooter route with pricing and ETAs"""
    import asyncio
    
    origin_lat = origin.get("lat") if isinstance(origin, dict) else origin.lat
    origin_lng = origin.get("lng") if isinstance(origin, dict) else origin.lng
    dest_lat = destination.get("lat") if isinstance(destination, dict) else destination.lat
    dest_lng = destination.get("lng") if isinstance(destination, dict) else destination.lng
    
    # Get nearby vehicles first
    vehicles = asyncio.run(lime_adapter.get_lime_nearby(origin_lat, origin_lng))
    
    if not vehicles:
        return None
    
    result = asyncio.run(lime_adapter.get_lime_route(
        origin_lat, origin_lng,
        dest_lat, dest_lng,
        vehicles
    ))
    
    if result:
        return {
            "id": f"lime-{hash((origin_lat, origin_lng, dest_lat, dest_lng)) % 10000}",
            "mode": "micromobility",
            **result
        }
    return None


@mcp.tool()
def get_transit_routes(
    origin: Dict[str, Any],
    destination: Dict[str, Any],
    when: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Get transit routes (511/Google/ORS) with itinerary"""
    import asyncio
    
    origin_lat = origin.get("lat") if isinstance(origin, dict) else origin.lat
    origin_lng = origin.get("lng") if isinstance(origin, dict) else origin.lng
    dest_lat = destination.get("lat") if isinstance(destination, dict) else destination.lat
    dest_lng = destination.get("lng") if isinstance(destination, dict) else destination.lng
    
    routes = asyncio.run(transit_adapter.get_transit_routes(
        origin_lat, origin_lng,
        dest_lat, dest_lng,
        when
    ))
    
    # Add IDs to routes
    result = []
    for i, route in enumerate(routes):
        route_id = f"{route.get('provider', 'transit')}-{route.get('line', 'default')}-{i}"
        result.append({
            "id": route_id,
            **route
        })
    
    return result


@mcp.tool()
def get_baseline_eta(
    mode: str,
    origin: Dict[str, Any],
    destination: Dict[str, Any]
) -> Dict[str, Any]:
    """Get baseline travel times for walk, bike, or drive"""
    import asyncio
    
    origin_lat = origin.get("lat") if isinstance(origin, dict) else origin.lat
    origin_lng = origin.get("lng") if isinstance(origin, dict) else origin.lng
    dest_lat = destination.get("lat") if isinstance(destination, dict) else destination.lat
    dest_lng = destination.get("lng") if isinstance(destination, dict) else destination.lng
    
    if mode == "walk":
        result = asyncio.run(baseline_adapter.get_walk_route(
            origin_lat, origin_lng,
            dest_lat, dest_lng
        ))
        return {
            "id": f"walk-{hash((origin_lat, origin_lng, dest_lat, dest_lng)) % 10000}",
            "mode": "walk",
            "provider": "baseline",
            "duration_min": result["duration_min"],
            "walk_min": result["duration_min"],
            "cost_usd": 0.0,
            "co2_g": 0
        }
    elif mode == "bike":
        result = asyncio.run(baseline_adapter.get_bike_route(
            origin_lat, origin_lng,
            dest_lat, dest_lng
        ))
        return {
            "id": f"bike-{hash((origin_lat, origin_lng, dest_lat, dest_lng)) % 10000}",
            "mode": "bike",
            "provider": "baseline",
            "duration_min": result["duration_min"],
            "cost_usd": 0.0,
            "co2_g": 50
        }
    elif mode == "drive":
        result = asyncio.run(baseline_adapter.get_drive_route(
            origin_lat, origin_lng,
            dest_lat, dest_lng
        ))
        # Assume car ownership cost ~$0.50/mile for demo
        distance_miles = result["distance_m"] / 1609.34
        cost = distance_miles * 0.50
        
        return {
            "id": f"drive-{hash((origin_lat, origin_lng, dest_lat, dest_lng)) % 10000}",
            "mode": "drive",
            "provider": "baseline",
            "duration_min": result["duration_min"],
            "cost_usd": round(cost, 2),
            "co2_g": int(result["distance_m"] / 1000 * 200)  # ~200g CO2 per km
        }
    
    return {}


@mcp.tool()
def get_safety_data(
    walk_segments: List[Dict[str, Any]],
    time_of_day: Optional[str] = None
) -> Dict[str, Any]:
    """Get safety heatmap/risk scores for route segments"""
    segments = [
        (seg.get("lat") if isinstance(seg, dict) else seg.lat,
         seg.get("lng") if isinstance(seg, dict) else seg.lng)
        for seg in walk_segments
    ]
    
    risk_penalty = safety_adapter.get_safety_risk_score(segments, time_of_day)
    night_walk_min = safety_adapter.get_night_walk_minutes(segments, time_of_day)
    
    return {
        "risk_penalty": risk_penalty,
        "night_walk_minutes": night_walk_min
    }


if __name__ == "__main__":
    mcp.run()

