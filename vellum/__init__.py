"""
Vellum
======

Domain-agnostic multi-party negotiation, persistence, and integrity engine.

A pure functional core for field-level propose-agree workflows,
dynamic record persistence, content integrity sealing, and
config-driven state machines.  Any vertical can import and extend
these primitives by implementing the Protocol interfaces.

Modules:
    negotiation  - Multi-party field-level negotiation engine
    persistence  - Dynamic type-aware persistence pipeline
    sealing      - Content integrity (canonicalization, hashing, seal protocol)
    statemachine - Config-driven finite state machine
    identity     - Actor context, RBAC, permission checking
    middleware   - Idempotency, rate limiting, retry logic
    events       - Audit logging, lifecycle event sourcing
    core         - Shared utilities (logging)
"""

__version__ = "0.1.0"
