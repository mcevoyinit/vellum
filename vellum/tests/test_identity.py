"""
Tests for vellum.identity
==========================

Actor identity, role-based access control, and permission checking.
Protocol conformance, RBAC logic, and ActorContext utilities.
"""

from typing import Any, Dict

import pytest

from vellum.identity import (
    AccessDecision,
    ActorContext,
    ActorResolver,
    PermissionPolicy,
    RoleBasedPolicy,
    RoleBinding,
)


# ======================================================================
# Test doubles
# ======================================================================


class StubActorResolver:
    """Minimal ActorResolver for protocol conformance testing."""

    def resolve(self, context: Dict[str, Any]) -> ActorContext:
        return ActorContext(
            actor_id=context.get("user_id", "unknown"),
            org_id=context.get("org_id", ""),
            roles=frozenset(context.get("roles", [])),
        )


class AlwaysDenyPolicy:
    """PermissionPolicy that always denies."""

    def check(
        self, actor: ActorContext, action: str, resource: str = ""
    ) -> AccessDecision:
        return AccessDecision(
            allowed=False,
            actor_id=actor.actor_id,
            action=action,
            resource=resource,
            reason="Always denied",
        )


# ======================================================================
# Fixtures
# ======================================================================


def make_bindings() -> list[RoleBinding]:
    """Standard role bindings for testing."""
    return [
        RoleBinding(role="ADMIN", permissions=frozenset({"CREATE", "READ", "UPDATE", "DELETE", "APPROVE"})),
        RoleBinding(role="OPERATOR", permissions=frozenset({"CREATE", "READ", "UPDATE"})),
        RoleBinding(role="VIEWER", permissions=frozenset({"READ"})),
    ]


def make_admin() -> ActorContext:
    return ActorContext(actor_id="u-1", org_id="o-1", roles=frozenset({"ADMIN"}))


def make_operator() -> ActorContext:
    return ActorContext(actor_id="u-2", org_id="o-1", roles=frozenset({"OPERATOR"}))


def make_viewer() -> ActorContext:
    return ActorContext(actor_id="u-3", org_id="o-1", roles=frozenset({"VIEWER"}))


# ======================================================================
# Protocol conformance
# ======================================================================


class TestProtocolConformance:

    def test_stub_resolver_is_actor_resolver(self) -> None:
        assert isinstance(StubActorResolver(), ActorResolver)

    def test_role_based_policy_is_permission_policy(self) -> None:
        assert isinstance(RoleBasedPolicy(make_bindings()), PermissionPolicy)

    def test_always_deny_is_permission_policy(self) -> None:
        assert isinstance(AlwaysDenyPolicy(), PermissionPolicy)


# ======================================================================
# ActorContext
# ======================================================================


class TestActorContext:

    def test_has_role(self) -> None:
        actor = make_admin()
        assert actor.has_role("ADMIN")
        assert not actor.has_role("VIEWER")

    def test_has_permission(self) -> None:
        actor = ActorContext(
            actor_id="u-1", org_id="o-1",
            permissions=frozenset({"READ", "WRITE"}),
        )
        assert actor.has_permission("READ")
        assert not actor.has_permission("DELETE")

    def test_has_any_role(self) -> None:
        actor = ActorContext(
            actor_id="u-1", org_id="o-1",
            roles=frozenset({"OPERATOR", "VIEWER"}),
        )
        assert actor.has_any_role(frozenset({"ADMIN", "OPERATOR"}))
        assert not actor.has_any_role(frozenset({"ADMIN"}))

    def test_metadata(self) -> None:
        actor = ActorContext(
            actor_id="u-1", org_id="o-1",
            metadata={"email": "user@example.com", "ip": "10.0.0.1"},
        )
        assert actor.metadata["email"] == "user@example.com"

    def test_default_roles_empty(self) -> None:
        actor = ActorContext(actor_id="u-1", org_id="o-1")
        assert actor.roles == frozenset()
        assert actor.permissions == frozenset()


# ======================================================================
# AccessDecision
# ======================================================================


class TestAccessDecision:

    def test_allowed(self) -> None:
        d = AccessDecision(allowed=True, actor_id="u-1", action="READ")
        assert d.allowed
        assert not d.denied

    def test_denied(self) -> None:
        d = AccessDecision(allowed=False, actor_id="u-1", action="DELETE", reason="No role")
        assert d.denied
        assert not d.allowed
        assert d.reason == "No role"

    def test_resource_included(self) -> None:
        d = AccessDecision(allowed=True, actor_id="u-1", action="READ", resource="INV-001")
        assert d.resource == "INV-001"


# ======================================================================
# RoleBinding
# ======================================================================


class TestRoleBinding:

    def test_from_set(self) -> None:
        binding = RoleBinding.from_set("ADMIN", {"CREATE", "DELETE"})
        assert binding.role == "ADMIN"
        assert isinstance(binding.permissions, frozenset)
        assert "CREATE" in binding.permissions


# ======================================================================
# RoleBasedPolicy
# ======================================================================


class TestRoleBasedPolicy:

    def test_admin_can_delete(self) -> None:
        policy = RoleBasedPolicy(make_bindings())
        decision = policy.check(make_admin(), "DELETE")
        assert decision.allowed
        assert "ADMIN" in decision.reason

    def test_operator_cannot_delete(self) -> None:
        policy = RoleBasedPolicy(make_bindings())
        decision = policy.check(make_operator(), "DELETE")
        assert not decision.allowed
        assert "No role grants" in decision.reason

    def test_viewer_can_read(self) -> None:
        policy = RoleBasedPolicy(make_bindings())
        decision = policy.check(make_viewer(), "READ")
        assert decision.allowed

    def test_viewer_cannot_create(self) -> None:
        policy = RoleBasedPolicy(make_bindings())
        decision = policy.check(make_viewer(), "CREATE")
        assert not decision.allowed

    def test_multi_role_union(self) -> None:
        """Actor with multiple roles gets union of permissions."""
        actor = ActorContext(
            actor_id="u-4", org_id="o-1",
            roles=frozenset({"OPERATOR", "VIEWER"}),
        )
        policy = RoleBasedPolicy(make_bindings())
        # OPERATOR can CREATE, VIEWER cannot — union means allowed
        assert policy.check(actor, "CREATE").allowed
        # Neither can APPROVE — still denied
        assert not policy.check(actor, "APPROVE").allowed

    def test_unknown_role_ignored(self) -> None:
        actor = ActorContext(
            actor_id="u-5", org_id="o-1",
            roles=frozenset({"NONEXISTENT"}),
        )
        policy = RoleBasedPolicy(make_bindings())
        decision = policy.check(actor, "READ")
        assert not decision.allowed

    def test_no_roles_denied(self) -> None:
        actor = ActorContext(actor_id="u-6", org_id="o-1")
        policy = RoleBasedPolicy(make_bindings())
        assert not policy.check(actor, "READ").allowed

    def test_resource_passed_through(self) -> None:
        policy = RoleBasedPolicy(make_bindings())
        decision = policy.check(make_admin(), "READ", resource="INV-001")
        assert decision.resource == "INV-001"

    def test_resolve_permissions(self) -> None:
        policy = RoleBasedPolicy(make_bindings())
        perms = policy.resolve_permissions(frozenset({"ADMIN"}))
        assert "DELETE" in perms
        assert "APPROVE" in perms

    def test_resolve_permissions_multi_role(self) -> None:
        policy = RoleBasedPolicy(make_bindings())
        perms = policy.resolve_permissions(frozenset({"OPERATOR", "VIEWER"}))
        assert "CREATE" in perms
        assert "READ" in perms
        assert "DELETE" not in perms

    def test_resolve_permissions_unknown_role(self) -> None:
        policy = RoleBasedPolicy(make_bindings())
        perms = policy.resolve_permissions(frozenset({"NONEXISTENT"}))
        assert perms == frozenset()


# ======================================================================
# ActorResolver (via stub)
# ======================================================================


class TestActorResolver:

    def test_resolve_from_context(self) -> None:
        resolver = StubActorResolver()
        actor = resolver.resolve({"user_id": "u-1", "org_id": "o-1", "roles": ["ADMIN"]})
        assert actor.actor_id == "u-1"
        assert actor.org_id == "o-1"
        assert "ADMIN" in actor.roles

    def test_resolve_defaults(self) -> None:
        resolver = StubActorResolver()
        actor = resolver.resolve({})
        assert actor.actor_id == "unknown"
        assert actor.org_id == ""
