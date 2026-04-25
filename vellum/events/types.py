"""
Event Types
===========

Data structures for actor attribution, audit logging, and lifecycle
event sourcing.

All types are immutable-by-convention dataclasses with no external
dependencies.  They form the foundation of compliance-grade record
keeping: every mutation is attributed to an actor and recorded as
an immutable event.
"""

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class ActorStamp:
    """Immutable attribution record: who did what, when.

    Attached to every audit entry and lifecycle event to provide
    a tamper-evident trail of actor actions.

    Attributes:
        actor_id: Unique identifier of the acting user or system.
        action: The action performed (e.g. ``"CREATE"``, ``"SEAL"``).
        timestamp: ISO 8601 timestamp of the action.
        org_id: Tenant/organization context.
        ip_address: Source IP address (if available).
        metadata: Additional context (user-agent, session, etc.).
    """

    actor_id: str
    action: str
    timestamp: str
    org_id: str = ""
    ip_address: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AuditEntry:
    """Structured audit log entry.

    Represents a single auditable action on a resource.  Includes
    the actor attribution, the resource affected, the action taken,
    and an optional change set for field-level diffing.

    Attributes:
        entry_id: Unique identifier for this audit entry.
        actor: The ``ActorStamp`` attributing the action.
        resource_type: Type of resource affected (e.g. ``"Invoice"``).
        resource_id: Identifier of the specific resource.
        action: Action performed (e.g. ``"CREATE"``, ``"UPDATE"``).
        changes: Field-level changes as ``{field: {"old": v, "new": v}}``.
        timestamp: ISO 8601 timestamp of the entry.
    """

    entry_id: str
    actor: ActorStamp
    resource_type: str
    resource_id: str
    action: str
    changes: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""


@dataclass
class LifecycleEvent:
    """State transition event for event sourcing.

    Records a state change in a resource's lifecycle.  The ordered
    sequence of lifecycle events for a resource constitutes its
    complete history and can be replayed to reconstruct state.

    Attributes:
        event_id: Unique identifier for this event.
        resource_type: Type of resource (e.g. ``"Contract"``).
        resource_id: Identifier of the specific resource.
        event_type: Type of event (e.g. ``"STATUS_CHANGED"``).
        actor: The ``ActorStamp`` attributing the event.
        from_state: Previous state (empty for creation events).
        to_state: New state after the transition.
        payload: Additional event-specific data.
        timestamp: ISO 8601 timestamp of the event.
    """

    event_id: str
    resource_type: str
    resource_id: str
    event_type: str
    actor: ActorStamp
    from_state: str = ""
    to_state: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""
