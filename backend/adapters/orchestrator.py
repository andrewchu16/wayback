"""Orchestrator for parallel async calls to provider adapters"""
from typing import List
import asyncio
from utils.models import NormalizedOption, Location
from adapters.lime_adapter import get_lime_options
from adapters.transit_adapter import get_transit_options
from adapters.baseline_adapter import get_baseline_options


async def gather_all_options(
    origin: Location,
    destination: Location,
    when: str = None
) -> List[NormalizedOption]:
    """
    Gather all route options from all providers in parallel.
    
    Args:
        origin: Origin location
        destination: Destination location
        when: ISO8601 datetime string for departure time
    
    Returns:
        List of normalized route options
    """
    # Run all adapters in parallel
    results = await asyncio.gather(
        get_lime_options(origin, destination),
        get_transit_options(origin, destination, when),
        get_baseline_options(origin, destination),
        return_exceptions=True
    )
    
    # Flatten results and filter out exceptions/None
    all_options = []
    for result in results:
        if isinstance(result, Exception):
            # Log error but continue
            print(f"Adapter error: {result}")
            continue
        if result:
            if isinstance(result, list):
                all_options.extend(result)
            else:
                all_options.append(result)
    
    # Always ensure at least walking baseline
    if not all_options:
        # Fallback: create a basic walking option
        from adapters.baseline_adapter import get_baseline_options
        baseline = await get_baseline_options(origin, destination)
        if baseline:
            all_options.extend(baseline)
    
    return all_options

