"""Safety adapter for calculating risk scores based on time-of-day and route segments"""
from typing import Dict, Any, List, Tuple
from datetime import datetime
import pytz


def get_safety_risk_score(walk_segments: List[Tuple[float, float]], 
                          time_of_day: Optional[str] = None) -> float:
    """
    Calculate safety risk penalty (0-0.3) based on time of day and route segments.
    
    Args:
        walk_segments: List of (lat, lng) tuples for walking segments
        time_of_day: ISO8601 datetime string
    
    Returns:
        Risk penalty (0.0 = safe, 0.3 = high risk)
    """
    risk = 0.0
    
    # Time-based risk: higher at night (22:00 - 6:00)
    if time_of_day:
        try:
            dt = datetime.fromisoformat(time_of_day.replace('Z', '+00:00'))
            hour = dt.hour
            
            if hour >= 22 or hour < 6:
                risk += 0.15  # Night time penalty
            elif hour >= 20 or hour < 8:
                risk += 0.08  # Evening/early morning
        except:
            pass
    
    # Length-based risk: longer walks = higher risk
    if len(walk_segments) > 2:
        # Estimate walk distance from segments
        walk_duration_min = len(walk_segments) * 2  # Rough estimate
        if walk_duration_min > 10:
            risk += 0.10  # Long walk penalty
        elif walk_duration_min > 5:
            risk += 0.05
    
    # Clamp to 0.0 - 0.3
    return min(0.3, max(0.0, risk))


def get_night_walk_minutes(walk_segments: List[Tuple[float, float]],
                           time_of_day: Optional[str] = None) -> int:
    """Calculate walking minutes that occur at night"""
    if not time_of_day:
        return 0
    
    try:
        dt = datetime.fromisoformat(time_of_day.replace('Z', '+00:00'))
        hour = dt.hour
        
        # If it's night time (22:00 - 6:00), all walking is night walking
        if hour >= 22 or hour < 6:
            return len(walk_segments) * 2  # Rough estimate
    except:
        pass
    
    return 0

