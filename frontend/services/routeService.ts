import Constants from 'expo-constants';

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

// Backend response interfaces
export interface NormalizedOption {
  id: string;
  mode: string; // ridehail, transit, micromobility, walk, bike, drive
  provider: string;
  product?: string;
  line?: string;
  eta_pickup_min?: number;
  wait_min?: number;
  duration_min: number;
  walk_min?: number;
  cost_usd: number;
  co2_g?: number;
  deeplink?: string;
  metadata?: Record<string, any>;
}

export interface AgentRecommendation {
  option_id: string;
  score: number;
  why: string;
}

export interface PlanResponse {
  options: NormalizedOption[];
  agents: {
    speed?: AgentRecommendation;
    cost?: AgentRecommendation;
    eco?: AgentRecommendation;
    safety?: AgentRecommendation;
  };
}

// ngrok tunnel URL - allows accessing backend from anywhere
// Get your ngrok URL by running: cd backend && .\get_ngrok_url.ps1
// Or check: http://localhost:4040
// API_BASE_URL is configured via environment variable in app.json (expo.extra.apiBaseUrl)
const API_BASE_URL = Constants.expoConfig?.extra?.apiBaseUrl || 'https://d1f12f5f540a.ngrok-free.app';

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

// Helper function to convert backend NormalizedOption to frontend Route
function normalizeOptionToRoute(
  option: NormalizedOption,
  origin: Location,
  destination: Location
): Route {
  // Calculate distance (fallback estimate if not provided)
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

  // Estimate distance based on duration if available
  const avgSpeed = option.mode === 'walk' ? 5 : option.mode === 'transit' ? 30 : 40; // km/h
  const estimatedDistance = option.duration_min > 0 
    ? (option.duration_min / 60) * avgSpeed * 1000 
    : distance;

  // Generate simple polyline (in production, this would come from the backend)
  const midLat = (origin.latitude + destination.latitude) / 2;
  const midLon = (origin.longitude + destination.longitude) / 2;
  const polyline = `${origin.latitude},${origin.longitude}|${midLat},${midLon}|${destination.latitude},${destination.longitude}`;

  // Determine transport mode display name
  const modeNames: Record<string, string> = {
    ridehail: option.product || option.provider || 'Ride',
    transit: option.line || option.product || 'Public Transit',
    micromobility: option.provider || 'Scooter',
    walk: 'Walking',
    bike: 'Bike',
    drive: 'Drive',
  };

  const transportMode = modeNames[option.mode] || option.provider || option.mode;

  // Calculate total time (pickup/wait + duration + walk)
  const totalTimeMin = (option.eta_pickup_min || option.wait_min || 0) + option.duration_min + (option.walk_min || 0);
  
  // Calculate total duration in seconds
  const totalDurationSeconds = totalTimeMin * 60;

  // Create segments
  const segments: RouteSegment[] = [];
  
  if (option.walk_min && option.walk_min > 0) {
    segments.push({
      transport_mode: 'Walking',
      distance_meters: Math.round(estimatedDistance * 0.1), // Estimate walk distance
      duration_seconds: option.walk_min * 60,
      instructions: 'Walk to pickup point',
    });
  }

  segments.push({
    transport_mode: transportMode,
    distance_meters: Math.round(estimatedDistance),
    duration_seconds: option.duration_min * 60,
    instructions: option.product 
      ? `Take ${transportMode}${option.line ? ` - ${option.line}` : ''} to destination`
      : `Take ${transportMode} to destination`,
  });

  return {
    id: option.id,
    transport_modes: [transportMode],
    total_distance_meters: Math.round(estimatedDistance),
    total_duration_seconds: totalDurationSeconds,
    cost_usd: option.cost_usd,
    segments,
    polyline,
  };
}

export class RouteService {
  static async calculateRoutes(
    origin: Location,
    destination: Location,
    when?: string,
    useMockFallback: boolean = true
  ): Promise<Route[]> {
    try {
      // Convert frontend location format (latitude/longitude) to backend format (lat/lng)
      const response = await fetch(`${API_BASE_URL}/plan`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          origin: {
            lat: origin.latitude,
            lng: origin.longitude,
          },
          destination: {
            lat: destination.latitude,
            lng: destination.longitude,
          },
          when: when,
        }),
      });

      if (!response.ok) {
        // Try to get error details from response body
        let errorMessage = `Failed to calculate routes: ${response.status}`;
        try {
          const errorData = await response.json();
          if (errorData.detail) {
            errorMessage = `Failed to calculate routes: ${errorData.detail}`;
          }
        } catch (e) {
          // If response is not JSON, use status text
          errorMessage = `Failed to calculate routes: ${response.status} ${response.statusText}`;
        }
        throw new Error(errorMessage);
      }

      const data: PlanResponse = await response.json();
      
      // Convert backend NormalizedOption[] to frontend Route[]
      return data.options.map(option => normalizeOptionToRoute(option, origin, destination));
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

