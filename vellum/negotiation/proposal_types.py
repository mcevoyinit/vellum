"""
Proposal Types
==============

Data classes and constants for the proposal system.

These types are shared between ProposalManager (domain logic) and
ProposalStore implementations (persistence backends).
"""

from typing import Any, List, Optional
from dataclasses import dataclass, field

from .field_state_machine import FieldNegotiationStatus


class ConcurrentModificationError(Exception):
    """Raised when optimistic locking detects a concurrent modification.

    This occurs when two requests try to update the same field simultaneously.
    The client should retry the operation after fetching the latest state.
    """


class ProposalStatus:
    """Proposal status constants"""

    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    COUNTER_PROPOSED = "COUNTER_PROPOSED"
    SUPERSEDED = "SUPERSEDED"
    WITHDRAWN = "WITHDRAWN"
    CANCELLED = "CANCELLED"  # Orphan proposals when field becomes LOCKED


# System/readonly fields that cannot be negotiated.
# Domain-specific stores can extend this via ProposalManager's
# extra_readonly_fields parameter.
READONLY_FIELDS = frozenset(
    {
        "id",
        "status",
        "createdAt",
        "updatedAt",
        "lastModified",
        "proposedAt",
        "respondedAt",
        "version",
        "entityId",
        "proposerRole",
        "proposerPartyId",
        "proposerCollaboratorId",
        "uid",
    }
)


@dataclass
class FieldProposal:
    """
    A proposal for changing a field value.

    Domain-agnostic: uses string for proposer_role instead of enum.
    """

    proposal_id: str
    entity_id: str  # Generic entity ID
    field_path: str
    proposed_value: Any
    proposer_party_id: str  # Generic party ID
    proposer_collaborator_id: str
    proposer_role: str  # String role (domain-specific)
    status: str
    proposed_at: str
    comment: Optional[str] = None
    responded_at: Optional[str] = None
    responded_by_party_id: Optional[str] = None
    responded_by_collaborator_id: Optional[str] = None
    response_comment: Optional[str] = None
    counter_proposal_id: Optional[str] = None
    superseded_by_id: Optional[str] = None
    version: int = 1  # Optimistic locking version
    is_amendment: bool = False  # True if proposing change to AGREED field
    previous_agreed_value: Optional[str] = None  # Value before amendment proposal


@dataclass
class ProposalResult:
    """Result of a proposal operation"""

    success: bool
    proposal: Optional[FieldProposal] = None
    field_status: Optional[FieldNegotiationStatus] = None
    error: Optional[str] = None
    requires_sync: bool = False


@dataclass
class AcceptResult:
    """Result of accepting a proposal"""

    success: bool
    proposal: Optional[FieldProposal] = None
    field_status: Optional[FieldNegotiationStatus] = None
    consensus_reached: bool = False
    pending_approvers: List[str] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class RejectResult:
    """Result of rejecting a proposal"""

    success: bool
    proposal: Optional[FieldProposal] = None
    counter_proposal: Optional[FieldProposal] = None
    field_status: Optional[FieldNegotiationStatus] = None
    error: Optional[str] = None
