"""Safety adapter for calculating risk scores based on time-of-day and route segments"""
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timedelta
from math import radians, sin, cos, sqrt, atan2


def _haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Calculate distance between two points using Haversine formula.
    
    Args:
        lat1, lng1: First point coordinates
        lat2, lng2: Second point coordinates
    
    Returns:
        Distance in meters
    """
    R = 6371000  # Earth radius in meters
    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)
    delta_lat = radians(lat2 - lat1)
    delta_lon = radians(lng2 - lng1)
    
    a = sin(delta_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance_m = R * c
    
    return distance_m


def _calculate_walk_duration_minutes(walk_segments: List[Tuple[float, float]]) -> float:
    """
    Calculate total walking duration in minutes based on segment distances.
    
    Args:
        walk_segments: List of (lat, lng) tuples for walking segments
    
    Returns:
        Estimated walking duration in minutes
    """
    if len(walk_segments) < 2:
        return 0.0
    
    total_distance_m = 0.0
    for i in range(len(walk_segments) - 1):
        lat1, lng1 = walk_segments[i]
        lat2, lng2 = walk_segments[i + 1]
        total_distance_m += _haversine_distance(lat1, lng1, lat2, lng2)
    
    # Walking speed: ~5 km/h = 1.39 m/s = 83.4 m/min
    walking_speed_m_per_min = 83.4
    duration_min = total_distance_m / walking_speed_m_per_min
    
    return duration_min


def _parse_datetime(time_of_day: Optional[str]) -> Optional[datetime]:
    """
    Parse ISO8601 datetime string to datetime object.
    
    Args:
        time_of_day: ISO8601 datetime string (e.g., "2024-01-01T20:30:00Z" or "2024-01-01T20:30:00+00:00")
    
    Returns:
        datetime object or None if parsing fails
    """
    if not time_of_day:
        return None
    
    try:
        # Handle Z suffix (UTC)
        dt_str = time_of_day.replace('Z', '+00:00')
        dt = datetime.fromisoformat(dt_str)
        return dt
    except (ValueError, AttributeError):
        return None


def _is_night_time(dt: datetime) -> bool:
    """
    Check if datetime is during night hours (22:00 - 6:00).
    
    Args:
        dt: datetime object
    
    Returns:
        True if night time, False otherwise
    """
    hour = dt.hour
    return hour >= 22 or hour < 6


def _is_evening_or_early_morning(dt: datetime) -> bool:
    """
    Check if datetime is during evening/early morning hours (20:00 - 8:00).
    
    Args:
        dt: datetime object
    
    Returns:
        True if evening/early morning, False otherwise
    """
    hour = dt.hour
    return (hour >= 20 or hour < 8) and not _is_night_time(dt)


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
    dt = _parse_datetime(time_of_day)
    if dt:
        if _is_night_time(dt):
            risk += 0.15  # Night time penalty (highest risk)
        elif _is_evening_or_early_morning(dt):
            risk += 0.08  # Evening/early morning (moderate risk)
    
    # Length-based risk: longer walks = higher risk exposure
    if len(walk_segments) >= 2:
        walk_duration_min = _calculate_walk_duration_minutes(walk_segments)
        
        if walk_duration_min > 10:
            risk += 0.10  # Long walk penalty (>10 minutes)
        elif walk_duration_min > 5:
            risk += 0.05  # Medium walk penalty (5-10 minutes)
        elif walk_duration_min > 2:
            risk += 0.02  # Short walk penalty (2-5 minutes)
    
    # Clamp to 0.0 - 0.3
    return min(0.3, max(0.0, risk))


def get_night_walk_minutes(walk_segments: List[Tuple[float, float]],
                           time_of_day: Optional[str] = None) -> int:
    """
    Calculate walking minutes that occur at night.
    
    Args:
        walk_segments: List of (lat, lng) tuples for walking segments
        time_of_day: ISO8601 datetime string
    
    Returns:
        Number of minutes spent walking during night hours (22:00 - 6:00)
    """
    if not time_of_day or len(walk_segments) < 2:
        return 0
    
    dt = _parse_datetime(time_of_day)
    if not dt:
        return 0
    
    # Calculate total walk duration
    total_walk_min = _calculate_walk_duration_minutes(walk_segments)
    
    # If starting during night time, check if walk ends before 6:00 or continues into day
    if _is_night_time(dt):
        end_time = dt + timedelta(minutes=total_walk_min)
        
        # If walk completes entirely at night
        if end_time.hour >= 22 or end_time.hour < 6:
            return int(total_walk_min)
        # If walk spans into day time (ends after 6:00)
        else:
            # Calculate minutes until 6:00
            if dt.hour >= 22:
                # Walking starts between 22:00-23:59, calculate until 6:00 next day
                hours_until_6am = (24 - dt.hour) + 6
                night_minutes = (hours_until_6am * 60) - dt.minute
            else:
                # Walking starts between 0:00-5:59, calculate until 6:00 same day
                hours_until_6am = 6 - dt.hour
                night_minutes = (hours_until_6am * 60) - dt.minute
            
            return min(int(total_walk_min), max(0, night_minutes))
    
    # If starting during day, check if walk extends into night
    start_hour = dt.hour
    end_time = dt + timedelta(minutes=total_walk_min)
    
    # Check if walk extends into night (22:00+)
    if start_hour < 22:
        if end_time.hour >= 22:
            # Walk extends into night, calculate night portion
            night_start = datetime(
                end_time.year, end_time.month, end_time.day, 22, 0, 0
            )
            night_duration = (end_time - night_start).total_seconds() / 60
            return max(0, int(night_duration))
    
    return 0

