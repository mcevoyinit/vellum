"""
Role-Based Access Control
=========================

Reference ``PermissionPolicy`` implementation using role-to-permission
bindings.  Zero external dependencies.

Usage::

    from vellum.identity import RoleBasedPolicy, RoleBinding, ActorContext

    bindings = [
        RoleBinding(role="ADMIN", permissions=frozenset({"CREATE", "DELETE", "APPROVE"})),
        RoleBinding(role="VIEWER", permissions=frozenset({"READ"})),
    ]

    policy = RoleBasedPolicy(bindings)

    actor = ActorContext(actor_id="user-1", org_id="org-1", roles=frozenset({"ADMIN"}))
    decision = policy.check(actor, action="DELETE")
    assert decision.allowed
"""

from typing import Dict, FrozenSet, List

from .types import AccessDecision, ActorContext, RoleBinding


class RoleBasedPolicy:
    """Simple RBAC: roles → permission sets → action check.

    Resolves the actor's assigned roles into a union of permission
    sets via the configured ``RoleBinding`` list, then checks whether
    the requested action is in that union.

    This is intentionally simple — it handles the 80% case of
    "does this role grant this permission?"  More complex patterns
    (field-level authority, cross-tenant grants, ABAC) belong in
    host application implementations of ``PermissionPolicy``.
    """

    def __init__(self, bindings: List[RoleBinding]) -> None:
        self._role_map: Dict[str, FrozenSet[str]] = {
            b.role: b.permissions for b in bindings
        }

    def check(
        self, actor: ActorContext, action: str, resource: str = ""
    ) -> AccessDecision:
        """Check if the actor's roles grant the requested action.

        Resolves all of the actor's roles into their permission sets,
        takes the union, and checks if ``action`` is present.

        Args:
            actor: The authenticated actor context.
            action: The action being attempted.
            resource: Optional resource identifier (included in the
                decision for audit purposes, not used in evaluation).

        Returns:
            ``AccessDecision`` with ``allowed=True`` if any role
            grants the action, ``allowed=False`` otherwise.
        """
        granted: set[str] = set()
        for role in actor.roles:
            perms = self._role_map.get(role)
            if perms:
                granted |= perms

        if action in granted:
            return AccessDecision(
                allowed=True,
                actor_id=actor.actor_id,
                action=action,
                resource=resource,
                reason=f"Granted by role(s): {self._granting_roles(actor.roles, action)}",
            )

        return AccessDecision(
            allowed=False,
            actor_id=actor.actor_id,
            action=action,
            resource=resource,
            reason=f"No role grants '{action}'",
        )

    def resolve_permissions(self, roles: FrozenSet[str]) -> FrozenSet[str]:
        """Resolve a set of roles into their combined permissions.

        Args:
            roles: Set of role names to resolve.

        Returns:
            Union of all permissions granted by the given roles.
        """
        result: set[str] = set()
        for role in roles:
            perms = self._role_map.get(role)
            if perms:
                result |= perms
        return frozenset(result)

    def _granting_roles(self, roles: FrozenSet[str], action: str) -> str:
        """Identify which roles grant a specific action."""
        granting = sorted(
            r for r in roles
            if r in self._role_map and action in self._role_map[r]
        )
        return ", ".join(granting)
