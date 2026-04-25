"""
Vellum State Machine
====================

Config-driven finite state machine with pluggable transition validators.

Define states and valid transitions declaratively.  Add domain-specific
rules (access control, prerequisite checks) via ``TransitionValidator``
implementations.

Quickstart::

    from vellum.statemachine import StateMachine, StateMachineConfig

    config = StateMachineConfig.from_dict(
        states={"DRAFT", "REVIEW", "APPROVED", "REJECTED"},
        transitions={
            "DRAFT": {"REVIEW"},
            "REVIEW": {"APPROVED", "REJECTED"},
            "REJECTED": {"DRAFT"},
        },
        initial_states={"DRAFT"},
        terminal_states={"APPROVED"},
    )

    sm = StateMachine(config)
    result = sm.can_transition("DRAFT", "REVIEW")
    assert result.allowed

Protocol:

- ``TransitionValidator`` — domain-specific transition validation
"""

# Engine
from .engine import StateMachine

# Protocol
from .protocols import TransitionValidator

# Types
from .types import StateMachineConfig, TransitionResult

__all__ = [
    # Engine
    "StateMachine",
    # Protocol
    "TransitionValidator",
    # Types
    "StateMachineConfig",
    "TransitionResult",
]
