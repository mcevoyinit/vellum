"""
Tests for vellum.middleware
============================

Idempotency, rate limiting, and retry primitives.
Protocol conformance, in-memory implementations, edge cases.
"""

import time
from typing import Any, Dict

import pytest

from vellum.middleware import (
    IdempotencyResult,
    IdempotencyStore,
    InMemoryIdempotencyStore,
    InMemoryRateLimiter,
    RateLimitConfig,
    RateLimitResult,
    RateLimiter,
    RetryExecutor,
    RetryPolicy,
    RetryResult,
    SimpleRetryExecutor,
)


# ======================================================================
# Protocol conformance
# ======================================================================


class TestProtocolConformance:

    def test_memory_store_is_idempotency_store(self) -> None:
        assert isinstance(InMemoryIdempotencyStore(), IdempotencyStore)

    def test_memory_limiter_is_rate_limiter(self) -> None:
        limiter = InMemoryRateLimiter([RateLimitConfig("default", 100, 60.0)])
        assert isinstance(limiter, RateLimiter)

    def test_simple_retry_is_retry_executor(self) -> None:
        assert isinstance(SimpleRetryExecutor(), RetryExecutor)


# ======================================================================
# InMemoryIdempotencyStore
# ======================================================================


class TestIdempotencyStore:

    def setup_method(self) -> None:
        self.store = InMemoryIdempotencyStore()

    def test_first_check_not_duplicate(self) -> None:
        result = self.store.check("key-1")
        assert not result.is_duplicate
        assert result.idempotency_key == "key-1"

    def test_lock_succeeds_first_time(self) -> None:
        assert self.store.lock("key-1")

    def test_lock_fails_second_time(self) -> None:
        self.store.lock("key-1")
        assert not self.store.lock("key-1")

    def test_check_during_processing_is_duplicate(self) -> None:
        self.store.lock("key-1")
        result = self.store.check("key-1")
        assert result.is_duplicate
        assert result.error  # Has error message about processing

    def test_complete_stores_response(self) -> None:
        self.store.lock("key-1")
        self.store.complete("key-1", {"status": "ok"})
        result = self.store.check("key-1")
        assert result.is_duplicate
        assert result.cached_response == {"status": "ok"}
        assert not result.error

    def test_complete_without_lock(self) -> None:
        """Complete should work even without prior lock."""
        self.store.complete("key-1", {"status": "ok"})
        result = self.store.check("key-1")
        assert result.is_duplicate
        assert result.cached_response == {"status": "ok"}

    def test_different_keys_independent(self) -> None:
        self.store.lock("key-1")
        self.store.complete("key-1", "response-1")
        assert self.store.lock("key-2")
        result = self.store.check("key-2")
        assert result.is_duplicate  # Locked, in processing

    def test_lock_after_complete_fails(self) -> None:
        self.store.complete("key-1", "done")
        assert not self.store.lock("key-1")


# ======================================================================
# InMemoryRateLimiter
# ======================================================================


class TestRateLimiter:

    def test_first_request_allowed(self) -> None:
        limiter = InMemoryRateLimiter([RateLimitConfig("api", 10, 60.0)])
        result = limiter.check("ip-1", tier="api")
        assert result.allowed
        assert result.tier == "api"
        assert result.limit == 10

    def test_unknown_tier_always_allowed(self) -> None:
        limiter = InMemoryRateLimiter([RateLimitConfig("api", 10, 60.0)])
        result = limiter.check("ip-1", tier="nonexistent")
        assert result.allowed

    def test_exhaust_limit(self) -> None:
        limiter = InMemoryRateLimiter([RateLimitConfig("api", 3, 60.0)])
        for _ in range(3):
            result = limiter.check("ip-1", tier="api")
            assert result.allowed
        result = limiter.check("ip-1", tier="api")
        assert not result.allowed
        assert result.retry_after > 0

    def test_different_identities_independent(self) -> None:
        limiter = InMemoryRateLimiter([RateLimitConfig("api", 1, 60.0)])
        assert limiter.check("ip-1", tier="api").allowed
        # ip-1 is now exhausted
        assert not limiter.check("ip-1", tier="api").allowed
        # ip-2 should still be fine
        assert limiter.check("ip-2", tier="api").allowed

    def test_remaining_decreases(self) -> None:
        limiter = InMemoryRateLimiter([RateLimitConfig("api", 5, 60.0)])
        r1 = limiter.check("ip-1", tier="api")
        r2 = limiter.check("ip-1", tier="api")
        assert r2.remaining < r1.remaining

    def test_multiple_tiers(self) -> None:
        limiter = InMemoryRateLimiter([
            RateLimitConfig("ip", 2, 60.0),
            RateLimitConfig("tenant", 100, 3600.0),
        ])
        # Exhaust IP tier
        limiter.check("ip-1", tier="ip")
        limiter.check("ip-1", tier="ip")
        assert not limiter.check("ip-1", tier="ip").allowed
        # Tenant tier should still be fine
        assert limiter.check("ip-1", tier="tenant").allowed


# ======================================================================
# SimpleRetryExecutor
# ======================================================================


class TestRetryExecutor:

    def setup_method(self) -> None:
        self.executor = SimpleRetryExecutor()

    def test_success_first_try(self) -> None:
        result = self.executor.execute(
            lambda: 42,
            RetryPolicy(max_retries=3, base_delay=0.001),
        )
        assert result.success
        assert result.attempts == 1
        assert result.result == 42

    def test_fails_then_succeeds(self) -> None:
        attempts = {"count": 0}

        def flaky():
            attempts["count"] += 1
            if attempts["count"] < 3:
                raise ValueError("Not yet")
            return "ok"

        result = self.executor.execute(
            flaky,
            RetryPolicy(max_retries=3, base_delay=0.001, max_delay=0.01),
        )
        assert result.success
        assert result.attempts == 3
        assert result.result == "ok"

    def test_exhausts_retries(self) -> None:
        def always_fail():
            raise RuntimeError("Boom")

        result = self.executor.execute(
            always_fail,
            RetryPolicy(max_retries=2, base_delay=0.001, max_delay=0.01),
        )
        assert not result.success
        assert result.attempts == 3  # 1 initial + 2 retries
        assert "Boom" in result.last_error

    def test_non_retryable_error_stops(self) -> None:
        def fail_type():
            raise TypeError("Wrong type")

        result = self.executor.execute(
            fail_type,
            RetryPolicy(
                max_retries=3,
                base_delay=0.001,
                retryable_errors=frozenset({"ValueError"}),
            ),
        )
        assert not result.success
        assert result.attempts == 1  # No retries for non-retryable

    def test_retryable_error_retries(self) -> None:
        attempts = {"count": 0}

        def fail_then_ok():
            attempts["count"] += 1
            if attempts["count"] < 2:
                raise ValueError("Retry me")
            return "done"

        result = self.executor.execute(
            fail_then_ok,
            RetryPolicy(
                max_retries=3,
                base_delay=0.001,
                retryable_errors=frozenset({"ValueError"}),
            ),
        )
        assert result.success
        assert result.attempts == 2

    def test_zero_retries_single_attempt(self) -> None:
        def fail():
            raise RuntimeError("Fail")

        result = self.executor.execute(
            fail,
            RetryPolicy(max_retries=0, base_delay=0.001),
        )
        assert not result.success
        assert result.attempts == 1


# ======================================================================
# Type defaults
# ======================================================================


class TestTypeDefaults:

    def test_idempotency_result_defaults(self) -> None:
        r = IdempotencyResult(is_duplicate=False)
        assert r.cached_response is None
        assert r.idempotency_key == ""
        assert r.error == ""

    def test_rate_limit_result_defaults(self) -> None:
        r = RateLimitResult(allowed=True)
        assert r.limit == 0
        assert r.remaining == 0
        assert r.retry_after == 0.0
        assert r.tier == ""

    def test_retry_policy_defaults(self) -> None:
        p = RetryPolicy()
        assert p.max_retries == 3
        assert p.base_delay == 1.0
        assert p.max_delay == 60.0
        assert p.backoff_factor == 2.0
        assert p.retryable_errors == frozenset()

    def test_retry_result_defaults(self) -> None:
        r = RetryResult(success=True, attempts=1)
        assert r.last_error == ""
        assert r.result is None
