"""
Dynamic Pipeline
================

Domain-agnostic persistence pipeline.

Orchestrates: extract → resolve type → normalize → generate ID → validate
→ persist.  Pure orchestration — all I/O is delegated to Protocol
implementations provided at construction time.

Usage::

    from vellum.persistence import DynamicPipeline, SimpleTypeResolver

    resolver = SimpleTypeResolver()
    resolver.register("Invoice", {"amount", "currency", "vendor"})

    pipeline = DynamicPipeline(type_resolver=resolver, backend=my_backend)
    result = pipeline.process({"amount": 100, "currency": "USD", "vendor": "Acme"})
"""

import json
import time
import uuid
from typing import Any, Callable, Dict, List, Optional

from .protocols import IDGenerator, PersistenceBackend, TypeResolver, ValidationHook
from .types import BatchResult, PipelineResult, PersistResult, ValidationResult


class _DefaultIDGenerator:
    """Fallback ID generator using UUID4."""

    def generate(self, model_name: str, payload: Dict[str, Any]) -> str:
        short = uuid.uuid4().hex[:12]
        prefix = model_name.upper()[:8] if model_name else "REC"
        return f"{prefix}-{short}"


class DynamicPipeline:
    """Domain-agnostic persistence pipeline.

    All domain-specific logic is injected via Protocol implementations.
    The pipeline itself contains zero I/O and zero domain knowledge.

    Args:
        type_resolver: Resolves payloads to registered model types.
        backend: Handles actual storage.  ``None`` for validate-only mode.
        id_generator: Generates record IDs.  Falls back to UUID if ``None``.
        validation_hooks: Domain-specific validation rules.  All must pass.
        normalizer: Optional callable ``(data, model_name) -> data`` for
            pre-processing before validation (e.g. enum normalization).
    """

    def __init__(
        self,
        type_resolver: TypeResolver,
        backend: Optional[PersistenceBackend] = None,
        id_generator: Optional[IDGenerator] = None,
        validation_hooks: Optional[List[ValidationHook]] = None,
        normalizer: Optional[Callable[[Dict[str, Any], str], Dict[str, Any]]] = None,
    ) -> None:
        self.type_resolver = type_resolver
        self.backend = backend
        self.id_generator = id_generator or _DefaultIDGenerator()
        self.validation_hooks = validation_hooks or []
        self.normalizer = normalizer

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process(
        self,
        payload: Any,
        operation: str = "CREATE",
        context: Optional[Dict[str, Any]] = None,
    ) -> PipelineResult:
        """Process a single payload through the full pipeline.

        Steps:
            1. Extract data (unwrap wrapper formats)
            2. Resolve type
            3. Normalize (if normalizer provided)
            4. Generate or verify ID
            5. Run validation hooks (all must pass)
            6. Persist (if backend provided)

        Args:
            payload: Raw payload (dict, JSON string, or wrapper format).
            operation: ``"CREATE"`` or ``"UPDATE"``.
            context: Caller-provided metadata forwarded to validation hooks.

        Returns:
            ``PipelineResult`` with success/failure and all intermediate results.
        """
        start = time.monotonic()
        ctx = context or {}

        # Step 1: Extract
        data = self.extract_data(payload)
        if not isinstance(data, dict) or not data:
            return PipelineResult(
                success=False,
                operation=operation,
                error="Empty or invalid payload after extraction",
                duration_ms=_elapsed(start),
            )

        # Step 2: Resolve type
        resolution = self.type_resolver.resolve(data)
        if not resolution.success:
            return PipelineResult(
                success=False,
                operation=operation,
                type_resolution=resolution,
                error=resolution.error or "Could not resolve model type",
                duration_ms=_elapsed(start),
            )

        model_name = resolution.model_name

        # Step 3: Normalize (optional)
        if self.normalizer and model_name:
            data = self.normalizer(data, model_name)

        # Step 4: ID generation / verification
        record_id = data.get("id")
        if operation == "CREATE":
            if record_id:
                return PipelineResult(
                    success=False,
                    operation=operation,
                    model_name=model_name,
                    type_resolution=resolution,
                    error="CREATE operation should not include 'id' field",
                    duration_ms=_elapsed(start),
                )
            record_id = self.id_generator.generate(model_name or "", data)
            data["id"] = record_id
        elif operation == "UPDATE":
            if not record_id:
                return PipelineResult(
                    success=False,
                    operation=operation,
                    model_name=model_name,
                    type_resolution=resolution,
                    error="UPDATE operation requires 'id' field",
                    duration_ms=_elapsed(start),
                )

        # Step 5: Validation hooks
        for hook in self.validation_hooks:
            hook_result = hook.validate(
                record_id=record_id or "",
                model_name=model_name or "",
                payload=data,
                operation=operation,
                context=ctx,
            )
            if not hook_result.valid:
                return PipelineResult(
                    success=False,
                    record_id=record_id,
                    model_name=model_name,
                    operation=operation,
                    type_resolution=resolution,
                    validation=hook_result,
                    error="; ".join(hook_result.errors) if hook_result.errors else "Validation failed",
                    duration_ms=_elapsed(start),
                )

        # Step 6: Persist
        persist_result: Optional[PersistResult] = None
        if self.backend is not None:
            persist_result = self.backend.persist(
                record_id=record_id or "",
                model_name=model_name or "",
                data=data,
                operation=operation,
            )
            if not persist_result.success:
                return PipelineResult(
                    success=False,
                    record_id=record_id,
                    model_name=model_name,
                    operation=operation,
                    type_resolution=resolution,
                    persist_result=persist_result,
                    error=persist_result.error or "Persistence failed",
                    duration_ms=_elapsed(start),
                )

        return PipelineResult(
            success=True,
            record_id=record_id,
            model_name=model_name,
            operation=operation,
            type_resolution=resolution,
            validation=ValidationResult(valid=True),
            persist_result=persist_result,
            duration_ms=_elapsed(start),
        )

    def process_batch(
        self,
        payloads: List[Any],
        operation: str = "CREATE",
        context: Optional[Dict[str, Any]] = None,
    ) -> BatchResult:
        """Process multiple payloads.  Returns per-item results.

        Each payload is processed independently — a failure in one item
        does not abort the batch.
        """
        results: List[PipelineResult] = []
        for item in payloads:
            results.append(self.process(item, operation=operation, context=context))

        succeeded = sum(1 for r in results if r.success)
        return BatchResult(
            results=results,
            total=len(results),
            succeeded=succeeded,
            failed=len(results) - succeeded,
        )

    def validate_only(self, payload: Any) -> ValidationResult:
        """Validate a payload without persisting.

        Runs type resolution and validation hooks but skips ID generation
        and persistence.
        """
        data = self.extract_data(payload)
        if not isinstance(data, dict) or not data:
            return ValidationResult(valid=False, errors=["Empty or invalid payload"])

        resolution = self.type_resolver.resolve(data)
        if not resolution.success:
            return ValidationResult(
                valid=False,
                errors=[resolution.error or "No matching type found"],
            )

        model_name = resolution.model_name or ""

        # Type-level validation
        type_validation = self.type_resolver.validate(data, model_name)
        if not type_validation.valid:
            return type_validation

        # Hook validation (with placeholder ID since no record exists yet)
        for hook in self.validation_hooks:
            hook_result = hook.validate(
                record_id=data.get("id", ""),
                model_name=model_name,
                payload=data,
                operation="VALIDATE",
                context={},
            )
            if not hook_result.valid:
                return hook_result

        return ValidationResult(valid=True)

    @staticmethod
    def extract_data(payload: Any) -> Dict[str, Any]:
        """Extract record data from various wrapper formats.

        Supports:
            - Plain dict (pass-through)
            - JSON string (parsed)
            - Mutation wrapper format (``query``/``variables``/``input``)
            - Nested ``data`` or ``record`` wrappers
        """
        # JSON string
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except (json.JSONDecodeError, ValueError):
                return {}

        if not isinstance(payload, dict):
            return {}

        # Mutation wrapper format: {query, variables: {input: [...]}}
        if "query" in payload and "variables" in payload:
            variables = payload["variables"]
            if isinstance(variables, dict):
                inp = variables.get("input")
                if isinstance(inp, list) and len(inp) > 0:
                    return inp[0] if isinstance(inp[0], dict) else {}
                if isinstance(inp, dict):
                    return inp
                # Check other variable keys
                for val in variables.values():
                    if isinstance(val, dict):
                        return val
                    if isinstance(val, list) and len(val) > 0 and isinstance(val[0], dict):
                        return val[0]

        # Nested data wrapper
        if "data" in payload and isinstance(payload["data"], dict):
            return payload["data"]

        # Nested record wrapper
        if "record" in payload and isinstance(payload["record"], dict):
            return payload["record"]

        return payload


def _elapsed(start: float) -> float:
    """Milliseconds since start."""
    return round((time.monotonic() - start) * 1000, 2)
