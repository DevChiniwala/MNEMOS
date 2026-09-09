import json
from typing import Dict, Any, Optional
from mnemos.generator import AbsGenerator

class EmotionalSalienceScorer:
    """
    Evaluates the emotional weight and importance (salience) of a memory.
    Highly salient memories (traumatic, euphoric, critical) decay slower
    and are prioritized in retrieval.
    """
    
    def __init__(self, generator: Optional[AbsGenerator] = None):
        self.generator = generator

    def score(self, text: str) -> float:
        """
        Returns a salience score between 0.0 (neutral/trivial) and 1.0 (highly salient).
        Uses LLM if available, otherwise falls back to keyword heuristics.
        """
        if self.generator:
            return self._score_with_llm(text)
        return self._score_with_heuristics(text)

    def _score_with_llm(self, text: str) -> float:
        prompt = (
            "Analyze the emotional intensity and critical importance of the following memory. "
            "Return a JSON object with a single key 'salience' containing a float between 0.0 (trivial, mundane) "
            "and 1.0 (highly emotional, critical, life-altering).\n\n"
            f"Memory: {text}\n\n"
            "JSON:"
        )
        try:
            # Assuming generator has a raw generation or similar method
            # In mnemos, usually generate(prompt) or similar.
            # We'll use a generic approach assuming a standard text generation interface.
            # JITMIND uses _generate or generate depending on the wrapper.
            # Let's rely on standard text output.
            if hasattr(self.generator, "generate"):
                response = self.generator.generate(prompt)
            else:
                return 0.5 # Safe fallback
                
            # Naive json extraction
            start = response.find("{")
            end = response.rfind("}") + 1
            if start != -1 and end != -1:
                data = json.loads(response[start:end])
                return float(data.get("salience", 0.5))
            return 0.5
        except Exception:
            return self._score_with_heuristics(text)

    def _score_with_heuristics(self, text: str) -> float:
        """Fallback fast heuristic scoring based on affect words."""
        high_salience_words = {"never", "always", "hate", "love", "died", "born", "fired", "hired", "critical", "urgent", "danger", "warning", "panic", "thrilled"}
        medium_salience_words = {"important", "sad", "happy", "angry", "upset", "excited", "worried", "changed"}
        
        words = set(text.lower().split())
        
        if words.intersection(high_salience_words):
            return 0.8
        elif words.intersection(medium_salience_words):
            return 0.5
        return 0.1 # Default low salience for mundane facts
        
class FadingAffectModel:
    """
    Implements Fading Affect Bias (FAB): 
    The emotional impact of memories fades over time, but negative affect fades faster than positive affect.
    """
    
    @staticmethod
    def calculate_decayed_salience(initial_salience: float, is_positive: bool, days_elapsed: float) -> float:
        # Negative memories decay faster (higher decay rate)
        decay_rate = 0.05 if is_positive else 0.15
        
        # Exponential decay of salience
        import math
        return initial_salience * math.exp(-decay_rate * days_elapsed)
