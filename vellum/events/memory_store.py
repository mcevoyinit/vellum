"""
In-Memory Event Implementations
================================

Reference implementations for audit logging and event recording.
All use pure stdlib — no database, no external dependencies.

Suitable for testing, prototyping, and single-process applications.
Production deployments should use persistent implementations
(database, event store, cloud logging).
"""

import threading
from typing import Dict, List, Tuple

from .types import AuditEntry, LifecycleEvent


class InMemoryAuditLogger:
    """List-backed audit log for testing.

    Thread-safe, append-only.  Entries are stored in memory and
    lost when the instance is garbage collected.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        # (resource_type, resource_id) → [entries]
        self._entries: Dict[Tuple[str, str], List[AuditEntry]] = {}

    def log(self, entry: AuditEntry) -> None:
        """Append an audit entry."""
        with self._lock:
            key = (entry.resource_type, entry.resource_id)
            if key not in self._entries:
                self._entries[key] = []
            self._entries[key].append(entry)

    def query(
        self, resource_type: str, resource_id: str
    ) -> List[AuditEntry]:
        """Retrieve audit entries for a resource."""
        with self._lock:
            return list(self._entries.get((resource_type, resource_id), []))

    @property
    def all_entries(self) -> List[AuditEntry]:
        """All entries across all resources (for testing assertions)."""
        with self._lock:
            result: List[AuditEntry] = []
            for entries in self._entries.values():
                result.extend(entries)
            return result


class InMemoryEventRecorder:
    """List-backed event store for testing and prototyping.

    Thread-safe, append-only.  Events are stored in memory and
    lost when the instance is garbage collected.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        # (resource_type, resource_id) → [events]
        self._events: Dict[Tuple[str, str], List[LifecycleEvent]] = {}

    def record(self, event: LifecycleEvent) -> None:
        """Record a lifecycle event."""
        with self._lock:
            key = (event.resource_type, event.resource_id)
            if key not in self._events:
                self._events[key] = []
            self._events[key].append(event)

    def get_history(
        self, resource_type: str, resource_id: str
    ) -> List[LifecycleEvent]:
        """Retrieve event history for a resource."""
        with self._lock:
            return list(self._events.get((resource_type, resource_id), []))

    @property
    def all_events(self) -> List[LifecycleEvent]:
        """All events across all resources (for testing assertions)."""
        with self._lock:
            result: List[LifecycleEvent] = []
            for events in self._events.values():
                result.extend(events)
            return result
