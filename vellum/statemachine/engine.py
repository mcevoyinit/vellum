"""
State Machine Engine
====================

Config-driven finite state machine with pluggable transition validators.

No external dependencies.  Define states and transitions declaratively
via ``StateMachineConfig``, then add domain-specific rules via
``TransitionValidator`` implementations.

Usage::

    from vellum.statemachine import StateMachine, StateMachineConfig

    config = StateMachineConfig.from_dict(
        states={"DRAFT", "ACTIVE", "CLOSED"},
        transitions={
            "DRAFT": {"ACTIVE", "CLOSED"},
            "ACTIVE": {"CLOSED"},
        },
        terminal_states={"CLOSED"},
    )

    sm = StateMachine(config)
    result = sm.can_transition("DRAFT", "ACTIVE")
    assert result.allowed
"""

from typing import Any, Dict, List, Optional

from .protocols import TransitionValidator
from .types import StateMachineConfig, TransitionResult


class StateMachine:
    """Generic finite state machine engine.

    Validates transitions against a declarative configuration and
    optional domain-specific validators.  Contains no I/O and no
    domain knowledge.

    Resolution order:
        1. Check ``from_state`` is a known state.
        2. Check ``to_state`` is a known state.
        3. Check ``from_state`` is not terminal.
        4. Check the transition is in the config matrix.
        5. Run all registered ``TransitionValidator`` instances.

    Args:
        config: Declarative state machine configuration.
        validators: Optional domain-specific validators.  All must
            pass for a transition to be allowed.
    """

    def __init__(
        self,
        config: StateMachineConfig,
        validators: Optional[List[TransitionValidator]] = None,
    ) -> None:
        self._config = config
        self._validators = validators or []

    @property
    def config(self) -> StateMachineConfig:
        """The state machine configuration."""
        return self._config

    def can_transition(
        self,
        from_state: str,
        to_state: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> TransitionResult:
        """Check whether a transition is allowed.

        Runs structural checks first, then domain validators.

        Args:
            from_state: Current state.
            to_state: Requested target state.
            context: Caller-provided metadata forwarded to validators.

        Returns:
            ``TransitionResult`` indicating whether the transition
            is allowed.
        """
        ctx = context or {}

        # Check: from_state is known
        if from_state not in self._config.states:
            return TransitionResult(
                allowed=False,
                from_state=from_state,
                to_state=to_state,
                error=f"Unknown state: {from_state}",
            )

        # Check: to_state is known
        if to_state not in self._config.states:
            return TransitionResult(
                allowed=False,
                from_state=from_state,
                to_state=to_state,
                error=f"Unknown state: {to_state}",
            )

        # Check: not transitioning from a terminal state
        if from_state in self._config.terminal_states:
            return TransitionResult(
                allowed=False,
                from_state=from_state,
                to_state=to_state,
                error=f"Cannot transition from terminal state: {from_state}",
            )

        # Check: transition is in the config matrix
        valid_targets = self._config.transitions.get(from_state, frozenset())
        if to_state not in valid_targets:
            return TransitionResult(
                allowed=False,
                from_state=from_state,
                to_state=to_state,
                error=(
                    f"Invalid transition: {from_state} -> {to_state}. "
                    f"Valid targets: {sorted(valid_targets)}"
                ),
            )

        # Check: all domain validators pass
        for validator in self._validators:
            result = validator.validate(from_state, to_state, ctx)
            if not result.allowed:
                return result

        return TransitionResult(
            allowed=True,
            from_state=from_state,
            to_state=to_state,
        )

    def get_valid_transitions(self, from_state: str) -> List[str]:
        """Return all structurally valid target states from ``from_state``.

        Does NOT run domain validators — this returns the full set of
        *possible* transitions.  Use ``can_transition`` to check whether
        a specific transition is actually allowed for a given context.

        Args:
            from_state: Current state.

        Returns:
            Sorted list of valid target state names.
            Empty list if ``from_state`` is unknown or terminal.
        """
        if from_state not in self._config.states:
            return []
        if from_state in self._config.terminal_states:
            return []
        return sorted(self._config.transitions.get(from_state, frozenset()))

    def is_terminal(self, state: str) -> bool:
        """Check whether a state is terminal (no outbound transitions).

        Args:
            state: State to check.

        Returns:
            ``True`` if the state is in the terminal set.
        """
        return state in self._config.terminal_states

    def is_initial(self, state: str) -> bool:
        """Check whether a state is a valid initial state.

        Args:
            state: State to check.

        Returns:
            ``True`` if the state is in the initial set.
        """
        return state in self._config.initial_states

    def list_states(self) -> List[str]:
        """Return all state names, sorted."""
        return sorted(self._config.states)
