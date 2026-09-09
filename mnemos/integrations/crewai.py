try:
    from crewai.tools import tool
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    
    # Mock decorator if not installed
    def tool(name):
        def decorator(func):
            return func
        return decorator

import requests

API_URL = "http://localhost:8000/v1"

@tool("MNEMOS_Memorize")
def mnemos_memorize(text: str, user_id: str = "default") -> str:
    """
    Use this tool to store important facts, user preferences, or decisions into long-term memory.
    The memory is self-editing and will resolve contradictions automatically.
    """
    try:
        res = requests.post(f"{API_URL}/memories", json={
            "text": text,
            "user_id": user_id
        })
        if res.status_code == 200:
            return "Memory stored successfully."
        return f"Failed to store memory: {res.text}"
    except Exception as e:
        return f"Error connecting to MNEMOS: {e}"

@tool("MNEMOS_Research")
def mnemos_research(question: str, user_id: str = "default") -> str:
    """
    Use this tool to research past context, previous interactions, or historical knowledge 
    stored in the long-term memory system.
    """
    try:
        res = requests.post(f"{API_URL}/research", json={
            "question": question,
            "user_id": user_id,
            "max_iters": 2
        })
        if res.status_code == 200:
            return res.json().get("answer", "No relevant context found.")
        return f"Failed to research memory: {res.text}"
    except Exception as e:
        return f"Error connecting to MNEMOS: {e}"
