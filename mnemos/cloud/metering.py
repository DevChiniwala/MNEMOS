from typing import Dict
from datetime import datetime, date
from collections import defaultdict

class UsageMeter:
    """
    Tracks per-tenant usage for billing and rate limiting.
    Meters: memories stored, queries executed, tokens consumed.
    """

    def __init__(self):
        # tenant_id -> metric_name -> daily counts {date_str: count}
        self._usage: Dict[str, Dict[str, Dict[str, int]]] = defaultdict(
            lambda: defaultdict(lambda: defaultdict(int))
        )

    def _today(self) -> str:
        return date.today().isoformat()

    def record(self, tenant_id: str, metric: str, count: int = 1):
        """Record a usage event."""
        self._usage[tenant_id][metric][self._today()] += count

    def get_daily_usage(self, tenant_id: str, metric: str) -> int:
        """Get today's usage for a specific metric."""
        return self._usage[tenant_id][metric].get(self._today(), 0)

    def get_total_usage(self, tenant_id: str, metric: str) -> int:
        """Get all-time usage for a specific metric."""
        return sum(self._usage[tenant_id][metric].values())

    def get_usage_report(self, tenant_id: str) -> dict:
        """Full usage report for a tenant."""
        report = {}
        for metric, daily in self._usage[tenant_id].items():
            report[metric] = {
                "today": daily.get(self._today(), 0),
                "total": sum(daily.values())
            }
        return report

    def check_quota(self, tenant_id: str, metric: str, limit: int) -> bool:
        """Returns True if under quota, False if exceeded."""
        if limit == -1:  # unlimited
            return True
        return self.get_daily_usage(tenant_id, metric) < limit


# Singleton
usage_meter = UsageMeter()
