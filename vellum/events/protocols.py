"""
Event Protocols
===============

Abstract interfaces for audit logging and lifecycle event recording.

``AuditLogger`` implementations provide append-only audit storage
(database tables, cloud logging, file-based logs).

``EventRecorder`` implementations provide event sourcing storage
for replaying resource history.

Both are always host-provided — Vellum ships in-memory reference
implementations for testing.
"""

from typing import List, Protocol, runtime_checkable

from .types import AuditEntry, LifecycleEvent


@runtime_checkable
class AuditLogger(Protocol):
    """Append-only audit log for compliance-grade record keeping.

    The contract:
        - ``log`` must be append-only — entries are never modified
          or deleted.
        - ``query`` returns entries in chronological order.

    Implementations: database (Postgres, MySQL), cloud logging
    (CloudWatch, Stackdriver), file-based (JSONL).
    """

    def log(self, entry: AuditEntry) -> None:
        """Append an audit entry to the log.

        Args:
            entry: The structured audit entry to record.
        """
        ...

    def query(
        self, resource_type: str, resource_id: str
    ) -> List[AuditEntry]:
        """Retrieve audit entries for a specific resource.

        Args:
            resource_type: Type of resource to query.
            resource_id: Identifier of the specific resource.

        Returns:
            List of ``AuditEntry`` in chronological order.
        """
        ...


@runtime_checkable
class EventRecorder(Protocol):
    """Records lifecycle events for event sourcing and replay.

    The contract:
        - ``record`` must be append-only.
        - ``get_history`` returns events in chronological order.

    Implementations: event store (EventStoreDB), database
    (append-only table), message queue (Kafka).
    """

    def record(self, event: LifecycleEvent) -> None:
        """Record a lifecycle event.

        Args:
            event: The lifecycle event to store.
        """
        ...

    def get_history(
        self, resource_type: str, resource_id: str
    ) -> List[LifecycleEvent]:
        """Retrieve the event history for a specific resource.

        Args:
            resource_type: Type of resource to query.
            resource_id: Identifier of the specific resource.

        Returns:
            List of ``LifecycleEvent`` in chronological order.
        """
        ...
