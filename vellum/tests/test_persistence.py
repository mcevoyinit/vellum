"""
Tests for vellum.persistence — dynamic persistence pipeline.

Covers: protocols, type resolver, pipeline, validation hooks, batch
processing, data extraction, and error paths.

All tests use in-memory test doubles — no external dependencies.
"""

import json
import uuid
from typing import Any, Dict, List, Optional

import pytest

from vellum.persistence import (
    BatchResult,
    DynamicPipeline,
    IDGenerator,
    PersistenceBackend,
    PersistResult,
    PipelineResult,
    SimpleTypeResolver,
    TypeResolution,
    TypeResolver,
    ValidationHook,
    ValidationResult,
)


# ======================================================================
# Test doubles
# ======================================================================


class InMemoryBackend:
    """Test double for PersistenceBackend."""

    def __init__(self, fail_on_persist: bool = False):
        self.store: Dict[str, Dict[str, Any]] = {}
        self.persist_calls: List[tuple] = []
        self._fail = fail_on_persist

    def persist(
        self, record_id: str, model_name: str, data: Dict[str, Any], operation: str
    ) -> PersistResult:
        self.persist_calls.append((record_id, model_name, data, operation))
        if self._fail:
            return PersistResult(success=False, error="Simulated backend failure")
        self.store[record_id] = {"model_name": model_name, "data": data}
        return PersistResult(success=True, record_id=record_id)

    def fetch(self, record_id: str, model_name: str) -> Optional[Dict[str, Any]]:
        entry = self.store.get(record_id)
        return entry["data"] if entry else None

    def query(self, model_name: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [
            e["data"]
            for e in self.store.values()
            if e["model_name"] == model_name
        ]


class CountingIDGenerator:
    """Deterministic ID generator for tests."""

    def __init__(self, prefix: str = "TEST"):
        self._counter = 0
        self._prefix = prefix

    def generate(self, model_name: str, payload: Dict[str, Any]) -> str:
        self._counter += 1
        return f"{self._prefix}-{model_name}-{self._counter:04d}"


class BlockingHook:
    """ValidationHook that always blocks."""

    def __init__(self, error_code: str = "BLOCKED"):
        self._code = error_code

    def validate(
        self, record_id: str, model_name: str, payload: Dict[str, Any],
        operation: str, context: Dict[str, Any],
    ) -> ValidationResult:
        return ValidationResult(
            valid=False,
            errors=[f"Blocked by {self._code}"],
            error_code=self._code,
        )


class PassingHook:
    """ValidationHook that always passes."""

    def __init__(self):
        self.calls: List[tuple] = []

    def validate(
        self, record_id: str, model_name: str, payload: Dict[str, Any],
        operation: str, context: Dict[str, Any],
    ) -> ValidationResult:
        self.calls.append((record_id, model_name, operation, context))
        return ValidationResult(valid=True)


# ======================================================================
# Fixtures
# ======================================================================


@pytest.fixture
def resolver():
    """Pre-configured SimpleTypeResolver with 3 types."""
    r = SimpleTypeResolver()
    r.register("Invoice", {"amount", "currency", "vendor"})
    r.register("Order", {"items", "customer", "total"}, optional_fields={"notes"})
    r.register("Member", {"name", "email"})
    return r


@pytest.fixture
def backend():
    return InMemoryBackend()


@pytest.fixture
def pipeline(resolver, backend):
    return DynamicPipeline(
        type_resolver=resolver,
        backend=backend,
        id_generator=CountingIDGenerator(),
    )


# ======================================================================
# Protocol conformance
# ======================================================================


class TestProtocolConformance:
    """Verify Protocol runtime checking works."""

    def test_simple_resolver_is_type_resolver(self):
        r = SimpleTypeResolver()
        assert isinstance(r, TypeResolver)

    def test_in_memory_backend_is_persistence_backend(self):
        b = InMemoryBackend()
        assert isinstance(b, PersistenceBackend)

    def test_counting_id_generator_is_id_generator(self):
        g = CountingIDGenerator()
        assert isinstance(g, IDGenerator)

    def test_passing_hook_is_validation_hook(self):
        h = PassingHook()
        assert isinstance(h, ValidationHook)

    def test_blocking_hook_is_validation_hook(self):
        h = BlockingHook()
        assert isinstance(h, ValidationHook)


# ======================================================================
# SimpleTypeResolver
# ======================================================================


class TestSimpleTypeResolver:

    def test_resolve_by_field_matching(self, resolver):
        result = resolver.resolve({"amount": 100, "currency": "USD", "vendor": "Acme"})
        assert result.success
        assert result.model_name == "Invoice"

    def test_resolve_by_explicit_type_field(self, resolver):
        result = resolver.resolve({"type": "Order", "items": [], "customer": "X", "total": 0})
        assert result.model_name == "Order"
        assert result.confidence == 1.0

    def test_resolve_by_model_type_field(self, resolver):
        result = resolver.resolve({"model_type": "Member", "name": "A", "email": "a@b.com"})
        assert result.model_name == "Member"

    def test_resolve_unknown_payload(self, resolver):
        result = resolver.resolve({"foo": "bar", "baz": 42})
        assert not result.success
        assert result.error is not None

    def test_resolve_empty_payload(self, resolver):
        result = resolver.resolve({})
        assert not result.success

    def test_validate_passes(self, resolver):
        v = resolver.validate({"amount": 1, "currency": "X", "vendor": "Y"}, "Invoice")
        assert v.valid

    def test_validate_missing_field(self, resolver):
        v = resolver.validate({"amount": 1, "currency": "X"}, "Invoice")
        assert not v.valid
        assert "vendor" in str(v.errors)

    def test_validate_unknown_type(self, resolver):
        v = resolver.validate({"a": 1}, "NonExistent")
        assert not v.valid

    def test_list_types(self, resolver):
        types = resolver.list_types()
        assert types == ["Invoice", "Member", "Order"]

    def test_resolve_with_optional_fields(self, resolver):
        # Should match Order even with optional "notes" field present
        result = resolver.resolve(
            {"items": ["a"], "customer": "X", "total": 50, "notes": "rush"}
        )
        assert result.model_name == "Order"

    def test_resolve_prefers_explicit_type_over_fields(self, resolver):
        # Explicit type field wins even if fields match another type
        result = resolver.resolve(
            {"type": "Member", "name": "A", "email": "a@b.com", "amount": 1, "currency": "X", "vendor": "Y"}
        )
        assert result.model_name == "Member"


# ======================================================================
# DynamicPipeline — happy path
# ======================================================================


class TestPipelineHappyPath:

    def test_create_single_record(self, pipeline, backend):
        result = pipeline.process({"amount": 100, "currency": "USD", "vendor": "Acme"})
        assert result.success
        assert result.model_name == "Invoice"
        assert result.record_id == "TEST-Invoice-0001"
        assert result.operation == "CREATE"
        assert len(backend.store) == 1

    def test_update_record(self, pipeline, backend):
        # Pre-seed a record
        backend.store["EXISTING-001"] = {"model_name": "Invoice", "data": {}}

        result = pipeline.process(
            {"id": "EXISTING-001", "amount": 200, "currency": "EUR", "vendor": "X"},
            operation="UPDATE",
        )
        assert result.success
        assert result.record_id == "EXISTING-001"
        assert result.operation == "UPDATE"

    def test_batch_create(self, pipeline):
        result = pipeline.process_batch([
            {"amount": 1, "currency": "A", "vendor": "V1"},
            {"amount": 2, "currency": "B", "vendor": "V2"},
            {"amount": 3, "currency": "C", "vendor": "V3"},
        ])
        assert isinstance(result, BatchResult)
        assert result.total == 3
        assert result.succeeded == 3
        assert result.failed == 0

    def test_validate_only(self, pipeline):
        v = pipeline.validate_only({"amount": 1, "currency": "X", "vendor": "Y"})
        assert v.valid

    def test_pipeline_without_backend(self, resolver):
        """Pipeline in validate-only mode (no backend)."""
        p = DynamicPipeline(type_resolver=resolver)
        result = p.process({"amount": 1, "currency": "X", "vendor": "Y"})
        assert result.success
        assert result.persist_result is None

    def test_pipeline_with_normalizer(self, resolver, backend):
        def upper_normalizer(data: Dict, model_name: str) -> Dict:
            return {k: v.upper() if isinstance(v, str) else v for k, v in data.items()}

        p = DynamicPipeline(
            type_resolver=resolver,
            backend=backend,
            normalizer=upper_normalizer,
            id_generator=CountingIDGenerator(),
        )
        result = p.process({"amount": 1, "currency": "usd", "vendor": "acme"})
        assert result.success
        stored = backend.store[result.record_id]["data"]
        assert stored["currency"] == "USD"
        assert stored["vendor"] == "ACME"

    def test_duration_is_set(self, pipeline):
        result = pipeline.process({"amount": 1, "currency": "X", "vendor": "Y"})
        assert result.duration_ms >= 0


# ======================================================================
# Validation hooks
# ======================================================================


class TestValidationHooks:

    def test_single_hook_passes(self, resolver, backend):
        hook = PassingHook()
        p = DynamicPipeline(
            type_resolver=resolver, backend=backend,
            validation_hooks=[hook], id_generator=CountingIDGenerator(),
        )
        result = p.process({"amount": 1, "currency": "X", "vendor": "Y"})
        assert result.success
        assert len(hook.calls) == 1

    def test_single_hook_blocks(self, resolver, backend):
        p = DynamicPipeline(
            type_resolver=resolver, backend=backend,
            validation_hooks=[BlockingHook("ACCESS_DENIED")],
            id_generator=CountingIDGenerator(),
        )
        result = p.process({"amount": 1, "currency": "X", "vendor": "Y"})
        assert not result.success
        assert result.validation is not None
        assert result.validation.error_code == "ACCESS_DENIED"
        assert len(backend.store) == 0  # Not persisted

    def test_multiple_hooks_all_pass(self, resolver, backend):
        h1, h2 = PassingHook(), PassingHook()
        p = DynamicPipeline(
            type_resolver=resolver, backend=backend,
            validation_hooks=[h1, h2], id_generator=CountingIDGenerator(),
        )
        result = p.process({"amount": 1, "currency": "X", "vendor": "Y"})
        assert result.success
        assert len(h1.calls) == 1
        assert len(h2.calls) == 1

    def test_first_hook_blocks_short_circuits(self, resolver, backend):
        h1 = BlockingHook("HOOK1_FAIL")
        h2 = PassingHook()
        p = DynamicPipeline(
            type_resolver=resolver, backend=backend,
            validation_hooks=[h1, h2], id_generator=CountingIDGenerator(),
        )
        result = p.process({"amount": 1, "currency": "X", "vendor": "Y"})
        assert not result.success
        assert len(h2.calls) == 0  # Second hook never called

    def test_context_forwarded_to_hooks(self, resolver, backend):
        hook = PassingHook()
        p = DynamicPipeline(
            type_resolver=resolver, backend=backend,
            validation_hooks=[hook], id_generator=CountingIDGenerator(),
        )
        p.process(
            {"amount": 1, "currency": "X", "vendor": "Y"},
            context={"actor": "user-123"},
        )
        assert hook.calls[0][3] == {"actor": "user-123"}


# ======================================================================
# Data extraction
# ======================================================================


class TestDataExtraction:

    def test_plain_dict(self):
        assert DynamicPipeline.extract_data({"a": 1}) == {"a": 1}

    def test_json_string(self):
        result = DynamicPipeline.extract_data('{"a": 1}')
        assert result == {"a": 1}

    def test_invalid_json_string(self):
        assert DynamicPipeline.extract_data("not json") == {}

    def test_graphql_mutation_list_input(self):
        payload = {
            "query": "mutation { addInvoice($input: ...) }",
            "variables": {"input": [{"amount": 100}]},
        }
        assert DynamicPipeline.extract_data(payload) == {"amount": 100}

    def test_graphql_mutation_dict_input(self):
        payload = {
            "query": "mutation { ... }",
            "variables": {"input": {"amount": 200}},
        }
        assert DynamicPipeline.extract_data(payload) == {"amount": 200}

    def test_nested_data_wrapper(self):
        assert DynamicPipeline.extract_data({"data": {"x": 1}}) == {"x": 1}

    def test_nested_record_wrapper(self):
        assert DynamicPipeline.extract_data({"record": {"y": 2}}) == {"y": 2}

    def test_non_dict_payload(self):
        assert DynamicPipeline.extract_data(42) == {}
        assert DynamicPipeline.extract_data(None) == {}


# ======================================================================
# Error paths
# ======================================================================


class TestErrorPaths:

    def test_unresolvable_type(self, pipeline):
        result = pipeline.process({"unknown_field": "value"})
        assert not result.success
        assert "resolve" in result.error.lower() or "matching" in result.error.lower()

    def test_backend_persist_failure(self, resolver):
        failing_backend = InMemoryBackend(fail_on_persist=True)
        p = DynamicPipeline(
            type_resolver=resolver, backend=failing_backend,
            id_generator=CountingIDGenerator(),
        )
        result = p.process({"amount": 1, "currency": "X", "vendor": "Y"})
        assert not result.success
        assert "backend" in result.error.lower() or "persist" in result.error.lower()

    def test_empty_payload(self, pipeline):
        result = pipeline.process({})
        assert not result.success

    def test_create_with_id_rejected(self, pipeline):
        result = pipeline.process({"id": "EXISTING", "amount": 1, "currency": "X", "vendor": "Y"})
        assert not result.success
        assert "CREATE" in result.error

    def test_update_without_id_rejected(self, pipeline):
        result = pipeline.process(
            {"amount": 1, "currency": "X", "vendor": "Y"},
            operation="UPDATE",
        )
        assert not result.success
        assert "UPDATE" in result.error

    def test_batch_with_mixed_results(self, resolver):
        p = DynamicPipeline(
            type_resolver=resolver,
            id_generator=CountingIDGenerator(),
            backend=InMemoryBackend(),
        )
        batch = p.process_batch([
            {"amount": 1, "currency": "X", "vendor": "Y"},  # Valid
            {"unknown": "nope"},                              # Invalid
            {"name": "A", "email": "a@b"},                   # Valid (Member)
        ])
        assert batch.total == 3
        assert batch.succeeded == 2
        assert batch.failed == 1

    def test_validate_only_unknown_type(self, pipeline):
        v = pipeline.validate_only({"zzz": 123})
        assert not v.valid


# ======================================================================
# Type result dataclasses
# ======================================================================


class TestTypes:

    def test_type_resolution_success_property(self):
        r = TypeResolution(model_name="X", confidence=0.9)
        assert r.success

    def test_type_resolution_failure_property(self):
        r = TypeResolution(error="no match")
        assert not r.success

    def test_validation_result_success_property(self):
        assert ValidationResult(valid=True).success
        assert not ValidationResult(valid=False).success

    def test_pipeline_result_fields(self):
        r = PipelineResult(success=True, record_id="R1", model_name="M")
        assert r.record_id == "R1"
        assert r.duration_ms == 0.0

    def test_batch_result_defaults(self):
        b = BatchResult()
        assert b.total == 0
        assert b.results == []
