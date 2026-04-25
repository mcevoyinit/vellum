"""
Middleware Types
================

Data structures for idempotency checking, rate limiting, and retry logic.

All types are pure dataclasses with no external dependencies.
"""

from dataclasses import dataclass, field
from typing import Any, FrozenSet


# ======================================================================
# Idempotency
# ======================================================================


@dataclass
class IdempotencyResult:
    """Result of an idempotency check.

    Attributes:
        is_duplicate: ``True`` if this request has already been
            processed (the cached response should be returned).
        cached_response: The stored response from the original
            request, if available.
        idempotency_key: The key used for deduplication.
        error: Error message if the check itself failed.
    """

    is_duplicate: bool
    cached_response: Any = None
    idempotency_key: str = ""
    error: str = ""


# ======================================================================
# Rate Limiting
# ======================================================================


@dataclass
class RateLimitConfig:
    """Configuration for a single rate limit tier.

    Attributes:
        tier: Name of the tier (e.g. ``"ip"``, ``"tenant"``).
        max_requests: Maximum requests allowed in the window.
        window_seconds: Time window in seconds.
    """

    tier: str
    max_requests: int
    window_seconds: float


@dataclass
class RateLimitResult:
    """Result of a rate limit check.

    Attributes:
        allowed: Whether the request is within limits.
        limit: Maximum requests in the current window.
        remaining: Requests remaining before throttling.
        retry_after: Seconds to wait before retrying (0 if allowed).
        tier: The tier that was evaluated.
    """

    allowed: bool
    limit: int = 0
    remaining: int = 0
    retry_after: float = 0.0
    tier: str = ""


# ======================================================================
# Retry
# ======================================================================


@dataclass
class RetryPolicy:
    """Configuration for retry behavior.

    Attributes:
        max_retries: Maximum number of retry attempts.
        base_delay: Initial delay in seconds before the first retry.
        max_delay: Maximum delay between retries (caps backoff).
        backoff_factor: Multiplier applied to delay after each attempt.
        retryable_errors: Set of error type names that should be
            retried.  If empty, all errors are retried.
    """

    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    backoff_factor: float = 2.0
    retryable_errors: FrozenSet[str] = field(default_factory=frozenset)


@dataclass
class RetryResult:
    """Outcome of a retried operation.

    Attributes:
        success: Whether the operation eventually succeeded.
        attempts: Total number of attempts (1 = succeeded first try).
        last_error: Error message from the last failed attempt.
        result: The return value of the operation on success.
    """

    success: bool
    attempts: int
    last_error: str = ""
    result: Any = None
