"""
Namespace Adapter
=================

Protocol and result types for cross-namespace operations in the negotiation engine.

The negotiation service uses this adapter interface instead of calling
domain-specific namespace services directly, keeping the engine entity-agnostic.
Each entity type provides its own adapter implementation.

Example:
    class MyNamespaceAdapter:
        def check_access(self, entity_id, member_id, namespace_id, field_path, operation):
            ...
        def sync_to_namespace(self, entity_id, source_namespace_id, target_namespace_id):
            ...

    # The adapter satisfies the NamespaceAdapter protocol
    assert isinstance(MyNamespaceAdapter(), NamespaceAdapter)
"""

from dataclasses import dataclass
from typing import Optional, Protocol, runtime_checkable


@dataclass
class AccessResult:
    """Result of a namespace access check."""

    allowed: bool
    reason: Optional[str] = None


@dataclass
class SyncResult:
    """Result of syncing data to another namespace."""

    success: bool
    error: Optional[str] = None


@runtime_checkable
class NamespaceAdapter(Protocol):
    """
    Protocol for cross-namespace operations.

    Implementations handle access control and data synchronization
    between namespaces for a specific entity type.
    """

    def check_access(
        self,
        entity_id: str,
        member_id: str,
        namespace_id: int,
        field_path: str,
        operation: str,
    ) -> AccessResult:
        """Check if a member has access to perform an operation on an entity field."""
        ...

    def sync_to_namespace(
        self,
        entity_id: str,
        source_namespace_id: int,
        target_namespace_id: int,
    ) -> SyncResult:
        """Sync entity data from source namespace to target namespace."""
        ...
