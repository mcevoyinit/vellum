"""
Middleware Protocols
====================

Abstract interfaces for idempotency, rate limiting, and retry.

Implementations handle the actual storage and enforcement strategy.
Vellum ships in-memory reference implementations; host applications
provide Redis-backed, DynamoDB-backed, or other production stores.
"""

from typing import Any, Callable, Protocol, runtime_checkable

from .types import IdempotencyResult, RateLimitResult, RetryPolicy, RetryResult


@runtime_checkable
class IdempotencyStore(Protocol):
    """Store and retrieve idempotency state for request deduplication.

    The contract:
        - ``check`` returns whether a key has been seen before.
        - ``lock`` atomically claims a key for processing (returns
          ``True`` on success, ``False`` if already locked).
        - ``complete`` stores the final response for future lookups.

    Implementations: Redis (SETNX), DynamoDB (conditional put),
    in-memory (dict).
    """

    def check(self, key: str) -> IdempotencyResult:
        """Check if a request with this key has been processed.

        Args:
            key: The idempotency key (typically from a request header).

        Returns:
            ``IdempotencyResult`` with ``is_duplicate=True`` and the
            cached response if the key was previously completed.
        """
        ...

    def lock(self, key: str, ttl_seconds: int = 60) -> bool:
        """Atomically claim this key for processing.

        Args:
            key: The idempotency key to lock.
            ttl_seconds: Lock TTL to prevent stuck processing.

        Returns:
            ``True`` if the lock was acquired, ``False`` if the key
            is already locked or completed.
        """
        ...

    def complete(self, key: str, response: Any, ttl_seconds: int = 86400) -> None:
        """Store the final response for a completed request.

        Args:
            key: The idempotency key.
            response: The response to cache for future duplicate requests.
            ttl_seconds: How long to retain the completed response.
        """
        ...


@runtime_checkable
class RateLimiter(Protocol):
    """Check and enforce rate limits.

    Implementations: Redis sliding window, in-memory token bucket,
    distributed counter.

    The contract:
        - ``check`` evaluates whether the identity has capacity
          in the given tier.
        - ``check`` must be safe to call concurrently.
    """

    def check(self, identity: str, tier: str = "default") -> RateLimitResult:
        """Check if the identity is within rate limits for the tier.

        Args:
            identity: The entity being rate-limited (IP, tenant ID,
                API key, etc.).
            tier: The rate limit tier to evaluate.

        Returns:
            ``RateLimitResult`` indicating whether the request is
            allowed and how much capacity remains.
        """
        ...


@runtime_checkable
class RetryExecutor(Protocol):
    """Execute operations with retry logic.

    Implementations: simple backoff, circuit breaker, queue-based.

    The contract:
        - ``execute`` calls the operation up to ``policy.max_retries + 1``
          times with backoff delays between failures.
        - ``execute`` must not swallow exceptions from non-retryable errors.
    """

    def execute(
        self, operation: Callable[[], Any], policy: RetryPolicy
    ) -> RetryResult:
        """Execute an operation with retries according to the policy.

        Args:
            operation: A zero-argument callable to execute.
            policy: Retry configuration (max attempts, delays, etc.).

        Returns:
            ``RetryResult`` with success status and attempt count.
        """
        ...
