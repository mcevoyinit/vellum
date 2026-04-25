"""
Vellum Sealing
==============

Content integrity primitives for tamper-evident data.

Provides JSON canonicalization, cryptographic hashing, and a seal
protocol for signing content hashes.  Any signing infrastructure
(HSMs, PKI, smart contracts) can implement the ``SealAuthority``
protocol.

Quickstart::

    from vellum.sealing import SHA256Hasher

    hasher = SHA256Hasher()
    result = hasher.compute_hash({"amount": 100, "currency": "USD"})
    assert hasher.verify_hash({"currency": "USD", "amount": 100}, result.digest)

Protocols:

- ``ContentHasher`` — canonicalize + hash structured data
- ``SealAuthority`` — sign content hashes (host-provided)

The multi-party sealing workflow / attestation registry runtime is shipped
separately under commercial license.
"""

# Reference implementation
from .hasher import SHA256Hasher, generate_display_reference, generate_seal_id

# Protocols
from .protocols import ContentHasher, SealAuthority

# Types
from .types import ContentHash, SealPayload, SealResult, VerificationResult

__all__ = [
    # Reference implementation
    "SHA256Hasher",
    "generate_display_reference",
    "generate_seal_id",
    # Protocols
    "ContentHasher",
    "SealAuthority",
    # Types
    "ContentHash",
    "SealPayload",
    "SealResult",
    "VerificationResult",
]
