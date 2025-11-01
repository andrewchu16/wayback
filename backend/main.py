from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
import stripe

from utils.models import (
    Location, PlanResponse, CheckoutRequest, CheckoutResponse
)
from adapters.orchestrator import gather_all_options
from agents.speed_agent import SpeedAgent
from agents.cost_agent import CostAgent
from agents.eco_agent import EcoAgent
from agents.safety_agent import SafetyAgent
from utils.mcp_client import MCPClient

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
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")


class PlanRequest(BaseModel):
    """Request for /plan endpoint"""
    origin: dict  # {"lat": float, "lng": float}
    destination: dict  # {"lat": float, "lng": float}
    when: Optional[str] = None  # ISO8601 datetime


@app.get("/")
async def root():
    return {"message": "Route Finder API"}


@app.post("/plan", response_model=PlanResponse)
async def plan(request: PlanRequest):
    """
    Main orchestrator endpoint: gather options from providers and run agents.
    
    Returns normalized options with agent recommendations.
    """
    try:
        # Convert request to Location models
        origin = Location(lat=request.origin["lat"], lng=request.origin["lng"])
        destination = Location(
            lat=request.destination["lat"], 
            lng=request.destination["lng"]
        )
        
        # Gather all options from providers in parallel
        options = await gather_all_options(origin, destination, request.when)
        
        if not options:
            # Fallback: return at least walking
            raise HTTPException(status_code=500, detail="No route options available")
        
        # Get safety data if needed
        safety_client = MCPClient()
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
            risk_penalty = 0.0
            night_walk_min = 0
        finally:
            safety_client.close()
        
        # Run agents
        speed_agent = SpeedAgent()
        cost_agent = CostAgent()
        eco_agent = EcoAgent()
        safety_agent = SafetyAgent()
        
        try:
            speed_rec = speed_agent.score(options)
            cost_rec = cost_agent.score(options)
            eco_rec = eco_agent.score(options)
            safety_rec = safety_agent.score(
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
    
    except Exception as e:
        print(f"Plan error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/payments/checkout", response_model=CheckoutResponse)
async def create_checkout(checkout_request: CheckoutRequest):
    """
    Create Stripe Checkout session for service fee.
    
    Returns checkout URL for redirect.
    """
    if not stripe.api_key:
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

