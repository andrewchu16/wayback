"""Lime adapter using GBFS API or heuristic pricing"""
from typing import Optional, Dict, Any, List
import httpx
from math import radians, sin, cos, sqrt, atan2

from settings import settings


async def get_lime_nearby(origin_lat: float, origin_lng: float,
                          radius_m: int = 400) -> List[Dict[str, Any]]:
    """Get nearby Lime vehicles using GBFS or return empty"""
    # For MVP: Return mock nearby vehicle
    # In production: Use GBFS API
    
    gbfs_url = settings.lime_gbfs_url
    
    # Mock: return one nearby vehicle
    return [{
        "vehicle_id": "lime-123",
        "lat": origin_lat + 0.001,  # ~100m away
        "lng": origin_lng + 0.001,
        "vehicle_type": "scooter"
    }]


async def get_lime_route(origin_lat: float, origin_lng: float,
                        dest_lat: float, dest_lng: float,
                        nearby_vehicles: Optional[List[Dict[str, Any]]] = None) -> Optional[Dict[str, Any]]:
    """Calculate Lime scooter route with pricing"""
    if nearby_vehicles is None:
        nearby_vehicles = await get_lime_nearby(origin_lat, origin_lng)
    
    if not nearby_vehicles:
        return None
    
    # Calculate distance
    R = 6371000
    lat1_rad = radians(origin_lat)
    lat2_rad = radians(dest_lat)
    delta_lat = radians(dest_lat - origin_lat)
    delta_lon = radians(dest_lng - origin_lng)
    
    a = sin(delta_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance_m = R * c
    
    # Lime pricing: $1 unlock + $0.55/min
    # Scooter speed: ~20 km/h = 5.56 m/s
    duration_seconds = int(distance_m / 5.56)
    duration_min = duration_seconds // 60
    
    # Walk to scooter: estimate based on nearest vehicle
    walk_to_scooter_min = 2  # Simplified
    walk_from_scooter_min = 1  # Simplified
    
    total_min = walk_to_scooter_min + duration_min + walk_from_scooter_min
    
    # Lime pricing: $1 unlock + $0.55/min
    cost = 1.0 + (duration_min * 0.55)
    
    return {
        "provider": "lime",
        "product": "Lime Scooter",
        "wait_min": walk_to_scooter_min,
        "duration_min": duration_min,
        "walk_min": walk_from_scooter_min,
        "cost_usd": round(cost, 2),
        "deeplink": f"limebike://?lat={dest_lat}&lng={dest_lng}"
    }

