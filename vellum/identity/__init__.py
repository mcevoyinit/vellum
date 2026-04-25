"""
Vellum Identity
===============

Actor identity, role-based access control, and permission checking.

Provides a framework-agnostic representation of *who* is acting and
*what* they are allowed to do.  Host applications implement
``ActorResolver`` to bridge their auth middleware; ``PermissionPolicy``
implementations encode authorization logic.

Quickstart::

    from vellum.identity import RoleBasedPolicy, RoleBinding, ActorContext

    bindings = [
        RoleBinding(role="ADMIN", permissions=frozenset({"CREATE", "DELETE"})),
        RoleBinding(role="VIEWER", permissions=frozenset({"READ"})),
    ]

    policy = RoleBasedPolicy(bindings)
    actor = ActorContext(actor_id="u-1", org_id="o-1", roles=frozenset({"ADMIN"}))

    decision = policy.check(actor, action="DELETE")
    assert decision.allowed

Protocols:

- ``ActorResolver`` — extract actor identity from request context
- ``PermissionPolicy`` — authorize actions against a policy
"""

# Protocols
from .protocols import ActorResolver, PermissionPolicy

# Reference implementation
from .rbac import RoleBasedPolicy

# Types
from .types import AccessDecision, ActorContext, RoleBinding

__all__ = [
    # Protocols
    "ActorResolver",
    "PermissionPolicy",
    # Reference implementation
    "RoleBasedPolicy",
    # Types
    "AccessDecision",
    "ActorContext",
    "RoleBinding",
]
