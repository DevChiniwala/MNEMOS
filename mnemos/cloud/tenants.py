from typing import Optional, Dict, List
from datetime import datetime
from pydantic import BaseModel, Field
import uuid

class Tenant(BaseModel):
    """Represents an organization / customer on MNEMOS Cloud."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    plan: str = "free"  # free | pro | enterprise
    api_key: str = Field(default_factory=lambda: f"mn_{uuid.uuid4().hex}")
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    max_memories: int = 10000
    max_queries_per_day: int = 1000
    is_active: bool = True

class Workspace(BaseModel):
    """A workspace within a tenant (e.g. dev, staging, prod)."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    name: str
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

class TenantManager:
    """
    Multi-tenant isolation layer for MNEMOS Cloud.
    Each tenant gets its own logical partition with strict data boundaries.
    """

    def __init__(self):
        self._tenants: Dict[str, Tenant] = {}
        self._workspaces: Dict[str, Workspace] = {}
        self._api_key_index: Dict[str, str] = {}  # api_key -> tenant_id

    def create_tenant(self, name: str, plan: str = "free") -> Tenant:
        tenant = Tenant(name=name, plan=plan)
        if plan == "pro":
            tenant.max_memories = 100000
            tenant.max_queries_per_day = 10000
        elif plan == "enterprise":
            tenant.max_memories = -1  # unlimited
            tenant.max_queries_per_day = -1
        self._tenants[tenant.id] = tenant
        self._api_key_index[tenant.api_key] = tenant.id
        return tenant

    def get_tenant_by_api_key(self, api_key: str) -> Optional[Tenant]:
        tenant_id = self._api_key_index.get(api_key)
        if tenant_id:
            return self._tenants.get(tenant_id)
        return None

    def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        return self._tenants.get(tenant_id)

    def list_tenants(self) -> List[Tenant]:
        return list(self._tenants.values())

    def create_workspace(self, tenant_id: str, name: str) -> Workspace:
        if tenant_id not in self._tenants:
            raise ValueError("Tenant not found.")
        ws = Workspace(tenant_id=tenant_id, name=name)
        self._workspaces[ws.id] = ws
        return ws

    def get_workspaces(self, tenant_id: str) -> List[Workspace]:
        return [ws for ws in self._workspaces.values() if ws.tenant_id == tenant_id]
