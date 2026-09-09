from enum import Enum
from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from mnemos.privacy.audit import audit_logger

class AccessLevel(Enum):
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"

class Permission(BaseModel):
    accessor_id: str
    level: AccessLevel

class Namespace(BaseModel):
    name: str = Field(..., description="Unique namespace identifier (e.g., 'team:alpha')")
    owner_id: str = Field(..., description="The user/agent who owns this namespace")
    permissions: List[Permission] = Field(default_factory=list)
    
    def can_access(self, actor_id: str, required_level: AccessLevel) -> bool:
        if actor_id == self.owner_id:
            return True
            
        # Admin implies all
        # Write implies read + write
        # Read implies read
        level_values = {AccessLevel.READ: 1, AccessLevel.WRITE: 2, AccessLevel.ADMIN: 3}
        required_val = level_values[required_level]
        
        for perm in self.permissions:
            if perm.accessor_id == actor_id:
                if level_values[perm.level] >= required_val:
                    return True
                    
        return False

class NamespaceManager:
    """
    Manages isolated memory namespaces for multi-agent shared context.
    """
    
    def __init__(self):
        self._namespaces: Dict[str, Namespace] = {}
        
    def create_namespace(self, name: str, owner_id: str) -> Namespace:
        if name in self._namespaces:
            raise ValueError(f"Namespace {name} already exists.")
        ns = Namespace(name=name, owner_id=owner_id)
        self._namespaces[name] = ns
        return ns
        
    def grant_access(self, admin_id: str, namespace_name: str, target_id: str, level: AccessLevel):
        ns = self._namespaces.get(namespace_name)
        if not ns:
            raise ValueError("Namespace not found.")
            
        if not ns.can_access(admin_id, AccessLevel.ADMIN):
            audit_logger.log_access(admin_id, namespace_name, "DENIED_GRANT")
            raise PermissionError("Admin access required to grant permissions.")
            
        # Remove existing perm if present
        ns.permissions = [p for p in ns.permissions if p.accessor_id != target_id]
        ns.permissions.append(Permission(accessor_id=target_id, level=level))
        audit_logger.log_access(admin_id, namespace_name, f"GRANTED_{level.value.upper()}_TO_{target_id}")

    def assert_access(self, actor_id: str, namespace_name: str, level: AccessLevel):
        """Raises PermissionError if access is denied."""
        ns = self._namespaces.get(namespace_name)
        if not ns:
            # For simplicity in this implementation, if a namespace doesn't exist, we auto-create it
            # assuming the first person to use it owns it. In production, this should be explicitly managed.
            ns = self.create_namespace(namespace_name, actor_id)
            
        if not ns.can_access(actor_id, level):
            audit_logger.log_access(actor_id, namespace_name, f"DENIED_{level.value.upper()}")
            raise PermissionError(f"Actor {actor_id} does not have {level.value} access to {namespace_name}.")
            
        audit_logger.log_access(actor_id, namespace_name, f"ALLOWED_{level.value.upper()}")
