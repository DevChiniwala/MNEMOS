from typing import Callable, Dict, List, Any

class MemoryEventBus:
    """
    Simple pub/sub event bus for multi-agent synchronization.
    Agents can subscribe to updates in shared namespaces.
    """
    
    def __init__(self):
        # Mapping of namespace -> list of callback functions
        self._subscribers: Dict[str, List[Callable[[Dict[str, Any]], None]]] = {}
        
    def subscribe(self, namespace: str, callback: Callable[[Dict[str, Any]], None]):
        """Subscribe to memory events in a specific namespace."""
        if namespace not in self._subscribers:
            self._subscribers[namespace] = []
        self._subscribers[namespace].append(callback)
        
    def publish(self, namespace: str, event_type: str, memory_id: str, content: str):
        """Publish a memory event to all subscribers of a namespace."""
        if namespace in self._subscribers:
            event = {
                "namespace": namespace,
                "event_type": event_type,
                "memory_id": memory_id,
                "content": content
            }
            for callback in self._subscribers[namespace]:
                try:
                    callback(event)
                except Exception as e:
                    print(f"Error in subscriber callback: {e}")

# Singleton instance
event_bus = MemoryEventBus()
