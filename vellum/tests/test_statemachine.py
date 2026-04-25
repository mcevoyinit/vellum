"""
Tests for vellum.statemachine
=============================

Generic finite state machine: configuration, transitions, terminal states,
validators, and protocol conformance.
"""

from typing import Any, Dict

import pytest

from vellum.statemachine import (
    StateMachine,
    StateMachineConfig,
    TransitionResult,
    TransitionValidator,
)


# ======================================================================
# Fixtures
# ======================================================================


def make_workflow_config() -> StateMachineConfig:
    """Standard 4-state workflow for testing."""
    return StateMachineConfig.from_dict(
        states={"DRAFT", "REVIEW", "APPROVED", "REJECTED"},
        transitions={
            "DRAFT": {"REVIEW"},
            "REVIEW": {"APPROVED", "REJECTED"},
            "REJECTED": {"DRAFT"},
        },
        initial_states={"DRAFT"},
        terminal_states={"APPROVED"},
    )


def make_linear_config() -> StateMachineConfig:
    """Simple linear A -> B -> C with C terminal."""
    return StateMachineConfig.from_dict(
        states={"A", "B", "C"},
        transitions={"A": {"B"}, "B": {"C"}},
        initial_states={"A"},
        terminal_states={"C"},
    )


# ======================================================================
# Test doubles
# ======================================================================


class BlockingValidator:
    """Validator that always blocks transitions."""

    def __init__(self, reason: str = "Blocked by validator") -> None:
        self._reason = reason

    def validate(
        self, from_state: str, to_state: str, context: Dict[str, Any]
    ) -> TransitionResult:
        return TransitionResult(
            allowed=False,
            from_state=from_state,
            to_state=to_state,
            error=self._reason,
        )


class PassingValidator:
    """Validator that always allows transitions."""

    def validate(
        self, from_state: str, to_state: str, context: Dict[str, Any]
    ) -> TransitionResult:
        return TransitionResult(
            allowed=True,
            from_state=from_state,
            to_state=to_state,
        )


class ContextCheckingValidator:
    """Validator that checks for a required context key."""

    def __init__(self, required_key: str) -> None:
        self._required_key = required_key

    def validate(
        self, from_state: str, to_state: str, context: Dict[str, Any]
    ) -> TransitionResult:
        if self._required_key not in context:
            return TransitionResult(
                allowed=False,
                from_state=from_state,
                to_state=to_state,
                error=f"Missing required context: {self._required_key}",
            )
        return TransitionResult(
            allowed=True,
            from_state=from_state,
            to_state=to_state,
        )


# ======================================================================
# Protocol conformance
# ======================================================================


class TestProtocolConformance:

    def test_blocking_validator_is_transition_validator(self) -> None:
        assert isinstance(BlockingValidator(), TransitionValidator)

    def test_passing_validator_is_transition_validator(self) -> None:
        assert isinstance(PassingValidator(), TransitionValidator)

    def test_context_validator_is_transition_validator(self) -> None:
        assert isinstance(ContextCheckingValidator("key"), TransitionValidator)


# ======================================================================
# StateMachineConfig
# ======================================================================


class TestStateMachineConfig:

    def test_from_dict_converts_to_frozensets(self) -> None:
        config = StateMachineConfig.from_dict(
            states={"A", "B"},
            transitions={"A": {"B"}},
        )
        assert isinstance(config.states, frozenset)
        assert isinstance(config.transitions["A"], frozenset)

    def test_from_dict_defaults(self) -> None:
        config = StateMachineConfig.from_dict(
            states={"A", "B"},
            transitions={"A": {"B"}},
        )
        assert config.initial_states == frozenset()
        assert config.terminal_states == frozenset()

    def test_from_dict_with_initial_and_terminal(self) -> None:
        config = make_workflow_config()
        assert "DRAFT" in config.initial_states
        assert "APPROVED" in config.terminal_states


# ======================================================================
# StateMachine — valid transitions
# ======================================================================


class TestValidTransitions:

    def test_allowed_transition(self) -> None:
        sm = StateMachine(make_workflow_config())
        result = sm.can_transition("DRAFT", "REVIEW")
        assert result.allowed
        assert result.from_state == "DRAFT"
        assert result.to_state == "REVIEW"

    def test_allowed_transition_success_property(self) -> None:
        sm = StateMachine(make_workflow_config())
        result = sm.can_transition("DRAFT", "REVIEW")
        assert result.success  # Alias

    def test_multi_target_transition(self) -> None:
        sm = StateMachine(make_workflow_config())
        r1 = sm.can_transition("REVIEW", "APPROVED")
        r2 = sm.can_transition("REVIEW", "REJECTED")
        assert r1.allowed
        assert r2.allowed

    def test_cycle_transition(self) -> None:
        sm = StateMachine(make_workflow_config())
        result = sm.can_transition("REJECTED", "DRAFT")
        assert result.allowed

    def test_linear_transitions(self) -> None:
        sm = StateMachine(make_linear_config())
        assert sm.can_transition("A", "B").allowed
        assert sm.can_transition("B", "C").allowed


# ======================================================================
# StateMachine — blocked transitions
# ======================================================================


class TestBlockedTransitions:

    def test_invalid_transition(self) -> None:
        sm = StateMachine(make_workflow_config())
        result = sm.can_transition("DRAFT", "APPROVED")
        assert not result.allowed
        assert "Invalid transition" in (result.error or "")

    def test_unknown_from_state(self) -> None:
        sm = StateMachine(make_workflow_config())
        result = sm.can_transition("NONEXISTENT", "REVIEW")
        assert not result.allowed
        assert "Unknown state: NONEXISTENT" in (result.error or "")

    def test_unknown_to_state(self) -> None:
        sm = StateMachine(make_workflow_config())
        result = sm.can_transition("DRAFT", "NONEXISTENT")
        assert not result.allowed
        assert "Unknown state: NONEXISTENT" in (result.error or "")

    def test_terminal_state_blocks_transition(self) -> None:
        sm = StateMachine(make_workflow_config())
        result = sm.can_transition("APPROVED", "DRAFT")
        assert not result.allowed
        assert "terminal state" in (result.error or "")

    def test_reverse_not_allowed(self) -> None:
        sm = StateMachine(make_linear_config())
        result = sm.can_transition("B", "A")
        assert not result.allowed

    def test_self_transition_not_configured(self) -> None:
        sm = StateMachine(make_workflow_config())
        result = sm.can_transition("DRAFT", "DRAFT")
        assert not result.allowed


# ======================================================================
# StateMachine — validators
# ======================================================================


class TestValidators:

    def test_passing_validator_allows(self) -> None:
        sm = StateMachine(make_workflow_config(), validators=[PassingValidator()])
        result = sm.can_transition("DRAFT", "REVIEW")
        assert result.allowed

    def test_blocking_validator_blocks(self) -> None:
        sm = StateMachine(
            make_workflow_config(),
            validators=[BlockingValidator("Access denied")],
        )
        result = sm.can_transition("DRAFT", "REVIEW")
        assert not result.allowed
        assert result.error == "Access denied"

    def test_multiple_validators_all_must_pass(self) -> None:
        sm = StateMachine(
            make_workflow_config(),
            validators=[PassingValidator(), BlockingValidator("Nope")],
        )
        result = sm.can_transition("DRAFT", "REVIEW")
        assert not result.allowed
        assert result.error == "Nope"

    def test_validator_short_circuits(self) -> None:
        """First failing validator stops the chain."""
        sm = StateMachine(
            make_workflow_config(),
            validators=[
                BlockingValidator("First blocker"),
                BlockingValidator("Second blocker"),
            ],
        )
        result = sm.can_transition("DRAFT", "REVIEW")
        assert result.error == "First blocker"

    def test_context_forwarded_to_validator(self) -> None:
        sm = StateMachine(
            make_workflow_config(),
            validators=[ContextCheckingValidator("actor_id")],
        )
        # Without context key
        r1 = sm.can_transition("DRAFT", "REVIEW")
        assert not r1.allowed
        assert "actor_id" in (r1.error or "")

        # With context key
        r2 = sm.can_transition("DRAFT", "REVIEW", context={"actor_id": "user-1"})
        assert r2.allowed

    def test_validators_not_called_for_structural_failures(self) -> None:
        """Validators only run if the transition is structurally valid."""
        blocker = BlockingValidator("Should not reach")
        sm = StateMachine(make_workflow_config(), validators=[blocker])
        result = sm.can_transition("DRAFT", "APPROVED")
        # Blocked by config, not by validator
        assert "Invalid transition" in (result.error or "")


# ======================================================================
# StateMachine — query methods
# ======================================================================


class TestQueryMethods:

    def test_get_valid_transitions(self) -> None:
        sm = StateMachine(make_workflow_config())
        targets = sm.get_valid_transitions("REVIEW")
        assert targets == ["APPROVED", "REJECTED"]

    def test_get_valid_transitions_terminal(self) -> None:
        sm = StateMachine(make_workflow_config())
        assert sm.get_valid_transitions("APPROVED") == []

    def test_get_valid_transitions_unknown(self) -> None:
        sm = StateMachine(make_workflow_config())
        assert sm.get_valid_transitions("NONEXISTENT") == []

    def test_get_valid_transitions_no_outbound(self) -> None:
        """State exists but has no configured transitions (implicit terminal)."""
        config = StateMachineConfig.from_dict(
            states={"A", "B"},
            transitions={"A": {"B"}},
        )
        sm = StateMachine(config)
        assert sm.get_valid_transitions("B") == []

    def test_is_terminal(self) -> None:
        sm = StateMachine(make_workflow_config())
        assert sm.is_terminal("APPROVED")
        assert not sm.is_terminal("DRAFT")

    def test_is_initial(self) -> None:
        sm = StateMachine(make_workflow_config())
        assert sm.is_initial("DRAFT")
        assert not sm.is_initial("REVIEW")

    def test_list_states(self) -> None:
        sm = StateMachine(make_workflow_config())
        states = sm.list_states()
        assert states == ["APPROVED", "DRAFT", "REJECTED", "REVIEW"]

    def test_config_property(self) -> None:
        config = make_workflow_config()
        sm = StateMachine(config)
        assert sm.config is config


# ======================================================================
# TransitionResult
# ======================================================================


class TestTransitionResult:

    def test_success_alias(self) -> None:
        r = TransitionResult(allowed=True, from_state="A", to_state="B")
        assert r.success is True

    def test_success_alias_false(self) -> None:
        r = TransitionResult(allowed=False, from_state="A", to_state="B", error="No")
        assert r.success is False

    def test_error_default_none(self) -> None:
        r = TransitionResult(allowed=True, from_state="A", to_state="B")
        assert r.error is None
