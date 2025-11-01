"""Speed agent: minimizes total_time_min"""
from typing import List
from agents.agent_base import BaseAgent
from utils.models import NormalizedOption, AgentRecommendation


class SpeedAgent(BaseAgent):
    """Agent that recommends the fastest route"""
    
    def score(self, options: List[NormalizedOption]) -> AgentRecommendation:
        """Recommend option with minimum total_time_min"""
        if not options:
            # Fallback: return None or default
            return AgentRecommendation(
                option_id="",
                score=0.0,
                why="No options available"
            )
        
        # Find fastest option
        fastest = min(options, key=lambda opt: opt.total_time_min)
        fastest_time = fastest.total_time_min
        
        # Calculate score: inverse of normalized time (faster = higher score)
        max_time = max(opt.total_time_min for opt in options)
        min_time = fastest_time
        
        if max_time == min_time:
            score = 1.0
        else:
            # Normalize: fastest gets 1.0, slowest gets ~0.1
            score = 1.0 - ((fastest_time - min_time) / (max_time - min_time)) * 0.9
        
        return AgentRecommendation(
            option_id=fastest.id,
            score=max(0.1, score),
            why=f"Fastest door-to-door at {fastest_time} minutes"
        )

