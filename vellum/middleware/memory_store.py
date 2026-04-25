"""
In-Memory Middleware Implementations
=====================================

Reference implementations for idempotency, rate limiting, and retry.
All use pure stdlib — no Redis, no external dependencies.

These are suitable for testing, prototyping, and single-process
applications.  Production deployments should use distributed
implementations (Redis, DynamoDB, etc.).
"""

import random
import threading
import time
from typing import Any, Callable, Dict, List, Tuple

from .types import (
    IdempotencyResult,
    RateLimitConfig,
    RateLimitResult,
    RetryPolicy,
    RetryResult,
)


class InMemoryIdempotencyStore:
    """Thread-safe dict-based idempotency store.

    State machine: ``NOT_EXISTS`` → ``PROCESSING`` → ``COMPLETED``.

    Suitable for testing and single-process applications.  Does not
    support TTL expiration (entries persist for the lifetime of the
    store instance).
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._store: Dict[str, Dict[str, Any]] = {}

    def check(self, key: str) -> IdempotencyResult:
        """Check if a request with this key has been processed."""
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return IdempotencyResult(is_duplicate=False, idempotency_key=key)
            if entry["status"] == "COMPLETED":
                return IdempotencyResult(
                    is_duplicate=True,
                    cached_response=entry["response"],
                    idempotency_key=key,
                )
            # PROCESSING — treat as duplicate to prevent concurrent execution
            return IdempotencyResult(
                is_duplicate=True,
                idempotency_key=key,
                error="Request is currently being processed",
            )

    def lock(self, key: str, ttl_seconds: int = 60) -> bool:
        """Atomically claim this key for processing."""
        with self._lock:
            if key in self._store:
                return False
            self._store[key] = {"status": "PROCESSING", "response": None}
            return True

    def complete(self, key: str, response: Any, ttl_seconds: int = 86400) -> None:
        """Store the final response for a completed request."""
        with self._lock:
            self._store[key] = {"status": "COMPLETED", "response": response}


class InMemoryRateLimiter:
    """Token bucket rate limiter.  No Redis needed.

    Each ``(identity, tier)`` pair gets its own token bucket.  Tokens
    refill linearly over the configured window.

    Args:
        configs: List of ``RateLimitConfig`` defining tiers.
    """

    def __init__(self, configs: List[RateLimitConfig]) -> None:
        self._configs: Dict[str, RateLimitConfig] = {c.tier: c for c in configs}
        self._lock = threading.Lock()
        # (identity, tier) → (tokens_remaining, last_refill_time)
        self._buckets: Dict[Tuple[str, str], Tuple[float, float]] = {}

    def check(self, identity: str, tier: str = "default") -> RateLimitResult:
        """Check if the identity is within rate limits."""
        config = self._configs.get(tier)
        if config is None:
            return RateLimitResult(allowed=True, tier=tier)

        with self._lock:
            now = time.monotonic()
            bucket_key = (identity, tier)
            tokens, last_refill = self._buckets.get(
                bucket_key, (float(config.max_requests), now)
            )

            # Refill tokens based on elapsed time
            elapsed = now - last_refill
            refill_rate = config.max_requests / config.window_seconds
            tokens = min(config.max_requests, tokens + elapsed * refill_rate)

            if tokens >= 1.0:
                tokens -= 1.0
                self._buckets[bucket_key] = (tokens, now)
                return RateLimitResult(
                    allowed=True,
                    limit=config.max_requests,
                    remaining=int(tokens),
                    tier=tier,
                )

            retry_after = (1.0 - tokens) / refill_rate
            self._buckets[bucket_key] = (tokens, now)
            return RateLimitResult(
                allowed=False,
                limit=config.max_requests,
                remaining=0,
                retry_after=round(retry_after, 2),
                tier=tier,
            )


class SimpleRetryExecutor:
    """Exponential backoff retry with jitter.

    Executes an operation up to ``max_retries + 1`` times.  On failure,
    waits ``base_delay * backoff_factor^attempt`` seconds (capped at
    ``max_delay``), with random jitter to prevent thundering herd.
    """

    def execute(
        self, operation: Callable[[], Any], policy: RetryPolicy
    ) -> RetryResult:
        """Execute with retries per the policy."""
        last_error = ""
        for attempt in range(1, policy.max_retries + 2):  # +2: 1-indexed, includes initial
            try:
                result = operation()
                return RetryResult(
                    success=True,
                    attempts=attempt,
                    result=result,
                )
            except Exception as exc:
                error_type = type(exc).__name__
                last_error = str(exc)

                # Check if this error type is retryable
                if (
                    policy.retryable_errors
                    and error_type not in policy.retryable_errors
                ):
                    return RetryResult(
                        success=False,
                        attempts=attempt,
                        last_error=last_error,
                    )

                # If we've exhausted retries, return failure
                if attempt > policy.max_retries:
                    return RetryResult(
                        success=False,
                        attempts=attempt,
                        last_error=last_error,
                    )

                # Calculate delay with jitter
                delay = min(
                    policy.base_delay * (policy.backoff_factor ** (attempt - 1)),
                    policy.max_delay,
                )
                jitter = delay * 0.1 * random.random()
                time.sleep(delay + jitter)

        # Should not reach here, but satisfy type checker
        return RetryResult(success=False, attempts=policy.max_retries + 1, last_error=last_error)
