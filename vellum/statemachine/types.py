"""
State Machine Types
===================

Data structures for finite state machine configuration and transition results.

All types are pure dataclasses with no external dependencies.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, FrozenSet, Optional, Set, Union


@dataclass
class TransitionResult:
    """Result of a state transition attempt.

    Attributes:
        allowed: Whether the transition is permitted.
        from_state: The source state.
        to_state: The target state.
        error: Human-readable reason if the transition was blocked.
    """

    allowed: bool
    from_state: str
    to_state: str
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        """Alias for ``allowed``."""
        return self.allowed


@dataclass
class StateMachineConfig:
    """Declarative configuration for a finite state machine.

    Define your states and valid transitions as data — no subclassing
    required.  Pass this to a ``StateMachine`` engine.

    Attributes:
        states: All valid state names.
        transitions: Map of ``state -> {valid target states}``.
        initial_states: States that a new entity can start in.
        terminal_states: States from which no further transitions
            are allowed.

    Example::

        config = StateMachineConfig(
            states=frozenset({"DRAFT", "ACTIVE", "CLOSED"}),
            transitions={
                "DRAFT": frozenset({"ACTIVE", "CLOSED"}),
                "ACTIVE": frozenset({"CLOSED"}),
            },
            initial_states=frozenset({"DRAFT"}),
            terminal_states=frozenset({"CLOSED"}),
        )
    """

    states: FrozenSet[str]
    transitions: Dict[str, FrozenSet[str]]
    initial_states: FrozenSet[str] = field(default_factory=frozenset)
    terminal_states: FrozenSet[str] = field(default_factory=frozenset)

    @staticmethod
    def from_dict(
        states: Union[Set[str], FrozenSet[str]],
        transitions: Dict[str, Union[Set[str], FrozenSet[str]]],
        initial_states: Union[Set[str], FrozenSet[str], None] = None,
        terminal_states: Union[Set[str], FrozenSet[str], None] = None,
    ) -> "StateMachineConfig":
        """Convenience constructor accepting plain sets.

        Converts mutable sets to frozensets for immutability.
        """
        return StateMachineConfig(
            states=frozenset(states),
            transitions={k: frozenset(v) for k, v in transitions.items()},
            initial_states=frozenset(initial_states or set()),
            terminal_states=frozenset(terminal_states or set()),
        )
