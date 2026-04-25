"""
Field State Machine — Types
============================

Public type surface for field-level negotiation state.

The runtime ``FieldStateMachine`` (transition logic, lock enforcement,
mandatory-field checks) is shipped separately under commercial license.
This module contains only the type definitions consumers need to
implement against the protocol.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List


class FieldNegotiationStatus(str, Enum):
    """Field negotiation states."""

    DRAFT = "DRAFT"
    PROPOSED = "PROPOSED"
    DISCREPANCY = "DISCREPANCY"
    COUNTER_PROPOSED = "COUNTER_PROPOSED"
    AGREED = "AGREED"
    LOCKED = "LOCKED"
    REJECTED = "REJECTED"
    WAIVED = "WAIVED"


@dataclass
class TransitionResult:
    """Result of a state transition attempt."""

    success: bool
    old_status: FieldNegotiationStatus
    new_status: FieldNegotiationStatus
    reason: str
    requires_sync: bool = False


@dataclass
class FieldLockRule:
    """Rule defining when a field becomes locked.

    ``locked_at_stages`` is a list of lifecycle stage strings.  The
    consuming domain defines what those strings mean.
    """

    field_path: str
    locked_at_stages: List[str]
