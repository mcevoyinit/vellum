"""
Sealing Types
=============

Data structures for content integrity and sealing operations.

All types are pure dataclasses with no external dependencies.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class ContentHash:
    """Result of canonicalizing and hashing content.

    Attributes:
        algorithm: Hash algorithm used (e.g. ``"sha256"``).
        digest: Hex-encoded hash digest (lowercase).
        canonical_form: The canonical string that was hashed.
    """

    algorithm: str
    digest: str
    canonical_form: str

    def matches(self, other_digest: str) -> bool:
        """Check if this hash matches another digest (case-insensitive)."""
        return self.digest.lower() == other_digest.lower()


@dataclass
class SealPayload:
    """Structured payload for a seal operation.

    Schema-versioned envelope containing subject, content hash,
    authority info, and metadata.  Implementations of ``SealAuthority``
    sign this payload.

    Attributes:
        schema_version: Seal schema version (e.g. ``"1.0"``).
        subject_type: Type of entity being sealed (e.g. ``"Invoice"``).
        subject_id: Unique identifier of the entity.
        content_hash: Hash of the canonical content.
        hash_algorithm: Algorithm used for hashing.
        content_type: MIME type of the original content.
        authority_type: Type of signing authority (e.g. ``"SERVER_RELAY"``).
        signer_id: Identifier of the signing party.
        org_id: Organization identifier.
        seal_type: Category of seal (e.g. ``"APPROVAL"``, ``"NOTARIZATION"``).
        nonce: Cryptographic nonce for replay protection.
        timestamp: ISO 8601 timestamp of the seal operation.
        metadata: Additional key-value metadata.
    """

    schema_version: str
    subject_type: str
    subject_id: str
    content_hash: str
    hash_algorithm: str
    content_type: str
    authority_type: str
    signer_id: str
    org_id: str
    seal_type: str
    nonce: str
    timestamp: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a plain dictionary for serialization."""
        return {
            "schema_version": self.schema_version,
            "subject": {
                "type": self.subject_type,
                "id": self.subject_id,
            },
            "content": {
                "hash": self.content_hash,
                "hash_algorithm": self.hash_algorithm,
                "content_type": self.content_type,
            },
            "authority": {
                "type": self.authority_type,
                "signer_id": self.signer_id,
                "org_id": self.org_id,
            },
            "metadata": {
                "seal_type": self.seal_type,
                "nonce": self.nonce,
                "timestamp": self.timestamp,
                **self.metadata,
            },
        }


@dataclass
class SealResult:
    """Result of a seal operation.

    Attributes:
        success: Whether the seal was applied successfully.
        seal_id: Unique identifier for the seal record.
        display_reference: Human-readable reference (e.g. ``"VRF-A3B2-C9D1"``).
        content_hash: The content hash that was sealed.
        error: Error message if the operation failed.
    """

    success: bool
    seal_id: Optional[str] = None
    display_reference: Optional[str] = None
    content_hash: Optional[ContentHash] = None
    error: Optional[str] = None


@dataclass
class VerificationResult:
    """Result of verifying a seal.

    Attributes:
        valid: Whether the seal is valid overall.
        content_hash_match: Whether the content hash matches.
        signature_valid: Whether the cryptographic signature is valid
            (``None`` if not checked).
        seal_id: The seal identifier that was verified.
        error: Error message if verification failed.
    """

    valid: bool
    content_hash_match: bool = False
    signature_valid: Optional[bool] = None
    seal_id: Optional[str] = None
    error: Optional[str] = None
