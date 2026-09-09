from mnemos.schemas.advanced_memory import AdvancedMemoryStore
from mnemos.privacy.audit import audit_logger


class ErasureEngine:
    """
    Handles GDPR 'Right to Erasure' requests (Article 17).
    Purges all traces of a user's data from the memory store.
    """

    def __init__(self, memory_store: AdvancedMemoryStore):
        self.memory_store = memory_store

    def erase_user_data(self, requestor_id: str, target_user_id: str) -> int:
        """
        Hard deletes all memories tagged with target_user_id.
        Returns the number of deleted records.
        """
        deleted_count = 0
        entries = self.memory_store.get_entries(include_inactive=True)
        target_ids = [
            e.id for e in entries
            if e.meta.get("user_id") == target_user_id
        ]

        for entry_id in target_ids:
            self.memory_store.delete_entry(entry_id)
            deleted_count += 1

        audit_logger.log_erasure(
            actor=requestor_id,
            target_user_id=target_user_id,
            items_deleted=deleted_count,
        )

        return deleted_count
