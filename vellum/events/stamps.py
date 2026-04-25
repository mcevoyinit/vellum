"""
Stamp & Entry Factories
========================

Convenience functions for creating ``ActorStamp``, ``AuditEntry``,
and ``LifecycleEvent`` instances with auto-generated IDs and
timestamps.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .types import ActorStamp, AuditEntry, LifecycleEvent


def _utc_now() -> str:
    """ISO 8601 UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


def create_actor_stamp(
    actor_id: str,
    action: str,
    *,
    org_id: str = "",
    ip_address: str = "",
    timestamp: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> ActorStamp:
    """Create an ``ActorStamp`` with auto-generated timestamp.

    Args:
        actor_id: Unique identifier of the acting user or system.
        action: The action performed.
        org_id: Tenant/organization context.
        ip_address: Source IP address.
        timestamp: ISO 8601 timestamp (auto-generated if omitted).
        metadata: Additional context.

    Returns:
        Populated ``ActorStamp``.
    """
    return ActorStamp(
        actor_id=actor_id,
        action=action,
        timestamp=timestamp or _utc_now(),
        org_id=org_id,
        ip_address=ip_address,
        metadata=metadata or {},
    )


def create_audit_entry(
    actor: ActorStamp,
    resource_type: str,
    resource_id: str,
    action: str,
    *,
    changes: Optional[Dict[str, Any]] = None,
    timestamp: Optional[str] = None,
    entry_id: Optional[str] = None,
) -> AuditEntry:
    """Create an ``AuditEntry`` with auto-generated ID and timestamp.

    Args:
        actor: The actor attribution stamp.
        resource_type: Type of resource affected.
        resource_id: Identifier of the specific resource.
        action: Action performed.
        changes: Field-level changes.
        timestamp: ISO 8601 timestamp (auto-generated if omitted).
        entry_id: Entry ID (auto-generated UUID if omitted).

    Returns:
        Populated ``AuditEntry``.
    """
    return AuditEntry(
        entry_id=entry_id or str(uuid.uuid4()),
        actor=actor,
        resource_type=resource_type,
        resource_id=resource_id,
        action=action,
        changes=changes or {},
        timestamp=timestamp or _utc_now(),
    )


def create_lifecycle_event(
    actor: ActorStamp,
    resource_type: str,
    resource_id: str,
    event_type: str,
    *,
    from_state: str = "",
    to_state: str = "",
    payload: Optional[Dict[str, Any]] = None,
    timestamp: Optional[str] = None,
    event_id: Optional[str] = None,
) -> LifecycleEvent:
    """Create a ``LifecycleEvent`` with auto-generated ID and timestamp.

    Args:
        actor: The actor attribution stamp.
        resource_type: Type of resource.
        resource_id: Identifier of the specific resource.
        event_type: Type of event.
        from_state: Previous state.
        to_state: New state.
        payload: Additional event-specific data.
        timestamp: ISO 8601 timestamp (auto-generated if omitted).
        event_id: Event ID (auto-generated UUID if omitted).

    Returns:
        Populated ``LifecycleEvent``.
    """
    return LifecycleEvent(
        event_id=event_id or str(uuid.uuid4()),
        resource_type=resource_type,
        resource_id=resource_id,
        event_type=event_type,
        actor=actor,
        from_state=from_state,
        to_state=to_state,
        payload=payload or {},
        timestamp=timestamp or _utc_now(),
    )
