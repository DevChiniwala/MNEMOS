from typing import List
from mnemos.schemas.advanced_memory import AdvancedMemoryStore
from mnemos.privacy.audit import audit_logger

class ErasureEngine:
    """
    Handles GDPR 'Right to Erasure' requests (Article 17).
    Ensures all traces of a user's data are permanently purged from the memory store.
    """
    
    def __init__(self, memory_store: AdvancedMemoryStore):
        self.memory_store = memory_store
        
    def erase_user_data(self, requestor_id: str, target_user_id: str) -> int:
        """
        Hard deletes all memories, history, and associated pages for a specific user.
        Returns the number of deleted records.
        """
        # Note: A real implementation would also reach into PageStore, ProfileStore, etc.
        # This implementation specifically purges AdvancedMemoryStore.
        
        deleted_count = 0
        
        # We must lock the store while performing mass deletion
        with self.memory_store.lock:
            # Gather all IDs matching the target user_id
            target_ids = []
            for mem_id, history in self.memory_store.history.items():
                if not history:
                    continue
                # If any version of the memory was tagged with this user_id
                # Assuming user_id is stored in meta
                # We also check the active store
                entry = self.memory_store.store.get(mem_id)
                if entry and entry.meta.get("user_id") == target_user_id:
                    target_ids.append(mem_id)
                elif history[-1].meta.get("user_id") == target_user_id:
                    target_ids.append(mem_id)
            
            # Perform hard deletion (bypassing soft-delete lifecycle)
            for mem_id in target_ids:
                if mem_id in self.memory_store.store:
                    del self.memory_store.store[mem_id]
                if mem_id in self.memory_store.history:
                    del self.memory_store.history[mem_id]
                deleted_count += 1
                
            self.memory_store._persist()
            
        audit_logger.log_erasure(actor=requestor_id, target_user_id=target_user_id, items_deleted=deleted_count)
        
        return deleted_count
