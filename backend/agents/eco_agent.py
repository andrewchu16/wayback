"""Eco agent: penalizes cars, rewards transit/walk/bike"""
from typing import List
from agents.agent_base import BaseAgent
from utils.models import NormalizedOption, AgentRecommendation


class EcoAgent(BaseAgent):
    """Agent that recommends the most environmentally friendly route"""
    
    def _get_mode_weight(self, mode: str) -> float:
        """Get base weight for transportation mode (higher = better)"""
        mode_weights = {
            "walk": 1.0,
            "bike": 0.95,
            "transit": 0.9,
            "micromobility": 0.85,  # Scooters
            "ridehail": 0.5,
            "drive": 0.3
        }
        return mode_weights.get(mode, 0.5)
    
    def score(self, options: List[NormalizedOption]) -> AgentRecommendation:
        """Recommend option with best eco score (considering mode and CO2)"""
        if not options:
            return AgentRecommendation(
                option_id="",
                score=0.0,
                why="No options available"
            )
        
        scored_options = []
        
        for opt in options:
            # Base score from mode
            base_score = self._get_mode_weight(opt.mode)
            
            # Penalize CO2 emissions
            co2_penalty = 0.0001 * (opt.co2_g or 0)
            
            # Final score
            final_score = base_score - co2_penalty
            final_score = max(0.0, min(1.0, final_score))  # Clamp to 0-1
            
            scored_options.append((opt, final_score))
        
        # Find best eco option
        best_option, best_score = max(scored_options, key=lambda x: x[1])
        
        # Generate rationale
        mode_names = {
            "walk": "walking",
            "bike": "biking",
            "transit": "public transit",
            "micromobility": "scooter",
            "ridehail": "ridehail",
            "drive": "driving"
        }
        
        mode_name = mode_names.get(best_option.mode, best_option.mode)
        co2_text = f" with low emissions ({best_option.co2_g or 0}g CO₂)" if best_option.co2_g and best_option.co2_g < 500 else ""
        
        return AgentRecommendation(
            option_id=best_option.id,
            score=best_score,
            why=f"Eco-friendly {mode_name} option{co2_text}"
        )

