import re
from typing import Tuple

class PIIRedactor:
    """
    A lightweight, regex-based PII redaction engine.
    For production, this should be augmented with an NER model (e.g., Presidio).
    """
    
    # Simple patterns for demonstration
    PATTERNS = {
        "EMAIL": r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
        "PHONE": r"\+?\d{1,4}?[-.\s]?\(?\d{1,3}?\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}",
        "SSN": r"\b\d{3}-\d{2}-\d{4}\b",
        "CREDIT_CARD": r"\b(?:\d[ -]*?){13,16}\b"
    }

    @classmethod
    def redact(cls, text: str) -> Tuple[str, dict]:
        """
        Redacts PII from text.
        Returns the redacted text and a dictionary of finding counts.
        """
        redacted_text = text
        stats = {}
        
        for entity_type, pattern in cls.PATTERNS.items():
            matches = re.findall(pattern, redacted_text)
            if matches:
                stats[entity_type] = len(matches)
                redacted_text = re.sub(pattern, f"[{entity_type}_REDACTED]", redacted_text)
                
        return redacted_text, stats
