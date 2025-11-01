"""Safety agent: prefers minimal walking at night, avoids risky segments"""
from typing import List, Optional
from agents.agent_base import BaseAgent
from utils.models import NormalizedOption, AgentRecommendation


class SafetyAgent(BaseAgent):
    """Agent that recommends the safest route"""
    
    def score(self, options: List[NormalizedOption], 
              time_of_day: Optional[str] = None,
              risk_penalty: Optional[float] = None,
              night_walk_minutes: Optional[int] = None) -> AgentRecommendation:
        """
        Recommend safest option considering walking time, night time, and risk.
        
        Args:
            options: List of route options
            time_of_day: ISO8601 datetime string
            risk_penalty: Pre-computed risk penalty (0-0.3)
            night_walk_minutes: Pre-computed night walking minutes
        """
        if not options:
            return AgentRecommendation(
                option_id="",
                score=0.0,
                why="No options available"
            )
        
        scored_options = []
        
        for opt in options:
            # Base: prefer shorter total time
            time_score = 1.0 - self._normalize_score(opt.total_time_min, 0, 120)
            
            # Penalize walking at night
            walk_penalty = 0.0
            if opt.walk_min and opt.walk_min > 0:
                if night_walk_minutes and night_walk_minutes > 0:
                    # Heavy penalty for night walking
                    walk_penalty = min(0.4, opt.walk_min * 0.1)
                else:
                    # Light penalty for day walking
                    walk_penalty = min(0.2, opt.walk_min * 0.05)
            
            # Apply risk penalty
            risk = risk_penalty or 0.0
            
            # Final score: time_score minus penalties
            final_score = time_score - walk_penalty - risk * 0.5
            final_score = max(0.0, min(1.0, final_score))
            
            scored_options.append((opt, final_score))
        
        # Find safest option
        safest_option, safest_score = max(scored_options, key=lambda x: x[1])
        
        # Generate rationale
        if safest_option.walk_min and safest_option.walk_min > 5:
            rationale = f"Minimal walking ({safest_option.walk_min} min) reduces exposure"
        elif safest_option.mode == "ridehail":
            rationale = f"Door-to-door service avoids walking at night"
        else:
            rationale = f"Balanced route with safety considerations"
        
        return AgentRecommendation(
            option_id=safest_option.id,
            score=safest_score,
            why=rationale
        )

