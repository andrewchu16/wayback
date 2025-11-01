"""Geocoding utilities for address autocomplete and geocoding"""
import httpx
from typing import List, Dict, Optional, Any
from utils.models import Location


class GeocodingService:
    """Geocoding service using Nominatim (OpenStreetMap) - free and no API key required"""
    
    NOMINATIM_BASE_URL = "https://nominatim.openstreetmap.org"
    
    @staticmethod
    async def autocomplete(query: str, limit: int = 5, location_bias: Optional[Location] = None) -> List[Dict[str, Any]]:
        """
        Get autocomplete suggestions for a search query.
        
        Args:
            query: Search query string
            limit: Maximum number of results
            location_bias: Optional location to bias results towards
            
        Returns:
            List of autocomplete suggestions with display_name, lat, lng
        """
        if not query or len(query.strip()) < 2:
            return []
        
        params = {
            "q": query.strip(),
            "format": "json",
            "limit": limit,
            "addressdetails": 1,
        }
        
        # Add location bias if provided (prioritize results near user)
        # Use viewbox for stronger geographic bias - creates a ~20km radius around user location
        if location_bias:
            # Approximate 1 degree latitude ≈ 111 km, so 0.18° ≈ ~20 km radius
            radius_degrees = 0.18
            viewbox = (
                location_bias.lng - radius_degrees,  # left (west)
                location_bias.lat + radius_degrees,  # top (north)
                location_bias.lng + radius_degrees,  # right (east)
                location_bias.lat - radius_degrees   # bottom (south)
            )
            params["viewbox"] = f"{viewbox[0]},{viewbox[1]},{viewbox[2]},{viewbox[3]}"
            params["bounded"] = "1"  # Prefer results within the viewbox
            params["lat"] = location_bias.lat
            params["lon"] = location_bias.lng
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{GeocodingService.NOMINATIM_BASE_URL}/search",
                params=params,
                headers={
                    "User-Agent": "WaybackRouteFinder/1.0"  # Required by Nominatim
                }
            )
            
            if response.status_code == 200:
                results = response.json()
                return [
                    {
                        "display_name": result.get("display_name", ""),
                        "lat": float(result.get("lat", 0)),
                        "lng": float(result.get("lon", 0)),
                        "place_id": result.get("place_id"),
                    }
                    for result in results
                ]
        
        return []
    
    @staticmethod
    async def geocode(query: str, location_bias: Optional[Location] = None) -> Optional[Location]:
        """
        Geocode a query string to get coordinates.
        
        Args:
            query: Address or place name to geocode
            location_bias: Optional location to bias results towards
            
        Returns:
            Location with lat/lng, or None if not found
        """
        results = await GeocodingService.autocomplete(query, limit=1, location_bias=location_bias)
        
        if results and len(results) > 0:
            return Location(lat=results[0]["lat"], lng=results[0]["lng"])
        
        return None
    
    @staticmethod
    async def reverse_geocode(location: Location) -> Optional[Dict[str, Any]]:
        """
        Reverse geocode coordinates to get address/place name.
        
        Args:
            location: Location with lat/lng coordinates
            
        Returns:
            Dictionary with display_name, lat, lng, place_id, or None if not found
        """
        try:
            params = {
                "lat": location.lat,
                "lon": location.lng,
                "format": "json",
                "addressdetails": 1,
            }
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{GeocodingService.NOMINATIM_BASE_URL}/reverse",
                    params=params,
                    headers={
                        "User-Agent": "WaybackRouteFinder/1.0"  # Required by Nominatim
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result and "display_name" in result:
                        return {
                            "display_name": result.get("display_name", ""),
                            "lat": float(result.get("lat", location.lat)),
                            "lng": float(result.get("lon", location.lng)),
                            "place_id": result.get("place_id"),
                        }
            
            return None
        except Exception as e:
            print(f"Reverse geocode error: {e}")
            return None

