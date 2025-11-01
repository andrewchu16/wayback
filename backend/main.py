from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import random
import asyncio

app = FastAPI(title="Route Finder API")

# Enable CORS for Expo app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your Expo app URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Location(BaseModel):
    latitude: float
    longitude: float


class RouteRequest(BaseModel):
    origin: Location
    destination: Location


class RouteSegment(BaseModel):
    transport_mode: str
    distance_meters: float
    duration_seconds: int
    instructions: str


class Route(BaseModel):
    id: str
    transport_modes: List[str]
    total_distance_meters: float
    total_duration_seconds: int
    cost_usd: float
    segments: List[RouteSegment]
    polyline: str  # Encoded polyline for map display


class RoutesResponse(BaseModel):
    routes: List[Route]


# Mock transportation modes with typical pricing
TRANSPORT_MODES = [
    {"name": "Uber", "base_cost": 8.0, "cost_per_km": 1.5, "speed_kmh": 45},
    {"name": "Lyft", "base_cost": 7.5, "cost_per_km": 1.4, "speed_kmh": 45},
    {"name": "Lime", "base_cost": 1.0, "cost_per_min": 0.3, "speed_kmh": 20},
    {"name": "Walking", "base_cost": 0.0, "cost_per_km": 0.0, "speed_kmh": 5},
    {"name": "Public Transit", "base_cost": 2.5, "cost_per_km": 0.0, "speed_kmh": 30},
]


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in meters using Haversine formula"""
    from math import radians, sin, cos, sqrt, atan2
    
    R = 6371000  # Earth radius in meters
    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)
    delta_lat = radians(lat2 - lat1)
    delta_lon = radians(lon2 - lon1)
    
    a = sin(delta_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    
    return R * c


def generate_polyline(origin: Location, destination: Location) -> str:
    """Generate a simple polyline between origin and destination"""
    # This is a simplified polyline - in production, you'd use a real routing service
    # Format: "lat1,lon1|lat2,lon2|..."
    mid_lat = (origin.latitude + destination.latitude) / 2
    mid_lon = (origin.longitude + destination.longitude) / 2
    return f"{origin.latitude},{origin.longitude}|{mid_lat},{mid_lon}|{destination.latitude},{destination.longitude}"


@app.get("/")
async def root():
    return {"message": "Route Finder API"}


@app.post("/api/routes", response_model=RoutesResponse)
async def calculate_routes(request: RouteRequest):
    """
    Calculate multiple route options between origin and destination.
    Uses mock data to simulate AI agent route calculation.
    """
    # Simulate AI processing delay
    await asyncio.sleep(1.5)
    
    distance = calculate_distance(
        request.origin.latitude,
        request.origin.longitude,
        request.destination.latitude,
        request.destination.longitude
    )
    
    routes = []
    
    for mode in TRANSPORT_MODES:
        # Calculate duration based on speed
        duration_seconds = int((distance / 1000) / mode["speed_kmh"] * 3600)
        
        # Add some variance for realism
        duration_seconds += random.randint(-60, 120)
        duration_seconds = max(60, duration_seconds)  # Minimum 1 minute
        
        # Calculate cost
        if mode["name"] == "Lime":
            cost = mode["base_cost"] + (duration_seconds / 60) * mode["cost_per_min"]
        else:
            cost = mode["base_cost"] + (distance / 1000) * mode["cost_per_km"]
        
        # Generate route segments (simplified - just one segment for now)
        segments = [
            RouteSegment(
                transport_mode=mode["name"],
                distance_meters=distance,
                duration_seconds=duration_seconds,
                instructions=f"Take {mode['name']} to destination"
            )
        ]
        
        route = Route(
            id=f"{mode['name'].lower().replace(' ', '_')}_{random.randint(1000, 9999)}",
            transport_modes=[mode["name"]],
            total_distance_meters=distance,
            total_duration_seconds=duration_seconds,
            cost_usd=round(cost, 2),
            segments=segments,
            polyline=generate_polyline(request.origin, request.destination)
        )
        
        routes.append(route)
    
    # Sort by duration (fastest first)
    routes.sort(key=lambda r: r.total_duration_seconds)
    
    return RoutesResponse(routes=routes)

