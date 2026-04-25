"""
Vellum Middleware
=================

Idempotency, rate limiting, and retry primitives.

Provides Protocol interfaces and in-memory reference implementations
for the three core API middleware concerns: request deduplication,
request throttling, and operation retry with backoff.

Quickstart::

    from vellum.middleware import (
        InMemoryIdempotencyStore,
        InMemoryRateLimiter,
        RateLimitConfig,
        SimpleRetryExecutor,
        RetryPolicy,
    )

    # Idempotency
    store = InMemoryIdempotencyStore()
    if store.lock("req-123"):
        result = do_work()
        store.complete("req-123", result)

    # Rate limiting
    limiter = InMemoryRateLimiter([RateLimitConfig("api", 100, 60.0)])
    check = limiter.check("192.168.1.1", tier="api")
    assert check.allowed

    # Retry
    executor = SimpleRetryExecutor()
    result = executor.execute(flaky_operation, RetryPolicy(max_retries=3))

Protocols:

- ``IdempotencyStore`` — request deduplication state
- ``RateLimiter`` — request throttling
- ``RetryExecutor`` — operation retry with backoff
"""

# Reference implementations
from .memory_store import (
    InMemoryIdempotencyStore,
    InMemoryRateLimiter,
    SimpleRetryExecutor,
)

# Protocols
from .protocols import IdempotencyStore, RateLimiter, RetryExecutor

# Types
from .types import (
    IdempotencyResult,
    RateLimitConfig,
    RateLimitResult,
    RetryPolicy,
    RetryResult,
)

__all__ = [
    # Reference implementations
    "InMemoryIdempotencyStore",
    "InMemoryRateLimiter",
    "SimpleRetryExecutor",
    # Protocols
    "IdempotencyStore",
    "RateLimiter",
    "RetryExecutor",
    # Types
    "IdempotencyResult",
    "RateLimitConfig",
    "RateLimitResult",
    "RetryPolicy",
    "RetryResult",
]
