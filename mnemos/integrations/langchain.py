from typing import Any, Dict, List, Optional
try:
    from langchain_core.memory import BaseMemory
    from langchain_core.pydantic_v1 import Field
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    BaseMemory = object

class MnemosLangchainMemory(BaseMemory):
    """
    LangChain integration for MNEMOS.
    Uses the MNEMOS API to persistently store user inputs and retrieve relevant context.
    """
    
    api_url: str = "http://localhost:8000/v1"
    user_id: str = "default"
    memory_key: str = "mnemos_history"
    
    @property
    def memory_variables(self) -> List[str]:
        return [self.memory_key]
        
    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Research the context related to the user's input.
        """
        import requests
        if not LANGCHAIN_AVAILABLE:
            raise ImportError("Langchain is not installed.")
            
        # Simplistic: grab the first string input as the query
        query = next(iter(inputs.values())) if inputs else ""
        
        try:
            res = requests.post(f"{self.api_url}/research", json={
                "question": str(query),
                "user_id": self.user_id,
                "max_iters": 1
            })
            if res.status_code == 200:
                answer = res.json().get("answer", "")
                return {self.memory_key: answer}
        except Exception as e:
            print(f"MNEMOS retrieval error: {e}")
            
        return {self.memory_key: ""}
        
    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, str]) -> None:
        """
        Save the interaction into MNEMOS.
        """
        import requests
        if not LANGCHAIN_AVAILABLE:
            return
            
        # Concatenate inputs and outputs to memorize the exchange
        user_msg = next(iter(inputs.values())) if inputs else ""
        ai_msg = next(iter(outputs.values())) if outputs else ""
        
        fact = f"User said: {user_msg}\nAI responded: {ai_msg}"
        
        try:
            requests.post(f"{self.api_url}/memories", json={
                "text": fact,
                "user_id": self.user_id
            })
        except Exception as e:
            print(f"MNEMOS storage error: {e}")
            
    def clear(self) -> None:
        # For a persistent memory store, clear might just be a no-op 
        # or require a GDPR erasure call.
        pass
