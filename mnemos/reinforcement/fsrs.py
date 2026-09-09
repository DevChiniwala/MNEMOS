from typing import Dict, Any
from datetime import datetime, timedelta
import math

class SpacedRepetitionScheduler:
    """
    Implements a spaced repetition algorithm (inspired by FSRS / SM-2) for AI memories.
    Determines how memory strength increases upon recall and when a memory should be reviewed or consolidated.
    """
    
    def __init__(self):
        # Default stability and difficulty parameters
        self.initial_stability = 2.0  # days
        self.initial_difficulty = 5.0 # scale 1-10

    def calculate_next_review(self, stability: float, difficulty: float, recall_rating: float) -> Dict[str, Any]:
        """
        recall_rating: 1.0 (Failed/Forgot), 2.0 (Hard), 3.0 (Good), 4.0 (Easy)
        Returns the new stability, new difficulty, and the next review interval in days.
        """
        # Constrain difficulty
        new_difficulty = difficulty - 0.5 * (recall_rating - 3.0)
        new_difficulty = max(1.0, min(10.0, new_difficulty))
        
        if recall_rating < 2.0:
            # Memory lapse (failed retrieval)
            new_stability = max(1.0, stability * 0.5)
        else:
            # Successful retrieval
            # Easier recall -> higher stability multiplier
            multiplier = 1.0 + (recall_rating - 2.0) * 0.5
            # Harder material -> lower multiplier
            difficulty_penalty = (11.0 - new_difficulty) / 5.0
            
            new_stability = stability * multiplier * difficulty_penalty
            
        next_review_days = new_stability
        
        return {
            "stability": new_stability,
            "difficulty": new_difficulty,
            "next_review_days": next_review_days
        }

    def apply_reinforcement(self, entry_meta: dict) -> dict:
        """
        Applies a reinforcement event to a memory's metadata.
        Call this when an agent successfully retrieves and uses a memory.
        """
        stability = entry_meta.get("fsrs_stability", self.initial_stability)
        difficulty = entry_meta.get("fsrs_difficulty", self.initial_difficulty)
        
        # We assume implicit retrieval counts as a 'Good' (3.0) recall
        result = self.calculate_next_review(stability, difficulty, 3.0)
        
        entry_meta["fsrs_stability"] = result["stability"]
        entry_meta["fsrs_difficulty"] = result["difficulty"]
        
        next_date = datetime.utcnow() + timedelta(days=result["next_review_days"])
        entry_meta["fsrs_next_review"] = next_date.isoformat() + "Z"
        
        return entry_meta
