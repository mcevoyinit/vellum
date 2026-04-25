"""
Proposal Store Protocol
=======================

Abstract persistence interface for proposal storage.

Implementations handle the actual storage backend (database, file, in-memory,
etc.). The ProposalManager delegates all persistence to this protocol.
"""

from typing import List, Optional, Protocol, runtime_checkable

from .proposal_types import FieldProposal


@runtime_checkable
class ProposalStore(Protocol):
    """Protocol for proposal persistence backends.

    Implementations must provide all methods below.  When ProposalManager
    is created without a store (``store=None``), persistence is skipped
    and query methods return empty lists.
    """

    def fetch_proposal(self, proposal_id: str) -> Optional[FieldProposal]:
        """Fetch a single proposal by ID."""
        ...

    def persist_proposal(self, proposal: FieldProposal) -> bool:
        """Persist a new proposal. Returns True on success."""
        ...

    def update_proposal(self, proposal: FieldProposal) -> bool:
        """Update an existing proposal. Returns True on success."""
        ...

    def cancel_proposal(self, proposal_id: str, reason: str) -> bool:
        """Cancel a proposal with a reason. Returns True on success."""
        ...

    def get_pending_proposals(self, entity_id: str) -> List[FieldProposal]:
        """Get all pending proposals for an entity."""
        ...

    def get_pending_proposals_for_field(
        self, entity_id: str, field_path: str
    ) -> List[FieldProposal]:
        """Get pending proposals for a specific field."""
        ...

    def get_pending_proposals_by_party(
        self, entity_id: str, party_id: str
    ) -> List[FieldProposal]:
        """Get pending proposals submitted by a specific party."""
        ...

    def get_proposal_history(
        self, entity_id: str, field_path: str
    ) -> List[FieldProposal]:
        """Get all proposals for a field in chronological order."""
        ...
