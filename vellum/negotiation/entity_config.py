"""
Entity Type Configuration Registry
===================================

Per-entity-type configuration for the negotiation engine.

Each entity type (e.g., RepoAgreement, LeaseAgreement) registers a config
that describes how it participates in negotiation: its participant roles,
reference fields, type hints for coercion, lifecycle stages, etc.

The negotiation engine reads from this registry instead of hardcoding
domain-specific constants.

Usage:
    from .entity_config import get_entity_config, register_entity_type

    # Get config for an entity type
    config = get_entity_config("RepoAgreement")
    print(config.participant_fields)  # {"borrower": ["borrowerId", ...], ...}

    # Register a new entity type
    register_entity_type(EntityTypeConfig(
        graphql_type="LeaseAgreement",
        ...
    ))
"""

from dataclasses import dataclass
from typing import Dict, FrozenSet, List, Optional


@dataclass(frozen=True)
class EntityTypeConfig:
    """Per-entity-type configuration for the negotiation engine.

    Encapsulates all metadata that varies between entity types.
    One config per entity type.  All fields are required at construction.
    """

    # GraphQL type name (used in get{X}/add{X} query templates)
    graphql_type: str

    # Participant field mapping: role_name -> [scalar_id_field, edge_path]
    # Used by _determine_party_role to resolve who is who.
    # e.g. {"buyer": ("buyerId", "buyer.id"), "seller": ("sellerId", "seller.id")}
    participant_fields: Dict[str, tuple]

    # Which scalar field identifies the "source of truth" namespace owner
    source_namespace_field: str

    # Root-level fields that are entity references (skip write-back via parent
    # upsert to avoid orphaned nodes; consensus recorded in NegotiableFieldStatus only)
    reference_fields: FrozenSet[str]

    # Field type hints for coercion (field_path -> GraphQL scalar type name)
    field_type_hints: Dict[str, str]

    # Ordered lifecycle stages
    lifecycle_stages: tuple  # tuple of str for immutability

    # Mandatory fields per target status
    mandatory_fields: Dict[str, tuple]  # status -> tuple of field paths

    # Lock stages per field path
    lock_stages: Dict[str, tuple]  # field_path -> tuple of statuses

    # Identity fields (set at creation, excluded from mandatory checks)
    identity_fields: FrozenSet[str]

    # Schema field name -> negotiation field path
    # e.g. {"rent": "rent.amount"}
    field_path_mappings: Dict[str, str]

    # --- NEW (optional, with defaults) — added for Vellum convergence ---
    creator_field: str = ""                              # Who creates this doc (e.g., "seller")
    creator_only_roles: FrozenSet[str] = frozenset()     # Role restriction on creation
    tags: FrozenSet[str] = frozenset()                   # Type classifications (e.g., {"document", "sync_eligible"})


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_ENTITY_TYPE_CONFIGS: Dict[str, EntityTypeConfig] = {}


def register_entity_type(config: EntityTypeConfig) -> None:
    """Register an entity type configuration."""
    _ENTITY_TYPE_CONFIGS[config.graphql_type] = config


def get_entity_config(entity_type: str) -> EntityTypeConfig:
    """Look up the config for *entity_type*.

    Raises KeyError if no config is registered.
    """
    if entity_type not in _ENTITY_TYPE_CONFIGS:
        raise KeyError(
            f"No EntityTypeConfig registered for '{entity_type}'. "
            f"Registered types: {list(_ENTITY_TYPE_CONFIGS.keys())}"
        )
    return _ENTITY_TYPE_CONFIGS[entity_type]


def get_entity_config_or_none(entity_type: str) -> "Optional[EntityTypeConfig]":
    """Soft lookup — returns None instead of raising KeyError."""
    return _ENTITY_TYPE_CONFIGS.get(entity_type)


def get_registered_entity_types() -> List[str]:
    """Return all registered entity type names."""
    return list(_ENTITY_TYPE_CONFIGS.keys())
