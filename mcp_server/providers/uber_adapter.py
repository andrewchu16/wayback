"""Uber adapter for deeplinks and ETA estimates"""
from typing import Optional, Dict, Any
import urllib.parse


async def get_uber_deeplink(origin_lat: float, origin_lng: float,
                           dest_lat: float, dest_lng: float) -> Dict[str, Any]:
    """Generate Uber deeplink URL"""
    # Uber deeplink format: uber://?action=setPickup&pickup[latitude]=...&pickup[longitude]=...
    # &dropoff[latitude]=...&dropoff[longitude]=...
    
    deeplink = (
        f"uber://?action=setPickup"
        f"&pickup[latitude]={origin_lat}"
        f"&pickup[longitude]={origin_lng}"
        f"&dropoff[latitude]={dest_lat}"
        f"&dropoff[longitude]={dest_lng}"
    )
    
    # Estimate ETA and cost (mock for MVP)
    from math import radians, sin, cos, sqrt, atan2
    
    R = 6371000
    lat1_rad = radians(origin_lat)
    lat2_rad = radians(dest_lat)
    delta_lat = radians(dest_lat - origin_lat)
    delta_lon = radians(dest_lng - origin_lng)
    
    a = sin(delta_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance_m = R * c
    
    cost = 8.0 + (distance_m / 1000) * 1.5
    duration_min = int((distance_m / 1000) / 45 * 60)
    
    return {
        "provider": "uber",
        "product": "UberX",
        "eta_pickup_min": 5,  # Estimated pickup time
        "duration_min": duration_min,
        "cost_usd": round(cost, 2),
        "deeplink": deeplink
    }

