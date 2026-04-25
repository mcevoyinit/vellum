"""
Identity Protocols
==================

Abstract interfaces for actor resolution and permission checking.

``ActorResolver`` implementations extract identity from framework-specific
request contexts (WSGI ``g``, ASGI dependencies, etc.).

``PermissionPolicy`` implementations decide whether an actor can perform
a given action.  Vellum ships ``RoleBasedPolicy`` as a reference
implementation; host applications can provide ABAC, ReBAC, or any
other policy engine.
"""

from typing import Any, Dict, Protocol, runtime_checkable

from .types import AccessDecision, ActorContext


@runtime_checkable
class ActorResolver(Protocol):
    """Extracts ``ActorContext`` from a request context.

    Implementations bridge the gap between framework-specific request
    state (WSGI ``g``, ASGI ``Depends``, raw headers) and the
    framework-agnostic ``ActorContext`` that Vellum operations consume.

    The contract:
        - ``resolve`` must return a fully populated ``ActorContext``.
        - If the context is missing required fields, raise or return
          an ``ActorContext`` with empty roles/permissions.
    """

    def resolve(self, context: Dict[str, Any]) -> ActorContext:
        """Extract actor identity from a request context dict.

        Args:
            context: Framework-specific request state.  Typically
                includes auth tokens, tenant IDs, and user metadata.

        Returns:
            Populated ``ActorContext`` for the current request.
        """
        ...


@runtime_checkable
class PermissionPolicy(Protocol):
    """Decides whether an actor can perform an action on a resource.

    Implementations encode authorization logic — RBAC, ABAC, ReBAC,
    or custom business rules.  The ``check`` method returns an
    ``AccessDecision`` with the verdict and reasoning.

    The contract:
        - ``check`` must be **pure** — no side effects.
        - ``check`` must always return an ``AccessDecision``, never raise.
    """

    def check(
        self, actor: ActorContext, action: str, resource: str = ""
    ) -> AccessDecision:
        """Evaluate whether the actor may perform the action.

        Args:
            actor: The authenticated actor context.
            action: The action being attempted (e.g. ``"CREATE"``,
                ``"APPROVE"``, ``"DELETE"``).
            resource: Optional resource identifier the action targets.

        Returns:
            ``AccessDecision`` indicating whether the action is allowed.
        """
        ...
