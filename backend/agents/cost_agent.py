"""Cost agent: minimizes cost with hard cap (reject if >2x fastest)"""
from typing import List
from agents.agent_base import BaseAgent
from utils.models import NormalizedOption, AgentRecommendation


class CostAgent(BaseAgent):
    """Agent that recommends the cheapest route"""
    
    def score(self, options: List[NormalizedOption]) -> AgentRecommendation:
        """Recommend option with minimum cost (hard cap: reject if >2x fastest time)"""
        if not options:
            return AgentRecommendation(
                option_id="",
                score=0.0,
                why="No options available"
            )
        
        # Find fastest time first (for hard cap)
        fastest_time = min(opt.total_time_min for opt in options)
        time_cap = fastest_time * 2.0
        
        # Filter options that meet time cap
        viable_options = [opt for opt in options if opt.total_time_min <= time_cap]
        
        if not viable_options:
            # If nothing meets cap, return cheapest anyway
            viable_options = options
        
        # Find cheapest viable option
        cheapest = min(viable_options, key=lambda opt: opt.effective_cost_usd)
        cheapest_cost = cheapest.effective_cost_usd
        
        # Calculate score: inverse of normalized cost (cheaper = higher score)
        max_cost = max(opt.effective_cost_usd for opt in viable_options)
        min_cost = cheapest_cost
        
        if max_cost == min_cost:
            score = 1.0
        else:
            # Normalize: cheapest gets 1.0, most expensive gets ~0.1
            score = 1.0 - ((cheapest_cost - min_cost) / (max_cost - min_cost)) * 0.9
        
        # Penalize if it doesn't meet time cap
        if cheapest.total_time_min > time_cap:
            score *= 0.5
        
        return AgentRecommendation(
            option_id=cheapest.id,
            score=max(0.1, score),
            why=f"Lowest fare at ${cheapest_cost:.2f} with reasonable time"
        )

