"""
State Machine Protocols
=======================

Abstract interface for domain-specific transition validation.

The ``StateMachine`` engine handles structural validation (is this
transition in the config?).  ``TransitionValidator`` implementations
add domain-specific rules (e.g. "only the pledgee can foreclose",
"managers must approve before ACTIVE").
"""

from typing import Any, Dict, Protocol, runtime_checkable

from .types import TransitionResult


@runtime_checkable
class TransitionValidator(Protocol):
    """Domain-specific validation for state transitions.

    Multiple validators can be registered on a ``StateMachine``.
    All must return ``allowed=True`` for the transition to proceed.

    Use this to enforce business rules that go beyond the structural
    transition matrix — access control, prerequisite checks, temporal
    constraints, etc.

    The ``context`` dict carries caller-provided metadata (actor info,
    entity state, etc.).  Vellum does not define its contents — host
    applications do.
    """

    def validate(
        self,
        from_state: str,
        to_state: str,
        context: Dict[str, Any],
    ) -> TransitionResult:
        """Validate whether a specific transition should be allowed.

        Args:
            from_state: Current state of the entity.
            to_state: Requested target state.
            context: Caller-provided metadata (entity data, actor info, etc.).

        Returns:
            ``TransitionResult`` — ``allowed=True`` to permit,
            ``allowed=False`` with ``error`` to block.
        """
        ...
