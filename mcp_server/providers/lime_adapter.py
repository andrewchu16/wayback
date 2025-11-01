"""Lime adapter using GBFS API"""
from typing import Optional, Dict, Any, List
import httpx
from math import radians, sin, cos, sqrt, atan2

from settings import settings


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in meters using Haversine formula"""
    R = 6371000  # Earth radius in meters
    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)
    delta_lat = radians(lat2 - lat1)
    delta_lon = radians(lon2 - lon1)
    
    a = sin(delta_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c


async def _fetch_gbfs_feeds() -> Dict[str, str]:
    """Fetch GBFS feed list and return dict of feed_name -> feed_url"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(settings.lime_gbfs_url)
            response.raise_for_status()
            data = response.json()
            
            # Extract feeds from the response
            feeds = {}
            if "data" in data and "en" in data["data"]:
                for feed in data["data"]["en"].get("feeds", []):
                    feeds[feed["name"]] = feed["url"]
            
            return feeds
        except Exception as e:
            print(f"Error fetching GBFS feeds: {e}")
            return {}


async def _fetch_free_bike_status() -> List[Dict[str, Any]]:
    """Fetch free bike status from GBFS API"""
    feeds = await _fetch_gbfs_feeds()
    
    if "free_bike_status" not in feeds:
        print("free_bike_status feed not found in GBFS")
        return []
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(feeds["free_bike_status"])
            response.raise_for_status()
            data = response.json()
            
            # Extract bikes from response
            bikes = []
            if "data" in data and "bikes" in data["data"]:
                for bike in data["data"]["bikes"]:
                    # Filter out reserved and disabled bikes
                    if bike.get("is_reserved", 0) == 0 and bike.get("is_disabled", 0) == 0:
                        bikes.append({
                            "vehicle_id": bike.get("bike_id"),
                            "lat": bike.get("lat"),
                            "lng": bike.get("lon"),  # GBFS uses "lon" not "lng"
                            "vehicle_type": bike.get("vehicle_type", "scooter")
                        })
            
            return bikes
        except Exception as e:
            print(f"Error fetching free bike status: {e}")
            return []


async def get_lime_nearby(origin_lat: float, origin_lng: float,
                          radius_m: int = 400) -> List[Dict[str, Any]]:
    """Get nearby Lime vehicles within specified radius in meters"""
    bikes = await _fetch_free_bike_status()
    
    if not bikes:
        return []
    
    # Calculate distance for each bike and filter by radius
    nearby = []
    for bike in bikes:
        distance = haversine_distance(
            origin_lat, origin_lng,
            bike["lat"], bike["lng"]
        )
        
        if distance <= radius_m:
            bike["distance_m"] = round(distance, 1)
            nearby.append(bike)
    
    # Sort by distance (nearest first)
    nearby.sort(key=lambda x: x["distance_m"])
    
    return nearby


async def get_lime_route(origin_lat: float, origin_lng: float,
                        dest_lat: float, dest_lng: float,
                        nearby_vehicles: Optional[List[Dict[str, Any]]] = None) -> Optional[Dict[str, Any]]:
    """Calculate Lime scooter route with pricing"""
    if nearby_vehicles is None:
        nearby_vehicles = await get_lime_nearby(origin_lat, origin_lng)
    
    if not nearby_vehicles:
        return None
    
    # Use the nearest vehicle
    nearest_vehicle = nearby_vehicles[0]
    scooter_lat = nearest_vehicle["lat"]
    scooter_lng = nearest_vehicle["lng"]
    
    # Calculate walk distance to scooter
    walk_to_scooter_m = haversine_distance(origin_lat, origin_lng, scooter_lat, scooter_lng)
    
    # Calculate distance from scooter to destination (this is the ride distance)
    scooter_to_dest_m = haversine_distance(scooter_lat, scooter_lng, dest_lat, dest_lng)
    
    # Walking speed: ~5 km/h = 1.39 m/s = 83.4 m/min
    walk_to_scooter_min = max(1, round(walk_to_scooter_m / 83.4, 1))
    # Walk from drop-off location (usually minimal, ~1 min)
    walk_from_scooter_min = 1
    
    # Scooter speed: ~20 km/h = 5.56 m/s = 333.6 m/min
    # Ride distance is from scooter location to destination
    ride_duration_min = max(1, round(scooter_to_dest_m / 333.6, 1))
    
    # Lime pricing: $1 unlock + $0.55/min
    cost = 1.0 + (ride_duration_min * 0.55)
    
    return {
        "provider": "lime",
        "product": "Lime Scooter",
        "wait_min": walk_to_scooter_min,
        "duration_min": ride_duration_min,
        "walk_min": walk_from_scooter_min,
        "cost_usd": round(cost, 2),
        "deeplink": f"limebike://?lat={dest_lat}&lng={dest_lng}",
        "vehicle_id": nearest_vehicle["vehicle_id"]
    }

