"""
Tests for vellum.events
========================

Audit logging, lifecycle event sourcing, actor stamps, and factory
functions.  Protocol conformance and in-memory implementations.
"""

from typing import Any, Dict, List

import pytest

from vellum.events import (
    ActorStamp,
    AuditEntry,
    AuditLogger,
    EventRecorder,
    InMemoryAuditLogger,
    InMemoryEventRecorder,
    LifecycleEvent,
    create_actor_stamp,
    create_audit_entry,
    create_lifecycle_event,
)


# ======================================================================
# Protocol conformance
# ======================================================================


class TestProtocolConformance:

    def test_memory_logger_is_audit_logger(self) -> None:
        assert isinstance(InMemoryAuditLogger(), AuditLogger)

    def test_memory_recorder_is_event_recorder(self) -> None:
        assert isinstance(InMemoryEventRecorder(), EventRecorder)


# ======================================================================
# ActorStamp
# ======================================================================


class TestActorStamp:

    def test_create_actor_stamp(self) -> None:
        stamp = create_actor_stamp(
            "user-1", "CREATE",
            org_id="org-1",
            ip_address="10.0.0.1",
            timestamp="2026-01-01T00:00:00Z",
        )
        assert stamp.actor_id == "user-1"
        assert stamp.action == "CREATE"
        assert stamp.org_id == "org-1"
        assert stamp.ip_address == "10.0.0.1"
        assert stamp.timestamp == "2026-01-01T00:00:00Z"

    def test_auto_timestamp(self) -> None:
        stamp = create_actor_stamp("user-1", "UPDATE")
        assert stamp.timestamp  # Auto-generated
        assert "T" in stamp.timestamp  # ISO 8601 format

    def test_metadata(self) -> None:
        stamp = create_actor_stamp(
            "user-1", "CREATE",
            metadata={"user_agent": "curl/7.68.0"},
        )
        assert stamp.metadata["user_agent"] == "curl/7.68.0"

    def test_default_metadata_empty(self) -> None:
        stamp = create_actor_stamp("user-1", "CREATE")
        assert stamp.metadata == {}


# ======================================================================
# InMemoryAuditLogger
# ======================================================================


class TestAuditLogger:

    def setup_method(self) -> None:
        self.logger = InMemoryAuditLogger()
        self.stamp = create_actor_stamp(
            "user-1", "UPDATE",
            org_id="org-1",
            timestamp="2026-01-01T00:00:00Z",
        )

    def test_log_and_query(self) -> None:
        entry = create_audit_entry(
            self.stamp, "Invoice", "INV-001", "CREATE",
            timestamp="2026-01-01T00:00:00Z",
        )
        self.logger.log(entry)
        results = self.logger.query("Invoice", "INV-001")
        assert len(results) == 1
        assert results[0].action == "CREATE"

    def test_query_empty(self) -> None:
        results = self.logger.query("Invoice", "INV-999")
        assert results == []

    def test_multiple_entries_same_resource(self) -> None:
        for action in ["CREATE", "UPDATE", "SEAL"]:
            entry = create_audit_entry(
                self.stamp, "Invoice", "INV-001", action,
            )
            self.logger.log(entry)
        results = self.logger.query("Invoice", "INV-001")
        assert len(results) == 3
        assert [r.action for r in results] == ["CREATE", "UPDATE", "SEAL"]

    def test_different_resources_independent(self) -> None:
        self.logger.log(create_audit_entry(self.stamp, "Invoice", "INV-001", "CREATE"))
        self.logger.log(create_audit_entry(self.stamp, "Invoice", "INV-002", "CREATE"))
        assert len(self.logger.query("Invoice", "INV-001")) == 1
        assert len(self.logger.query("Invoice", "INV-002")) == 1

    def test_all_entries(self) -> None:
        self.logger.log(create_audit_entry(self.stamp, "Invoice", "INV-001", "CREATE"))
        self.logger.log(create_audit_entry(self.stamp, "Contract", "CON-001", "CREATE"))
        assert len(self.logger.all_entries) == 2

    def test_changes_field(self) -> None:
        entry = create_audit_entry(
            self.stamp, "Invoice", "INV-001", "UPDATE",
            changes={"amount": {"old": 100, "new": 150}},
        )
        self.logger.log(entry)
        results = self.logger.query("Invoice", "INV-001")
        assert results[0].changes["amount"]["new"] == 150


# ======================================================================
# InMemoryEventRecorder
# ======================================================================


class TestEventRecorder:

    def setup_method(self) -> None:
        self.recorder = InMemoryEventRecorder()
        self.stamp = create_actor_stamp(
            "user-1", "TRANSITION",
            org_id="org-1",
            timestamp="2026-01-01T00:00:00Z",
        )

    def test_record_and_get_history(self) -> None:
        event = create_lifecycle_event(
            self.stamp, "Invoice", "INV-001", "STATUS_CHANGED",
            from_state="DRAFT", to_state="REVIEW",
        )
        self.recorder.record(event)
        history = self.recorder.get_history("Invoice", "INV-001")
        assert len(history) == 1
        assert history[0].from_state == "DRAFT"
        assert history[0].to_state == "REVIEW"

    def test_history_empty(self) -> None:
        assert self.recorder.get_history("Invoice", "INV-999") == []

    def test_ordered_history(self) -> None:
        for i, (from_s, to_s) in enumerate([
            ("DRAFT", "REVIEW"),
            ("REVIEW", "APPROVED"),
        ]):
            event = create_lifecycle_event(
                self.stamp, "Invoice", "INV-001", "STATUS_CHANGED",
                from_state=from_s, to_state=to_s,
            )
            self.recorder.record(event)
        history = self.recorder.get_history("Invoice", "INV-001")
        assert len(history) == 2
        assert history[0].from_state == "DRAFT"
        assert history[1].from_state == "REVIEW"

    def test_different_resources_independent(self) -> None:
        self.recorder.record(create_lifecycle_event(
            self.stamp, "Invoice", "INV-001", "CREATED",
        ))
        self.recorder.record(create_lifecycle_event(
            self.stamp, "Invoice", "INV-002", "CREATED",
        ))
        assert len(self.recorder.get_history("Invoice", "INV-001")) == 1
        assert len(self.recorder.get_history("Invoice", "INV-002")) == 1

    def test_all_events(self) -> None:
        self.recorder.record(create_lifecycle_event(
            self.stamp, "Invoice", "INV-001", "CREATED",
        ))
        self.recorder.record(create_lifecycle_event(
            self.stamp, "Contract", "CON-001", "CREATED",
        ))
        assert len(self.recorder.all_events) == 2

    def test_payload_included(self) -> None:
        event = create_lifecycle_event(
            self.stamp, "Invoice", "INV-001", "SEALED",
            payload={"seal_id": "SEAL-001"},
        )
        self.recorder.record(event)
        history = self.recorder.get_history("Invoice", "INV-001")
        assert history[0].payload["seal_id"] == "SEAL-001"


# ======================================================================
# Factory functions
# ======================================================================


class TestFactoryFunctions:

    def test_audit_entry_auto_id(self) -> None:
        stamp = create_actor_stamp("u-1", "CREATE")
        e1 = create_audit_entry(stamp, "Doc", "D-1", "CREATE")
        e2 = create_audit_entry(stamp, "Doc", "D-2", "CREATE")
        assert e1.entry_id != e2.entry_id  # UUID-based

    def test_audit_entry_custom_id(self) -> None:
        stamp = create_actor_stamp("u-1", "CREATE")
        entry = create_audit_entry(stamp, "Doc", "D-1", "CREATE", entry_id="CUSTOM-001")
        assert entry.entry_id == "CUSTOM-001"

    def test_lifecycle_event_auto_id(self) -> None:
        stamp = create_actor_stamp("u-1", "TRANSITION")
        e1 = create_lifecycle_event(stamp, "Doc", "D-1", "CREATED")
        e2 = create_lifecycle_event(stamp, "Doc", "D-2", "CREATED")
        assert e1.event_id != e2.event_id  # UUID-based

    def test_lifecycle_event_custom_id(self) -> None:
        stamp = create_actor_stamp("u-1", "TRANSITION")
        event = create_lifecycle_event(
            stamp, "Doc", "D-1", "CREATED", event_id="EVT-001",
        )
        assert event.event_id == "EVT-001"

    def test_lifecycle_event_auto_timestamp(self) -> None:
        stamp = create_actor_stamp("u-1", "TRANSITION")
        event = create_lifecycle_event(stamp, "Doc", "D-1", "CREATED")
        assert event.timestamp  # Auto-generated
