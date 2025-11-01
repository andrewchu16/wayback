from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import stripe

from settings import settings
from utils.models import (
    Location, PlanResponse, CheckoutRequest, CheckoutResponse
)
from adapters.orchestrator import gather_all_options
from agents.speed_agent import SpeedAgent
from agents.cost_agent import CostAgent
from agents.eco_agent import EcoAgent
from agents.safety_agent import SafetyAgent
from utils.mcp_client import MCPClient
from utils.geocoding import GeocodingService as BackendGeocodingService

app = FastAPI(title="Route Finder API")

# Enable CORS for Expo app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your Expo app URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Stripe (if key available)
stripe.api_key = settings.stripe_secret_key


class PlanRequest(BaseModel):
    """Request for /plan endpoint"""
    origin: dict  # {"lat": float, "lng": float}
    destination: dict  # {"lat": float, "lng": float}
    when: Optional[str] = None  # ISO8601 datetime


@app.get("/")
async def root():
    return {"message": "Route Finder API"}


class GeocodeRequest(BaseModel):
    """Request for /geocode endpoint"""
    query: str
    location_bias: Optional[dict] = None  # {"lat": float, "lng": float}


@app.get("/autocomplete")
async def autocomplete(
    q: str,
    limit: int = 5,
    lat: Optional[float] = None,
    lng: Optional[float] = None
):
    """
    Get autocomplete suggestions for a search query.
    
    Returns a list of location suggestions with display names and coordinates.
    """
    try:
        print(f"[Backend] Autocomplete endpoint called: q='{q}', limit={limit}, lat={lat}, lng={lng}")
        
        location_bias = None
        if lat is not None and lng is not None:
            location_bias = Location(lat=lat, lng=lng)
            print(f"[Backend] Using location bias: {location_bias}")
        else:
            print("[Backend] No location bias provided")
        
        suggestions = await BackendGeocodingService.autocomplete(
            query=q,
            limit=limit,
            location_bias=location_bias
        )
        
        print(f"[Backend] Returning {len(suggestions)} suggestions to frontend")
        return {"suggestions": suggestions}
    except Exception as e:
        print(f"[Backend] Autocomplete error: {e}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/geocode")
async def geocode(request: GeocodeRequest):
    """
    Geocode a query string to get coordinates.
    
    Returns a location with latitude and longitude, or null if not found.
    """
    try:
        location_bias = None
        if request.location_bias:
            location_bias = Location(
                lat=request.location_bias["lat"],
                lng=request.location_bias["lng"]
            )
        
        location = await BackendGeocodingService.geocode(
            query=request.query,
            location_bias=location_bias
        )
        
        if location:
            return {"location": {"lat": location.lat, "lng": location.lng}}
        return {"location": None}
    except Exception as e:
        print(f"Geocode error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class ReverseGeocodeRequest(BaseModel):
    """Request for /reverse-geocode endpoint"""
    lat: float
    lng: float


@app.post("/reverse-geocode")
async def reverse_geocode(request: ReverseGeocodeRequest):
    """
    Reverse geocode coordinates to get address/place name.
    
    Returns a location suggestion with display_name, lat, lng, and place_id, or null if not found.
    """
    try:
        location = Location(lat=request.lat, lng=request.lng)
        
        result = await BackendGeocodingService.reverse_geocode(location)
        
        if result:
            return {"suggestion": result}
        return {"suggestion": None}
    except Exception as e:
        print(f"Reverse geocode error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/plan", response_model=PlanResponse)
async def plan(request: PlanRequest):
    """
    Main orchestrator endpoint: gather options from providers and run agents.
    
    Returns normalized options with agent recommendations.
    """
    import traceback
    
    try:
        # Convert request to Location models
        origin = Location(lat=request.origin["lat"], lng=request.origin["lng"])
        destination = Location(
            lat=request.destination["lat"], 
            lng=request.destination["lng"]
        )
        
        # Gather all options from providers in parallel
        try:
            options = await gather_all_options(origin, destination, request.when)
        except Exception as e:
            print(f"Error gathering options: {e}")
            print(traceback.format_exc())
            # Return empty options list, will be handled below
            options = []
        
        if not options:
            # Try to get at least baseline options as last resort
            try:
                from adapters.baseline_adapter import get_baseline_options
                options = await get_baseline_options(origin, destination)
            except Exception as e:
                print(f"Error getting baseline options: {e}")
            
            if not options:
                raise HTTPException(
                    status_code=500, 
                    detail=f"No route options available. Origin: ({origin.lat}, {origin.lng}), Destination: ({destination.lat}, {destination.lng})"
                )
        
        # Get safety data if needed
        safety_client = MCPClient()
        risk_penalty = 0.0
        night_walk_min = 0
        try:
            # Create walk segments for safety calculation
            walk_segments = [
                {"lat": origin.lat, "lng": origin.lng},
                {"lat": destination.lat, "lng": destination.lng}
            ]
            
            safety_data = safety_client.call_tool(
                "get_safety_data",
                walk_segments=walk_segments,
                time_of_day=request.when
            )
            
            risk_penalty = safety_data.get("risk_penalty", 0.0) if isinstance(safety_data, dict) else 0.0
            night_walk_min = safety_data.get("night_walk_minutes", 0) if isinstance(safety_data, dict) else 0
        except Exception as e:
            print(f"Safety data error: {e}")
            print(traceback.format_exc())
            risk_penalty = 0.0
            night_walk_min = 0
        finally:
            safety_client.close()
        
        # Run agents with error handling
        speed_agent = SpeedAgent()
        cost_agent = CostAgent()
        eco_agent = EcoAgent()
        safety_agent = SafetyAgent()
        
        # Helper to safely get agent recommendation
        def safe_agent_score(agent, *args, **kwargs):
            try:
                return agent.score(*args, **kwargs)
            except Exception as e:
                print(f"Agent {agent.__class__.__name__} error: {e}")
                print(traceback.format_exc())
                # Return fallback recommendation
                from utils.models import AgentRecommendation
                if options:
                    return AgentRecommendation(
                        option_id=options[0].id,
                        score=0.5,
                        why="Agent unavailable, using first option"
                    )
                return AgentRecommendation(
                    option_id="",
                    score=0.0,
                    why="Agent unavailable"
                )
        
        try:
            speed_rec = safe_agent_score(speed_agent, options)
            cost_rec = safe_agent_score(cost_agent, options)
            eco_rec = safe_agent_score(eco_agent, options)
            safety_rec = safe_agent_score(
                safety_agent, 
                options,
                time_of_day=request.when,
                risk_penalty=risk_penalty,
                night_walk_minutes=night_walk_min
            )
        finally:
            speed_agent.close()
            cost_agent.close()
            eco_agent.close()
            safety_agent.close()
        
        return PlanResponse(
            options=options,
            agents={
                "speed": speed_rec,
                "cost": cost_rec,
                "eco": eco_rec,
                "safety": safety_rec
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Plan error: {e}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to calculate routes: {str(e)}"
        )


@app.post("/payments/checkout", response_model=CheckoutResponse)
async def create_checkout(checkout_request: CheckoutRequest):
    """
    Create Stripe Checkout session for service fee.
    
    Returns checkout URL for redirect.
    """
    if not settings.stripe_secret_key:
        raise HTTPException(
            status_code=500, 
            detail="Stripe not configured. Set STRIPE_SECRET_KEY environment variable."
        )
    
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": "Route Planning Service Fee",
                    },
                    "unit_amount": checkout_request.amount_cents,
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=checkout_request.success_url,
            cancel_url=checkout_request.cancel_url,
        )
        
        return CheckoutResponse(checkout_url=checkout_session.url)
    
    except Exception as e:
        print(f"Stripe checkout error: {e}")
        raise HTTPException(status_code=500, detail=f"Checkout creation failed: {str(e)}")

