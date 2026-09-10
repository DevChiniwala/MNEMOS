import logging
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict


class AuditLogger:
    """
    Compliance audit logger for MNEMOS.
    Tracks all PII redactions, data erasures, and namespace access events.
    """

    def __init__(self, log_file: str = None):
        if log_file is None:
            log_file = os.getenv("MNEMOS_AUDIT_LOG", "mnemos_compliance_audit.log")
        self._log_file = log_file
        self._logger = None

    def _get_logger(self) -> logging.Logger:
        if self._logger is None:
            self._logger = logging.getLogger("mnemos_audit")
            self._logger.setLevel(logging.INFO)
            if not self._logger.handlers:
                handler = logging.FileHandler(self._log_file)
                formatter = logging.Formatter('%(message)s')
                handler.setFormatter(formatter)
                self._logger.addHandler(handler)
        return self._logger

    def _log_event(self, event_type: str, actor: str, target: str, details: Dict[str, Any]):
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "actor": actor,
            "target": target,
            "details": details
        }
        self._get_logger().info(json.dumps(event))

    def log_redaction(self, actor: str, stats: Dict[str, int]):
        self._log_event("PII_REDACTION", actor, "memory_ingestion", {"stats": stats})

    def log_erasure(self, actor: str, target_user_id: str, items_deleted: int):
        self._log_event("DATA_ERASURE", actor, target_user_id, {"items_deleted": items_deleted})

    def log_access(self, actor: str, namespace: str, action: str):
        self._log_event("NAMESPACE_ACCESS", actor, namespace, {"action": action})


audit_logger = AuditLogger()
