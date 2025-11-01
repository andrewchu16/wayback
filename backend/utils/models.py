"""Pydantic models for normalized options and agent responses"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class Location(BaseModel):
    lat: float
    lng: float


class NormalizedOption(BaseModel):
    """Normalized option structure returned by adapters"""
    id: str
    mode: str  # ridehail, transit, micromobility, walk, bike, drive
    provider: str
    product: Optional[str] = None  # e.g., "Lyft", "UberX", "38"
    line: Optional[str] = None  # Transit line name
    
    # Timing
    eta_pickup_min: Optional[int] = None  # For ridehail
    wait_min: Optional[int] = None  # For transit/micromobility
    duration_min: int
    walk_min: Optional[int] = 0
    
    # Cost
    cost_usd: float
    
    # Environmental
    co2_g: Optional[int] = 0
    
    # Deep linking
    deeplink: Optional[str] = None
    
    # Additional metadata
    metadata: Optional[Dict[str, Any]] = None
    
    @property
    def total_time_min(self) -> int:
        """Calculate total time: pickup/wait + duration + walk"""
        return (self.eta_pickup_min or self.wait_min or 0) + self.duration_min + (self.walk_min or 0)
    
    @property
    def effective_cost_usd(self) -> float:
        """Effective cost (same as cost_usd for now)"""
        return self.cost_usd or 0.0


class AgentRecommendation(BaseModel):
    """Agent recommendation with option ID, score, and rationale"""
    option_id: str
    score: float  # 0.0 to 1.0
    why: str  # One sentence rationale


class PlanResponse(BaseModel):
    """Response from /plan endpoint"""
    options: List[NormalizedOption]
    agents: Dict[str, AgentRecommendation]  # speed, cost, eco, safety


class CheckoutRequest(BaseModel):
    """Request for Stripe checkout"""
    amount_cents: int
    success_url: str
    cancel_url: str


class CheckoutResponse(BaseModel):
    """Response from /payments/checkout endpoint"""
    checkout_url: str

