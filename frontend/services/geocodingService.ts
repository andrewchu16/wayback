import Constants from 'expo-constants';
import { Location } from './routeService';

export interface AutocompleteSuggestion {
  display_name: string;
  lat: number;
  lng: number;
  place_id?: string;
}

const API_BASE_URL = Constants.expoConfig?.extra?.apiBaseUrl || 'https://d1f12f5f540a.ngrok-free.app';

export class GeocodingService {
  /**
   * Fetches autocomplete suggestions for a given search query.
   * 
   * @param query - The search query string (minimum 2 characters)
   * @param limit - Maximum number of suggestions to return (default: 5)
   * @param locationBias - Optional location to bias results towards (prioritizes nearby locations)
   * @returns Promise resolving to an array of autocomplete suggestions, or empty array if query is too short or request fails
   * @throws Logs errors to console but returns empty array instead of throwing
   */
  static async autocomplete(
    query: string,
    limit: number = 5,
    locationBias?: Location
  ): Promise<AutocompleteSuggestion[]> {
    if (!query || query.trim().length < 2) {
      return [];
    }

    try {
      const params = new URLSearchParams({
        q: query.trim(),
        limit: limit.toString(),
      });

      if (locationBias) {
        params.append('lat', locationBias.latitude.toString());
        params.append('lng', locationBias.longitude.toString());
      }

      const response = await fetch(`${API_BASE_URL}/autocomplete?${params.toString()}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Autocomplete failed: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      return data.suggestions || [];
    } catch (error: any) {
      console.error('Error fetching autocomplete:', error);
      return [];
    }
  }

  /**
   * Geocodes a query string to a geographic location (latitude and longitude).
   * 
   * @param query - The location query to geocode (e.g., "New York, NY" or an address)
   * @param locationBias - Optional location to bias the geocoding towards (helps disambiguate when multiple locations match)
   * @returns Promise resolving to a Location object with latitude and longitude, or null if geocoding fails or no location is found
   * @throws Logs errors to console but returns null instead of throwing
   */
  static async geocode(
    query: string,
    locationBias?: Location
  ): Promise<Location | null> {
    try {
      const response = await fetch(`${API_BASE_URL}/geocode`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query,
          location_bias: locationBias
            ? { lat: locationBias.latitude, lng: locationBias.longitude }
            : null,
        }),
      });

      if (!response.ok) {
        throw new Error(`Geocode failed: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      if (data.location) {
        return {
          latitude: data.location.lat,
          longitude: data.location.lng,
        };
      }
      return null;
    } catch (error: any) {
      console.error('Error geocoding:', error);
      return null;
    }
  }

  /**
   * Reverse geocodes coordinates to get an address/place name.
   * 
   * @param location - The location coordinates to reverse geocode
   * @returns Promise resolving to an AutocompleteSuggestion with display_name, lat, lng, and place_id, or null if reverse geocoding fails
   * @throws Logs errors to console but returns null instead of throwing
   */
  static async reverseGeocode(
    location: Location
  ): Promise<AutocompleteSuggestion | null> {
    try {
      const response = await fetch(`${API_BASE_URL}/reverse-geocode`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          lat: location.latitude,
          lng: location.longitude,
        }),
      });

      if (!response.ok) {
        throw new Error(`Reverse geocode failed: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      if (data.suggestion) {
        return {
          display_name: data.suggestion.display_name,
          lat: data.suggestion.lat,
          lng: data.suggestion.lng,
          place_id: data.suggestion.place_id,
        };
      }
      return null;
    } catch (error: any) {
      console.error('Error reverse geocoding:', error);
      return null;
    }
  }
}

