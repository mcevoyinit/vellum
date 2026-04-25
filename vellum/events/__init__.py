"""
Vellum Events
=============

Audit logging and lifecycle event sourcing primitives.

Provides immutable actor attribution (``ActorStamp``), structured
audit entries, and lifecycle events for event sourcing.  Host
applications implement ``AuditLogger`` and ``EventRecorder`` with
their persistence layer; Vellum ships in-memory reference
implementations for testing.

Quickstart::

    from vellum.events import (
        InMemoryAuditLogger,
        create_actor_stamp,
        create_audit_entry,
    )

    logger = InMemoryAuditLogger()
    stamp = create_actor_stamp("user-1", "UPDATE", org_id="org-1")
    entry = create_audit_entry(
        stamp, "Invoice", "INV-001", "UPDATE",
        changes={"amount": {"old": 100, "new": 150}},
    )
    logger.log(entry)

    history = logger.query("Invoice", "INV-001")
    assert len(history) == 1

Protocols:

- ``AuditLogger`` — append-only audit log
- ``EventRecorder`` — lifecycle event store for event sourcing
"""

# Reference implementations
from .memory_store import InMemoryAuditLogger, InMemoryEventRecorder

# Protocols
from .protocols import AuditLogger, EventRecorder

# Factory functions
from .stamps import create_actor_stamp, create_audit_entry, create_lifecycle_event

# Types
from .types import ActorStamp, AuditEntry, LifecycleEvent

__all__ = [
    # Reference implementations
    "InMemoryAuditLogger",
    "InMemoryEventRecorder",
    # Protocols
    "AuditLogger",
    "EventRecorder",
    # Factory functions
    "create_actor_stamp",
    "create_audit_entry",
    "create_lifecycle_event",
    # Types
    "ActorStamp",
    "AuditEntry",
    "LifecycleEvent",
]
