"""Baseline adapter for walk/bike/drive routing using Mapbox or OpenRouteService"""
from typing import Optional, Dict, Any
import httpx
import os


async def get_walk_route(origin_lat: float, origin_lng: float, 
                         dest_lat: float, dest_lng: float) -> Dict[str, Any]:
    """Get walking route using ORS or simple calculation"""
    # For MVP: simple heuristic (5 km/h walking speed)
    from math import radians, sin, cos, sqrt, atan2
    
    R = 6371000  # Earth radius in meters
    lat1_rad = radians(origin_lat)
    lat2_rad = radians(dest_lat)
    delta_lat = radians(dest_lat - origin_lat)
    delta_lon = radians(dest_lng - origin_lng)
    
    a = sin(delta_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance_m = R * c
    
    # Walking speed: ~5 km/h = 1.39 m/s
    duration_seconds = int(distance_m / 1.39)
    
    return {
        "mode": "walk",
        "distance_m": distance_m,
        "duration_seconds": duration_seconds,
        "duration_min": duration_seconds // 60
    }


async def get_bike_route(origin_lat: float, origin_lng: float,
                        dest_lat: float, dest_lng: float) -> Dict[str, Any]:
    """Get biking route using ORS or simple calculation"""
    from math import radians, sin, cos, sqrt, atan2
    
    R = 6371000
    lat1_rad = radians(origin_lat)
    lat2_rad = radians(dest_lat)
    delta_lat = radians(dest_lat - origin_lat)
    delta_lon = radians(dest_lng - origin_lng)
    
    a = sin(delta_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance_m = R * c
    
    # Biking speed: ~15 km/h = 4.17 m/s
    duration_seconds = int(distance_m / 4.17)
    
    return {
        "mode": "bike",
        "distance_m": distance_m,
        "duration_seconds": duration_seconds,
        "duration_min": duration_seconds // 60
    }


async def get_drive_route(origin_lat: float, origin_lng: float,
                         dest_lat: float, dest_lng: float) -> Dict[str, Any]:
    """Get driving route - can use Mapbox/ORS if API key available"""
    from math import radians, sin, cos, sqrt, atan2
    
    R = 6371000
    lat1_rad = radians(origin_lat)
    lat2_rad = radians(dest_lat)
    delta_lat = radians(dest_lat - origin_lat)
    delta_lon = radians(dest_lng - origin_lng)
    
    a = sin(delta_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance_m = R * c
    
    # Average city driving: ~40 km/h accounting for traffic
    duration_seconds = int(distance_m / 11.11)  # ~40 km/h
    
    return {
        "mode": "drive",
        "distance_m": distance_m,
        "duration_seconds": duration_seconds,
        "duration_min": duration_seconds // 60
    }

