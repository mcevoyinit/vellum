"""
Sealing Protocols
=================

Abstract interfaces for content integrity and sealing operations.

Implementations handle the actual hashing strategy, signing mechanism,
and verification logic.  Vellum ships ``SHA256Hasher`` as a reference
``ContentHasher`` implementation.  ``SealAuthority`` implementations
are always host-provided (HSMs, PKI, smart contract signers, etc.).
"""

from typing import Any, Dict, Protocol, runtime_checkable

from .types import ContentHash, SealPayload, SealResult, VerificationResult


@runtime_checkable
class ContentHasher(Protocol):
    """Canonicalizes and hashes structured data for tamper detection.

    Implementations define the canonicalization strategy (key ordering,
    whitespace handling, encoding) and the hash algorithm.

    The contract:
        - ``canonicalize`` must be **deterministic** — the same logical
          data must always produce the same string.
        - ``hash`` must be a cryptographic hash function.
        - ``compute_hash`` combines both steps and returns a ``ContentHash``.
    """

    def canonicalize(self, data: Dict[str, Any]) -> str:
        """Produce a deterministic canonical string from structured data.

        Implementations typically sort keys, strip whitespace, and
        encode as UTF-8.
        """
        ...

    def hash(self, content: str) -> str:
        """Hash a canonical string and return the hex digest."""
        ...

    def compute_hash(self, data: Dict[str, Any]) -> ContentHash:
        """Canonicalize then hash.  Returns a full ``ContentHash``."""
        ...

    def verify_hash(self, data: Dict[str, Any], expected: str) -> bool:
        """Verify that data matches an expected hash digest."""
        ...


@runtime_checkable
class SealAuthority(Protocol):
    """Signs content hashes to produce tamper-evident seals.

    Implementations wrap the actual signing infrastructure — hardware
    security modules, PKI certificate authorities, smart contract
    signers, or simple HMAC for testing.

    The pipeline calls ``seal`` after the ``ContentHasher`` has produced
    the content hash.  ``verify`` checks an existing seal's validity.
    """

    def seal(self, payload: SealPayload) -> SealResult:
        """Apply a seal to the given payload.

        The implementation signs the content hash and stores the seal
        record in its backing store.

        Args:
            payload: Structured seal payload with content hash,
                subject info, and authority metadata.

        Returns:
            ``SealResult`` with the seal ID and display reference
            on success, or an error message on failure.
        """
        ...

    def verify(self, seal_id: str, content_hash: str) -> VerificationResult:
        """Verify an existing seal against a content hash.

        Args:
            seal_id: The seal record identifier.
            content_hash: Expected content hash to verify against.

        Returns:
            ``VerificationResult`` indicating whether the seal is valid.
        """
        ...
