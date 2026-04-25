"""
Consensus Configuration
=======================

Domain-agnostic configuration for multi-party consensus.

This module provides configuration primitives that work across ANY domain:
- Trade contracts (buyer/seller)
- Lease agreements (lessor/lessee)
- Supply chain (shipper/consignee/carrier)
- Custom workflows with arbitrary party roles

Design Principles:
    1. Party roles are strings, not enums - any domain defines their own
    2. Consensus rules are passed in at instantiation, not hardcoded
    3. Field patterns use wildcards for flexible matching
    4. "Authority" concept: who is source of truth for a field

Example Usage:
    # Trade domain
    config = ConsensusConfig(
        party_roles={"buyer", "seller"},
        default_required_approvers={"buyer", "seller"},
        default_authoritative_role="seller",
    )

    # Lease domain
    config = ConsensusConfig(
        party_roles={"lessor", "lessee", "guarantor"},
        default_required_approvers={"lessor", "lessee"},
        default_authoritative_role="lessor",
    )
"""

from typing import Dict, Optional, Set, List, Any
from dataclasses import dataclass, field


@dataclass
class ConsensusRule:
    """
    Rule for field-level consensus.

    Defines who must approve a field and who is authoritative.
    All roles are strings - domain defines their meaning.
    """

    field_pattern: str  # Field path pattern (supports * wildcard)
    required_approvers: Set[str]  # Roles that MUST approve
    authoritative_role: str  # Role that is "source of truth"
    optional_approvers: Set[str] = field(default_factory=set)  # Can approve but not required

    def matches(self, field_path: str) -> bool:
        """
        Check if this rule matches a field path.

        Supports:
            - Exact match: "price" matches "price"
            - Wildcard suffix: "payment.*" matches "payment.terms", "payment.amount"
            - Universal wildcard: "*" matches anything
        """
        if self.field_pattern == "*":
            return True

        if self.field_pattern == field_path:
            return True

        if self.field_pattern.endswith(".*"):
            prefix = self.field_pattern[:-2]
            return field_path.startswith(prefix + ".") or field_path == prefix

        return False


@dataclass
class ConsensusResult:
    """Result of a consensus check - domain agnostic."""

    is_reached: bool  # Whether all required approvers have approved
    approved_by: Set[str]  # Roles that have approved (strings)
    pending_approvers: Set[str]  # Roles still needed (strings)
    can_force: bool = False  # Whether authoritative role can force consensus


@dataclass
class PartyApproval:
    """
    Approval from a party - domain agnostic.

    Note: Uses 'party_id' instead of 'member_id' to be domain-neutral.
    The consuming code maps their domain entities to party_id.
    """

    party_id: str  # Unique identifier for the approving party
    role: str  # String role (e.g., "buyer", "lessor", "shipper")
    approved_at: str  # ISO timestamp
    proposal_id: str  # Reference to the proposal being approved


@dataclass
class ConsensusConfig:
    """
    Domain-agnostic configuration for multi-party consensus.

    This is the main configuration object. Instantiate with your domain's
    party roles and consensus rules.

    Attributes:
        party_roles: Set of valid party role strings for this domain
        rules: Dict mapping field patterns to consensus rules
        default_required_approvers: Default approvers if no rule matches
        default_authoritative_role: Default authority if no rule matches
    """

    party_roles: Set[str]  # Valid roles in this domain
    default_required_approvers: Set[str]  # Who must approve by default
    default_authoritative_role: str  # Who is authoritative by default
    rules: Dict[str, ConsensusRule] = field(default_factory=dict)

    def __post_init__(self):
        """Validate configuration after initialization."""
        # Ensure default approvers are valid roles
        invalid = self.default_required_approvers - self.party_roles
        if invalid:
            raise ValueError(f"Default approvers contain invalid roles: {invalid}")

        # Ensure default authority is a valid role
        if self.default_authoritative_role not in self.party_roles:
            raise ValueError(
                f"Default authoritative role '{self.default_authoritative_role}' "
                f"is not in party_roles: {self.party_roles}"
            )

        # Validate each rule
        for pattern, rule in self.rules.items():
            self._validate_rule(pattern, rule)

    def _validate_rule(self, pattern: str, rule: ConsensusRule):
        """Validate a consensus rule against configured party roles."""
        invalid_required = rule.required_approvers - self.party_roles
        if invalid_required:
            raise ValueError(
                f"Rule '{pattern}' has invalid required_approvers: {invalid_required}"
            )

        if rule.authoritative_role not in self.party_roles:
            raise ValueError(
                f"Rule '{pattern}' has invalid authoritative_role: {rule.authoritative_role}"
            )

        invalid_optional = rule.optional_approvers - self.party_roles
        if invalid_optional:
            raise ValueError(
                f"Rule '{pattern}' has invalid optional_approvers: {invalid_optional}"
            )

    def add_rule(self, rule: ConsensusRule) -> "ConsensusConfig":
        """
        Add a consensus rule.

        Args:
            rule: The ConsensusRule to add

        Returns:
            Self for chaining
        """
        self._validate_rule(rule.field_pattern, rule)
        self.rules[rule.field_pattern] = rule
        return self

    def get_rule(self, field_path: str) -> ConsensusRule:
        """
        Get the consensus rule for a field path.

        Matching priority:
            1. Exact match
            2. Wildcard pattern match (most specific first)
            3. Default rule

        Args:
            field_path: The field path to match

        Returns:
            Matching ConsensusRule
        """
        # 1. Try exact match
        if field_path in self.rules:
            return self.rules[field_path]

        # 2. Try wildcard patterns (prefer longer/more specific patterns)
        matching_rules = [
            (pattern, rule)
            for pattern, rule in self.rules.items()
            if rule.matches(field_path) and pattern != "*"
        ]
        if matching_rules:
            # Sort by pattern length descending (most specific wins)
            matching_rules.sort(key=lambda x: len(x[0]), reverse=True)
            return matching_rules[0][1]

        # 3. Try universal wildcard
        if "*" in self.rules:
            return self.rules["*"]

        # 4. Return default rule
        return ConsensusRule(
            field_pattern="*",
            required_approvers=self.default_required_approvers.copy(),
            authoritative_role=self.default_authoritative_role,
        )

    def get_required_approvers(self, field_path: str) -> Set[str]:
        """Get roles that must approve a field."""
        return self.get_rule(field_path).required_approvers.copy()

    def get_authoritative_role(self, field_path: str) -> str:
        """Get the authoritative role for a field."""
        return self.get_rule(field_path).authoritative_role

    def can_role_propose(self, role: str, field_path: str) -> bool:
        """
        Check if a role can propose changes to a field.

        Both required and optional approvers can propose.
        """
        if role not in self.party_roles:
            return False

        rule = self.get_rule(field_path)
        return role in rule.required_approvers or role in rule.optional_approvers

    def can_role_approve(self, role: str, field_path: str) -> bool:
        """Check if a role's approval is needed for consensus."""
        if role not in self.party_roles:
            return False

        rule = self.get_rule(field_path)
        return role in rule.required_approvers

    def check_consensus(
        self,
        field_path: str,
        approvals: List[PartyApproval],
    ) -> ConsensusResult:
        """
        Check if consensus is reached for a field.

        Args:
            field_path: Field path
            approvals: List of approvals received

        Returns:
            ConsensusResult with consensus status
        """
        rule = self.get_rule(field_path)

        # Get roles that have approved
        approved_roles = {approval.role for approval in approvals}

        # Check which required approvers are still pending
        pending = rule.required_approvers - approved_roles

        is_reached = len(pending) == 0

        # Authoritative role can force if they're the only one left
        can_force = len(pending) == 1 and rule.authoritative_role in approved_roles

        return ConsensusResult(
            is_reached=is_reached,
            approved_by=approved_roles,
            pending_approvers=pending,
            can_force=can_force,
        )

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "ConsensusConfig":
        """
        Create ConsensusConfig from a dictionary.

        Useful for loading from JSON/YAML configuration files.

        Expected format:
        {
            "party_roles": ["buyer", "seller", "broker"],
            "default_required_approvers": ["buyer", "seller"],
            "default_authoritative_role": "seller",
            "rules": {
                "price.*": {
                    "required_approvers": ["buyer", "seller"],
                    "authoritative_role": "seller"
                },
                "broker.commission": {
                    "required_approvers": ["buyer", "seller", "broker"],
                    "authoritative_role": "broker"
                }
            }
        }
        """
        rules = {}
        for pattern, rule_dict in config_dict.get("rules", {}).items():
            rules[pattern] = ConsensusRule(
                field_pattern=pattern,
                required_approvers=set(rule_dict.get("required_approvers", [])),
                authoritative_role=rule_dict.get("authoritative_role", ""),
                optional_approvers=set(rule_dict.get("optional_approvers", [])),
            )

        return cls(
            party_roles=set(config_dict.get("party_roles", [])),
            default_required_approvers=set(
                config_dict.get("default_required_approvers", [])
            ),
            default_authoritative_role=config_dict.get(
                "default_authoritative_role", ""
            ),
            rules=rules,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize ConsensusConfig to a dictionary."""
        return {
            "party_roles": list(self.party_roles),
            "default_required_approvers": list(self.default_required_approvers),
            "default_authoritative_role": self.default_authoritative_role,
            "rules": {
                pattern: {
                    "required_approvers": list(rule.required_approvers),
                    "authoritative_role": rule.authoritative_role,
                    "optional_approvers": list(rule.optional_approvers),
                }
                for pattern, rule in self.rules.items()
            },
        }


# ============================================================
# Factory functions for common domain configurations
# ============================================================


def create_bilateral_config(
    party_a: str = "party_a",
    party_b: str = "party_b",
    authoritative_party: str = None,
) -> ConsensusConfig:
    """
    Create a simple bilateral consensus config.

    Both parties must approve all fields. One party is authoritative.

    Args:
        party_a: Name for first party role
        party_b: Name for second party role
        authoritative_party: Which party is authoritative (defaults to party_a)

    Returns:
        ConsensusConfig for bilateral agreement
    """
    auth = authoritative_party or party_a
    return ConsensusConfig(
        party_roles={party_a, party_b},
        default_required_approvers={party_a, party_b},
        default_authoritative_role=auth,
    )


def create_multiparty_config(
    party_roles: Set[str],
    required_approvers: Set[str],
    authoritative_role: str,
    optional_parties: Set[str] = None,
) -> ConsensusConfig:
    """
    Create a multi-party consensus config.

    Args:
        party_roles: All valid party roles
        required_approvers: Roles that must approve
        authoritative_role: Role that is source of truth
        optional_parties: Roles that can participate but aren't required

    Returns:
        ConsensusConfig for multi-party agreement
    """
    all_roles = party_roles | (optional_parties or set())
    config = ConsensusConfig(
        party_roles=all_roles,
        default_required_approvers=required_approvers,
        default_authoritative_role=authoritative_role,
    )

    # Add default rule with optional approvers
    if optional_parties:
        config.add_rule(
            ConsensusRule(
                field_pattern="*",
                required_approvers=required_approvers,
                authoritative_role=authoritative_role,
                optional_approvers=optional_parties,
            )
        )

    return config
