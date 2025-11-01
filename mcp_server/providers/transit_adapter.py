"""Transit adapter using Google Directions API, OpenRouteService, or mock data"""
from typing import Optional, Dict, Any, List
import httpx
from datetime import datetime

from settings import settings


def _generate_mock_transit_route(origin_lat: float, origin_lng: float,
                                  dest_lat: float, dest_lng: float) -> List[Dict[str, Any]]:
    """Generate mock transit route based on distance"""
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
    transit_duration_min = int((distance_m / 1000) / 30 * 60)  # ~30 km/h average
    walk_from_stop_min = 3
    
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


async def _get_google_transit_routes(origin_lat: float, origin_lng: float,
                                     dest_lat: float, dest_lng: float,
                                     when: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
    """Get transit routes using Google Maps Directions API"""
    api_key = settings.google_maps_api_key
    if not api_key:
        return None
    
    try:
        url = "https://maps.googleapis.com/maps/api/directions/json"
        params = {
            "origin": f"{origin_lat},{origin_lng}",
            "destination": f"{dest_lat},{dest_lng}",
            "mode": "transit",
            "key": api_key
        }
        
        if when:
            # Google expects departure_time or arrival_time in seconds since epoch
            try:
                # Handle ISO format with or without timezone
                when_str = when.replace('Z', '+00:00') if when.endswith('Z') else when
                dt = datetime.fromisoformat(when_str)
                # If naive datetime, assume UTC
                if dt.tzinfo is None:
                    from datetime import timezone
                    dt = dt.replace(tzinfo=timezone.utc)
                params["departure_time"] = str(int(dt.timestamp()))
            except (ValueError, AttributeError, OSError):
                pass  # Ignore invalid datetime format
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("status") != "OK":
                    print(f"Google Directions API error: {data.get('status')}")
                    return None
                
                routes = []
                for route in data.get("routes", []):
                    # Parse the route to extract transit information
                    legs = route.get("legs", [])
                    if not legs:
                        continue
                    
                    # Aggregate information from all legs
                    total_duration_sec = 0
                    walk_duration_sec = 0
                    transit_duration_sec = 0
                    wait_duration_sec = 0
                    lines = []
                    
                    for leg in legs:
                        total_duration_sec += leg.get("duration", {}).get("value", 0)
                        
                        for step in leg.get("steps", []):
                            step_mode = step.get("travel_mode", "")
                            step_duration = step.get("duration", {}).get("value", 0)
                            
                            if step_mode == "WALKING":
                                walk_duration_sec += step_duration
                            elif step_mode == "TRANSIT":
                                transit_duration_sec += step_duration
                                transit_details = step.get("transit_details", {})
                                
                                line_info = transit_details.get("line", {})
                                line_name = line_info.get("short_name") or line_info.get("name", "")
                                if line_name:
                                    lines.append(line_name)
                    
                    # Estimate wait time (usually first wait before boarding)
                    if transit_duration_sec > 0:
                        wait_duration_sec = max(2 * 60, (total_duration_sec - walk_duration_sec - transit_duration_sec))  # At least 2 min wait
                    
                    # Convert to minutes
                    walk_min = max(0, int(walk_duration_sec / 60))
                    transit_duration_min = max(1, int(transit_duration_sec / 60))
                    wait_min = max(2, int(wait_duration_sec / 60))
                    
                    # Use first line or default
                    line = lines[0] if lines else "Transit"
                    
                    routes.append({
                        "provider": "google_transit",
                        "mode": "transit",
                        "line": line,
                        "wait_min": wait_min,
                        "duration_min": transit_duration_min,
                        "walk_min": walk_min,
                        "cost_usd": 2.50,  # Default transit fare
                        "co2_g": 200
                    })
                
                return routes if routes else None
            else:
                print(f"Google Directions API failed: {response.status_code}")
                return None
                
    except Exception as e:
        print(f"Google Directions API error: {e}")
        return None


async def _get_ors_transit_routes(origin_lat: float, origin_lng: float,
                                  dest_lat: float, dest_lng: float,
                                  when: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
    """Get transit routes using OpenRouteService (limited transit support)"""
    api_key = settings.ors_api_key
    if not api_key:
        return None
    
    try:
        # Note: ORS doesn't have native transit routing, but we can use isochrones
        # or driving directions as a fallback proxy
        url = "https://api.openrouteservice.org/v2/directions/driving-car"
        params = {
            "api_key": api_key
        }
        
        body = {
            "coordinates": [[origin_lng, origin_lat], [dest_lng, dest_lat]]
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                url,
                params=params,
                json=body,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # ORS doesn't provide transit, so we'll approximate using driving time
                # and apply transit factors
                routes_data = data.get("routes", [])
                if not routes_data:
                    return None
                
                route = routes_data[0]
                summary = route.get("summary", {})
                duration_sec = summary.get("duration", 0)
                
                # Apply transit factors: slower than driving, includes wait/walk
                transit_duration_sec = duration_sec * 1.5  # Transit is slower
                walk_min = 5  # Estimate walk to/from stops
                wait_min = 5  # Estimated wait time
                transit_duration_min = int(transit_duration_sec / 60)
                
                return [{
                    "provider": "ors",
                    "mode": "transit",
                    "line": "Transit",
                    "wait_min": wait_min,
                    "duration_min": transit_duration_min,
                    "walk_min": walk_min,
                    "cost_usd": 2.50,
                    "co2_g": 200
                }]
            else:
                print(f"OpenRouteService API failed: {response.status_code}")
                return None
                
    except Exception as e:
        print(f"OpenRouteService API error: {e}")
        return None


async def get_transit_routes(origin_lat: float, origin_lng: float,
                             dest_lat: float, dest_lng: float,
                             when: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get transit routes using Google Directions API, OpenRouteService, or mock data.
    
    Priority:
    1. Google Maps Directions API (if API key available)
    2. OpenRouteService (if API key available, limited transit support)
    3. Mock data (fallback)
    """
    # Try Google Maps first (best transit support)
    if settings.google_maps_api_key:
        routes = await _get_google_transit_routes(origin_lat, origin_lng, dest_lat, dest_lng, when)
        if routes:
            return routes
    
    # Try OpenRouteService as fallback (limited transit support)
    if settings.ors_api_key:
        routes = await _get_ors_transit_routes(origin_lat, origin_lng, dest_lat, dest_lng, when)
        if routes:
            return routes
    
    # Fallback to mock data
    print("Using mock transit data (no API keys or API calls failed)")
    return _generate_mock_transit_route(origin_lat, origin_lng, dest_lat, dest_lng)

