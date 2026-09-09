import logging
import json
from datetime import datetime
from typing import Any, Dict

class AuditLogger:
    """
    Compliance audit logger for MNEMOS.
    Tracks all PII redactions, data erasures, and namespace access events.
    """
    
    def __init__(self, log_file: str = "mnemos_compliance_audit.log"):
        self.logger = logging.getLogger("mnemos_audit")
        self.logger.setLevel(logging.INFO)
        
        # Prevent adding duplicate handlers if instantiated multiple times
        if not self.logger.handlers:
            handler = logging.FileHandler(log_file)
            formatter = logging.Formatter('%(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def _log_event(self, event_type: str, actor: str, target: str, details: Dict[str, Any]):
        event = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event_type": event_type,
            "actor": actor,
            "target": target,
            "details": details
        }
        self.logger.info(json.dumps(event))

    def log_redaction(self, actor: str, stats: Dict[str, int]):
        """Log when PII is redacted during memory ingestion."""
        self._log_event("PII_REDACTION", actor, "memory_ingestion", {"stats": stats})

    def log_erasure(self, actor: str, target_user_id: str, items_deleted: int):
        """Log a GDPR Article 17 erasure request execution."""
        self._log_event("DATA_ERASURE", actor, target_user_id, {"items_deleted": items_deleted})

    def log_access(self, actor: str, namespace: str, action: str):
        """Log access control decisions (e.g. reading/writing to a shared agent namespace)."""
        self._log_event("NAMESPACE_ACCESS", actor, namespace, {"action": action})

# Singleton instance
audit_logger = AuditLogger()
