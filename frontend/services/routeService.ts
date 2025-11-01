export interface Location {
  latitude: number;
  longitude: number;
}

export interface RouteSegment {
  transport_mode: string;
  distance_meters: number;
  duration_seconds: number;
  instructions: string;
}

export interface Route {
  id: string;
  transport_modes: string[];
  total_distance_meters: number;
  total_duration_seconds: number;
  cost_usd: number;
  segments: RouteSegment[];
  polyline: string;
}

export interface RoutesResponse {
  routes: Route[];
}

// ngrok tunnel URL - allows accessing backend from anywhere
// Get your ngrok URL by running: cd backend && .\get_ngrok_url.ps1
// Or check: http://localhost:4040
const API_BASE_URL = __DEV__ 
  ? 'https://f997b6488d2f.ngrok-free.app' 
  : 'https://f997b6488d2f.ngrok-free.app';

// Mock fallback data generator
function generateMockRoutes(origin: Location, destination: Location): Route[] {
  const calculateDistance = (lat1: number, lon1: number, lat2: number, lon2: number): number => {
    const R = 6371000; // Earth radius in meters
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = 
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
      Math.sin(dLon / 2) * Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
  };

  const distance = calculateDistance(
    origin.latitude,
    origin.longitude,
    destination.latitude,
    destination.longitude
  );

  const modes = [
    { name: 'Uber', baseCost: 8.0, costPerKm: 1.5, speedKmh: 45 },
    { name: 'Lyft', baseCost: 7.5, costPerKm: 1.4, speedKmh: 45 },
    { name: 'Lime', baseCost: 1.0, costPerMin: 0.3, speedKmh: 20 },
    { name: 'Walking', baseCost: 0.0, costPerKm: 0.0, speedKmh: 5 },
    { name: 'Public Transit', baseCost: 2.5, costPerKm: 0.0, speedKmh: 30 },
  ];

  return modes.map((mode, index) => {
    const durationSeconds = Math.max(60, Math.round((distance / 1000) / mode.speedKmh * 3600));
    let cost = 0;
    
    if (mode.name === 'Lime') {
      cost = mode.baseCost + (durationSeconds / 60) * mode.costPerMin;
    } else {
      cost = mode.baseCost + (distance / 1000) * mode.costPerKm;
    }

    const midLat = (origin.latitude + destination.latitude) / 2;
    const midLon = (origin.longitude + destination.longitude) / 2;
    const polyline = `${origin.latitude},${origin.longitude}|${midLat},${midLon}|${destination.latitude},${destination.longitude}`;

    return {
      id: `${mode.name.toLowerCase().replace(' ', '_')}_${Date.now()}_${index}`,
      transport_modes: [mode.name],
      total_distance_meters: Math.round(distance),
      total_duration_seconds: durationSeconds,
      cost_usd: Math.round(cost * 100) / 100,
      segments: [{
        transport_mode: mode.name,
        distance_meters: Math.round(distance),
        duration_seconds: durationSeconds,
        instructions: `Take ${mode.name} to destination`,
      }],
      polyline,
    };
  }).sort((a, b) => a.total_duration_seconds - b.total_duration_seconds);
}

export class RouteService {
  static async calculateRoutes(
    origin: Location,
    destination: Location,
    useMockFallback: boolean = true
  ): Promise<Route[]> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/routes`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          origin,
          destination,
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to calculate routes: ${response.status} ${response.statusText}`);
      }

      const data: RoutesResponse = await response.json();
      return data.routes;
    } catch (error: any) {
      console.error('Error calculating routes:', error);
      
      // If backend is not available and fallback is enabled, use mock data
      if (useMockFallback && (error.message?.includes('Network request failed') || error.message?.includes('Failed to fetch'))) {
        console.warn('Backend unavailable, using mock route data');
        return generateMockRoutes(origin, destination);
      }
      
      // Provide helpful error message
      const errorMessage = error.message?.includes('Network request failed')
        ? 'Cannot connect to backend server. Make sure the backend is running on http://localhost:8000. For iOS devices, use your computer\'s IP address instead of localhost.'
        : error.message || 'Failed to calculate routes';
      
      throw new Error(errorMessage);
    }
  }
}

