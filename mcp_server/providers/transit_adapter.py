"""Transit adapter using 511 API, Google Directions, or OpenRouteService"""
from typing import Optional, Dict, Any, List
import httpx

from settings import settings


async def get_transit_routes(origin_lat: float, origin_lng: float,
                             dest_lat: float, dest_lng: float,
                             when: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get transit routes using 511, Google Directions, or ORS"""
    # For MVP: Return mock transit option
    # In production: Use 511 API (GTFS) or Google Directions API
    
    api_key = settings.google_maps_api_key or settings.ors_api_key
    
    # Mock transit route for demo
    from math import radians, sin, cos, sqrt, atan2
    
    R = 6371000
    lat1_rad = radians(origin_lat)
    lat2_rad = radians(dest_lat)
    delta_lat = radians(dest_lat - origin_lat)
    delta_lon = radians(dest_lng - origin_lng)
    
    a = sin(delta_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance_m = R * c
    
    # Transit: walk to stop, wait, ride, walk from stop
    walk_to_stop_min = 5
    wait_min = 5
    transit_duration_min = int((distance_m / 1000) / 30 * 60)  # ~30 km/h
    walk_from_stop_min = 3
    
    total_min = walk_to_stop_min + wait_min + transit_duration_min + walk_from_stop_min
    
    return [{
        "provider": "muni",
        "mode": "transit",
        "line": "38",
        "wait_min": wait_min,
        "duration_min": transit_duration_min,
        "walk_min": walk_to_stop_min + walk_from_stop_min,
        "cost_usd": 2.50,
        "co2_g": 200
    }]

