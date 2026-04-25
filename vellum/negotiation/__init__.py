"""
Vellum Negotiation Protocol
===========================

Domain-agnostic multi-party negotiation primitives — protocol surface only.

This package provides the **public protocol** for field-level propose-agree
workflows: configuration schemas, type definitions, store protocols, and
adapter contracts.

The production runtime (consensus engine, field state machine, proposal
manager, orchestrator) is shipped separately under commercial license.

Public surface:
    - ConsensusConfig / ConsensusRule  — declarative rule schema
    - EntityTypeConfig                 — entity registration schema
    - FieldProposal / ProposalResult   — proposal data types
    - ProposalStore                    — store protocol
    - NamespaceAdapter                 — cross-namespace adapter protocol

Implement these protocols against your own runtime, or contact the maintainer
for a commercial runtime license.
"""

# -- Consensus primitives (schema only) ------------------------------------
from .consensus_config import (
    ConsensusConfig,
    ConsensusRule,
    ConsensusResult,
    PartyApproval,
    create_bilateral_config,
    create_multiparty_config,
)

# -- Entity type registry ---------------------------------------------------
from .entity_config import (
    EntityTypeConfig,
    register_entity_type,
    get_entity_config,
    get_registered_entity_types,
)

# -- Proposal types ---------------------------------------------------------
from .proposal_types import (
    FieldProposal,
    ProposalResult,
    AcceptResult,
    RejectResult,
    ProposalStatus,
    ConcurrentModificationError,
    READONLY_FIELDS,
)

# -- Proposal store protocol ------------------------------------------------
from .proposal_store import ProposalStore

# -- Namespace adapter protocol ---------------------------------------------
from .namespace_adapter import (
    NamespaceAdapter,
    AccessResult,
    SyncResult,
)


__all__ = [
    # Consensus config
    "ConsensusConfig",
    "ConsensusRule",
    "ConsensusResult",
    "PartyApproval",
    "create_bilateral_config",
    "create_multiparty_config",
    # Entity config
    "EntityTypeConfig",
    "register_entity_type",
    "get_entity_config",
    "get_registered_entity_types",
    # Proposal types
    "FieldProposal",
    "ProposalResult",
    "AcceptResult",
    "RejectResult",
    "ProposalStatus",
    "ConcurrentModificationError",
    "READONLY_FIELDS",
    # Proposal store
    "ProposalStore",
    # Namespace adapter
    "NamespaceAdapter",
    "AccessResult",
    "SyncResult",
]
