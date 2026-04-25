"""
Identity Types
==============

Data structures for actor identity, access decisions, and role bindings.

These types represent the server-side identity of an authenticated actor,
the result of permission checks, and the mapping between roles and
permissions.  All types are pure dataclasses with no external dependencies.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, FrozenSet


@dataclass
class ActorContext:
    """Server-side identity of the authenticated actor.

    Represents *who* is performing an action and *what* they are
    authorized to do.  Constructed by the host application's auth
    middleware (WSGI, ASGI, etc.) and passed into Vellum
    operations via context dicts.

    Attributes:
        actor_id: Unique user or system identifier.
        org_id: Tenant or organization the actor belongs to.
        roles: Set of role names assigned to the actor
            (e.g. ``{"ADMIN", "OPERATOR"}``).
        permissions: Resolved permission set derived from roles.
        metadata: Additional context (email, IP, user-agent, etc.).
    """

    actor_id: str
    org_id: str
    roles: FrozenSet[str] = frozenset()
    permissions: FrozenSet[str] = frozenset()
    metadata: Dict[str, Any] = field(default_factory=dict)

    def has_role(self, role: str) -> bool:
        """Check if the actor has a specific role."""
        return role in self.roles

    def has_permission(self, permission: str) -> bool:
        """Check if the actor has a specific permission."""
        return permission in self.permissions

    def has_any_role(self, roles: FrozenSet[str]) -> bool:
        """Check if the actor has any of the given roles."""
        return bool(self.roles & roles)


@dataclass
class AccessDecision:
    """Result of a permission check.

    Returned by ``PermissionPolicy.check()`` to indicate whether
    an action is allowed and why.

    Attributes:
        allowed: Whether the action is permitted.
        actor_id: The actor who requested the action.
        action: The action that was checked.
        resource: The resource the action targets (optional).
        reason: Human-readable explanation for the decision.
    """

    allowed: bool
    actor_id: str
    action: str
    resource: str = ""
    reason: str = ""

    @property
    def denied(self) -> bool:
        """Convenience inverse of ``allowed``."""
        return not self.allowed


@dataclass
class RoleBinding:
    """Maps a role to a set of permissions.

    Used by ``RoleBasedPolicy`` to resolve an actor's roles into
    concrete permissions.

    Attributes:
        role: The role name (e.g. ``"ADMIN"``).
        permissions: Permissions granted by this role.
    """

    role: str
    permissions: FrozenSet[str]

    @classmethod
    def from_set(cls, role: str, permissions: set[str]) -> "RoleBinding":
        """Create a binding from a mutable set."""
        return cls(role=role, permissions=frozenset(permissions))
