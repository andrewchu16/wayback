"""Geocoding utilities for address autocomplete and geocoding"""
import httpx
import math
from typing import List, Dict, Optional, Any
from utils.models import Location


class GeocodingService:
    """Geocoding service using Nominatim (OpenStreetMap) - free and no API key required"""
    
    NOMINATIM_BASE_URL = "https://nominatim.openstreetmap.org"
    RADIUS_KM = 20  # 20km radius for filtering results
    
    @staticmethod
    def _calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two coordinates using Haversine formula.
        
        Returns:
            Distance in kilometers
        """
        # Earth's radius in kilometers
        R = 6371.0
        
        # Convert to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Differences
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        # Haversine formula
        a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        distance = R * c
        return distance
    
    @staticmethod
    def _extract_city_from_address(address: Dict[str, Any]) -> Optional[str]:
        """
        Extract city name from Nominatim address dictionary.
        
        Args:
            address: Address dictionary from Nominatim response
            
        Returns:
            City name or None if not found
        """
        # Nominatim uses different fields for city depending on the location type
        # Try in order of specificity: city -> town -> village -> municipality -> county
        city = (
            address.get("city") or
            address.get("town") or
            address.get("village") or
            address.get("municipality") or
            address.get("county")
        )
        
        if city:
            return city.lower().strip()
        return None
    
    @staticmethod
    async def _get_city_from_location(location: Location) -> tuple[Optional[str], Optional[str]]:
        """
        Get city name for a given location using reverse geocoding.
        
        Args:
            location: Location with lat/lng coordinates
            
        Returns:
            Tuple of (normalized_city_name_lowercase, original_city_name) or (None, None) if not found
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
                        "User-Agent": "WaybackRouteFinder/1.0"
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result and "address" in result:
                        addr = result["address"]
                        original_city = (
                            addr.get("city") or
                            addr.get("town") or
                            addr.get("village") or
                            addr.get("municipality") or
                            addr.get("county")
                        )
                        if original_city:
                            normalized_city = original_city.lower().strip()
                            print(f"[GeocodingService] City from location ({location.lat}, {location.lng}): {normalized_city} (original: {original_city})")
                            return (normalized_city, original_city)
        except Exception as e:
            print(f"[GeocodingService] Error getting city from location: {e}")
        
        return (None, None)
    
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
            print(f"[GeocodingService] Query too short: '{query}'")
            return []
        
        # Get city from location_bias first to use in structured query
        target_city = None
        city_name_for_query = None  # Original case city name for API
        if location_bias:
            target_city, city_name_for_query = await GeocodingService._get_city_from_location(location_bias)
        
        # Use structured query if we have a city, otherwise use free-form query
        # Per Nominatim docs (https://nominatim.org/release-docs/latest/api/Search/#structured-query):
        # structured and free-form queries cannot be combined
        params = {
            "format": "json",
            "limit": limit * 2,  # Request more results to account for post-filtering
            "addressdetails": 1,
        }
        
        # Use structured query when we have city information
        # Per Nominatim docs, structured queries are better for known address components
        # For autocomplete, we'll use free-form query but add city constraint to the query string
        if city_name_for_query:
            # Add city to the query to constrain results to the same city
            # Nominatim processes free-form queries left-to-right and right-to-left
            # Adding city ensures results are prioritized within that city
            params["q"] = f"{query.strip()}, {city_name_for_query}"
            print(f"[GeocodingService] Using free-form query with city constraint: q='{query.strip()}, {city_name_for_query}'")
        else:
            # No city available, use standard free-form query
            params["q"] = query.strip()
            print(f"[GeocodingService] Using free-form query: q='{query.strip()}'")
        
        # Add location bias if provided (prioritize results near user)
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
            params["lat"] = location_bias.lat
            params["lon"] = location_bias.lng
        
        print(f"[GeocodingService] Autocomplete request: query='{query}', limit={limit}, location_bias={location_bias}")
        print(f"[GeocodingService] Nominatim URL: {GeocodingService.NOMINATIM_BASE_URL}/search")
        print(f"[GeocodingService] Params: {params}")
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:  # Increased timeout to 10s
                response = await client.get(
                    f"{GeocodingService.NOMINATIM_BASE_URL}/search",
                    params=params,
                    headers={
                        "User-Agent": "WaybackRouteFinder/1.0"  # Required by Nominatim
                    }
                )
                
                print(f"[GeocodingService] Response status: {response.status_code}")
                
                if response.status_code == 200:
                    results = response.json()
                    print(f"[GeocodingService] Nominatim returned {len(results)} results")
                    
                    if len(results) == 0:
                        print(f"[GeocodingService] No results from Nominatim for query: '{query}'")
                    
                    # Convert results to suggestions with address details
                    all_suggestions = []
                    for result in results:
                        suggestion = {
                            "display_name": result.get("display_name", ""),
                            "lat": float(result.get("lat", 0)),
                            "lng": float(result.get("lon", 0)),
                            "place_id": result.get("place_id"),
                            "address": result.get("address", {}),  # Keep address for city filtering
                        }
                        all_suggestions.append(suggestion)
                    
                    # Filter by city if location_bias is provided
                    if location_bias:
                        # Get city from location_bias
                        target_city = await GeocodingService._get_city_from_location(location_bias)
                        
                        if target_city:
                            filtered_suggestions = []
                            for suggestion in all_suggestions:
                                suggestion_city = GeocodingService._extract_city_from_address(suggestion.get("address", {}))
                                
                                if suggestion_city and suggestion_city == target_city:
                                    # Remove address from final suggestion (not needed in response)
                                    filtered_suggestion = {
                                        "display_name": suggestion["display_name"],
                                        "lat": suggestion["lat"],
                                        "lng": suggestion["lng"],
                                        "place_id": suggestion.get("place_id"),
                                    }
                                    filtered_suggestions.append(filtered_suggestion)
                                else:
                                    print(f"[GeocodingService] Filtered out '{suggestion['display_name']}' - city: {suggestion_city} (target: {target_city})")
                            
                            suggestions = filtered_suggestions[:limit]  # Apply limit after filtering
                            print(f"[GeocodingService] Filtered to {len(suggestions)} suggestions in same city ({target_city})")
                        else:
                            # If we can't determine city, fall back to distance filtering
                            print("[GeocodingService] Could not determine city from location, falling back to distance filtering")
                            filtered_suggestions = []
                            for suggestion in all_suggestions:
                                distance_km = GeocodingService._calculate_distance(
                                    location_bias.lat,
                                    location_bias.lng,
                                    suggestion["lat"],
                                    suggestion["lng"]
                                )
                                if distance_km <= GeocodingService.RADIUS_KM:
                                    # Remove address from final suggestion
                                    filtered_suggestion = {
                                        "display_name": suggestion["display_name"],
                                        "lat": suggestion["lat"],
                                        "lng": suggestion["lng"],
                                        "place_id": suggestion.get("place_id"),
                                    }
                                    filtered_suggestions.append(filtered_suggestion)
                                else:
                                    print(f"[GeocodingService] Filtered out '{suggestion['display_name']}' - {distance_km:.2f}km away (beyond {GeocodingService.RADIUS_KM}km limit)")
                            
                            suggestions = filtered_suggestions[:limit]  # Apply limit after filtering
                            print(f"[GeocodingService] Filtered to {len(suggestions)} suggestions within {GeocodingService.RADIUS_KM}km radius")
                    else:
                        # Remove address from suggestions (not needed in response)
                        suggestions = [
                            {
                                "display_name": s["display_name"],
                                "lat": s["lat"],
                                "lng": s["lng"],
                                "place_id": s.get("place_id"),
                            }
                            for s in all_suggestions[:limit]
                        ]
                    
                    print(f"[GeocodingService] Returning {len(suggestions)} suggestions")
                    for i, suggestion in enumerate(suggestions):
                        print(f"  [{i+1}] {suggestion['display_name']} ({suggestion['lat']}, {suggestion['lng']})")
                    
                    return suggestions
                else:
                    print(f"[GeocodingService] Nominatim error: Status {response.status_code}")
                    print(f"[GeocodingService] Response text: {response.text[:500]}")
        
        except httpx.TimeoutException as e:
            print(f"[GeocodingService] Timeout error: {e}")
        except httpx.RequestError as e:
            print(f"[GeocodingService] Request error: {e}")
        except Exception as e:
            print(f"[GeocodingService] Unexpected error: {e}")
            import traceback
            print(traceback.format_exc())
        
        print("[GeocodingService] Returning empty list")
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

