"""
SHA-256 Content Hasher
======================

Reference implementation of ``ContentHasher`` using JSON canonicalization
and SHA-256 hashing.

No external dependencies.  Uses only ``hashlib``, ``json``, ``secrets``,
and ``uuid`` from the standard library.

Canonicalization strategy:
    1. Recursively sort all dictionary keys
    2. Serialize with no whitespace (compact JSON)
    3. UTF-8 encode

This produces a deterministic byte string for any logically equivalent
JSON object, regardless of original key ordering or formatting.
"""

import hashlib
import json
import secrets
import uuid
from typing import Any, Dict

from .types import ContentHash, SealPayload


class SHA256Hasher:
    """Reference ``ContentHasher`` using JSON canonicalization + SHA-256.

    Usage::

        hasher = SHA256Hasher()
        result = hasher.compute_hash({"amount": 100, "currency": "USD"})
        assert result.algorithm == "sha256"
        assert hasher.verify_hash({"currency": "USD", "amount": 100}, result.digest)
    """

    ALGORITHM = "sha256"

    def canonicalize(self, data: Dict[str, Any]) -> str:
        """Produce canonical JSON: sorted keys, no whitespace, UTF-8.

        Recursively sorts dictionary keys at all nesting levels.
        Lists preserve their original order (order is semantically
        significant in JSON arrays).

        Args:
            data: Dictionary to canonicalize.

        Returns:
            Compact JSON string with deterministic key ordering.
        """
        return json.dumps(
            self._sort_recursive(data),
            separators=(",", ":"),
            ensure_ascii=False,
            sort_keys=True,
        )

    def hash(self, content: str) -> str:
        """SHA-256 hash of a UTF-8 string.

        Args:
            content: String to hash.

        Returns:
            Lowercase hex digest.
        """
        return hashlib.sha256(content.encode("utf-8")).hexdigest().lower()

    def compute_hash(self, data: Dict[str, Any]) -> ContentHash:
        """Canonicalize then hash.

        Args:
            data: Dictionary to hash.

        Returns:
            ``ContentHash`` with algorithm, digest, and canonical form.
        """
        canonical = self.canonicalize(data)
        digest = self.hash(canonical)
        return ContentHash(
            algorithm=self.ALGORITHM,
            digest=digest,
            canonical_form=canonical,
        )

    def verify_hash(self, data: Dict[str, Any], expected: str) -> bool:
        """Check whether data produces the expected hash.

        Args:
            data: Dictionary to verify.
            expected: Expected hex digest.

        Returns:
            ``True`` if the computed hash matches ``expected``.
        """
        return self.compute_hash(data).digest == expected.lower()

    def build_seal_payload(
        self,
        subject_type: str,
        subject_id: str,
        data: Dict[str, Any],
        signer_id: str,
        org_id: str,
        seal_type: str = "APPROVAL",
        authority_type: str = "SERVER_RELAY",
        content_type: str = "application/json",
        timestamp: str = "",
        metadata: Dict[str, Any] | None = None,
    ) -> SealPayload:
        """Build a structured seal payload from raw data.

        Computes the content hash and assembles all seal metadata into
        a ``SealPayload`` ready for signing by a ``SealAuthority``.

        Args:
            subject_type: Type of entity being sealed.
            subject_id: Unique identifier of the entity.
            data: The content to seal (will be hashed).
            signer_id: Identifier of the signing party.
            org_id: Organization identifier.
            seal_type: Category of seal operation.
            authority_type: Type of signing authority.
            content_type: MIME type of the original content.
            timestamp: ISO 8601 timestamp.  Auto-generated if empty.
            metadata: Additional key-value metadata.

        Returns:
            ``SealPayload`` ready for signing.
        """
        from datetime import datetime, timezone

        content_hash = self.compute_hash(data)
        nonce = secrets.token_hex(16)

        if not timestamp:
            timestamp = datetime.now(timezone.utc).isoformat()

        return SealPayload(
            schema_version="1.0",
            subject_type=subject_type,
            subject_id=subject_id,
            content_hash=content_hash.digest,
            hash_algorithm=self.ALGORITHM,
            content_type=content_type,
            authority_type=authority_type,
            signer_id=signer_id,
            org_id=org_id,
            seal_type=seal_type,
            nonce=nonce,
            timestamp=timestamp,
            metadata=metadata or {},
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _sort_recursive(self, obj: Any) -> Any:
        """Recursively sort dictionary keys."""
        if isinstance(obj, dict):
            return {k: self._sort_recursive(v) for k, v in sorted(obj.items())}
        elif isinstance(obj, list):
            return [self._sort_recursive(item) for item in obj]
        return obj


# ------------------------------------------------------------------
# Utility functions
# ------------------------------------------------------------------


def generate_display_reference(prefix: str = "VRF") -> str:
    """Generate a human-readable display reference.

    Format: ``{PREFIX}-{4hex}-{4hex}`` (e.g. ``VRF-A3B2-C9D1``).

    These references are easy to read aloud, copy into emails, and
    use as visual identifiers in UIs.  They are NOT cryptographically
    unique — use ``generate_seal_id`` for unique identifiers.

    Args:
        prefix: Reference prefix (default ``"VRF"``).

    Returns:
        Human-readable reference string.
    """
    segment1 = secrets.token_hex(2).upper()
    segment2 = secrets.token_hex(2).upper()
    return f"{prefix}-{segment1}-{segment2}"


def generate_seal_id(content_hash: str = "") -> str:
    """Generate a unique seal identifier.

    Combines a UUID4 fragment with an optional content hash prefix
    for traceable, unique seal IDs.

    Args:
        content_hash: Optional hash to include as prefix material.

    Returns:
        Unique seal ID string.
    """
    short_uuid = uuid.uuid4().hex[:12]
    if content_hash:
        prefix = content_hash[:8].upper()
        return f"SEAL-{prefix}-{short_uuid}"
    return f"SEAL-{short_uuid}"
