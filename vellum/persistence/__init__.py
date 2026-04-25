"""
Vellum Persistence
==================

Domain-agnostic dynamic persistence pipeline.

Define how your application stores and retrieves records by implementing
the Protocol interfaces.  The ``DynamicPipeline`` orchestrates the flow:
extract → resolve type → normalize → generate ID → validate → persist.

Quickstart::

    from vellum.persistence import DynamicPipeline, SimpleTypeResolver

    resolver = SimpleTypeResolver()
    resolver.register("Invoice", {"amount", "currency", "vendor"})
    resolver.register("Order", {"items", "customer", "total"})

    pipeline = DynamicPipeline(type_resolver=resolver, backend=my_backend)
    result = pipeline.process({"amount": 100, "currency": "USD", "vendor": "Acme"})
    assert result.success
    assert result.model_name == "Invoice"

Protocols:

- ``TypeResolver`` — resolve payloads to registered model types
- ``IDGenerator`` — generate unique record identifiers
- ``ValidationHook`` — domain-specific pre-persist validation
- ``PersistenceBackend`` — actual record storage and retrieval

Reference implementation:

- ``SimpleTypeResolver`` — field-set matching, no external dependencies
"""

# Pipeline
from .pipeline import DynamicPipeline

# Protocols
from .protocols import (
    IDGenerator,
    PersistenceBackend,
    TypeResolver,
    ValidationHook,
)

# Reference implementation
from .simple_resolver import SimpleTypeResolver

# Types
from .types import (
    BatchResult,
    PersistResult,
    PipelineResult,
    TypeResolution,
    ValidationResult,
)

__all__ = [
    # Pipeline
    "DynamicPipeline",
    # Protocols
    "IDGenerator",
    "PersistenceBackend",
    "TypeResolver",
    "ValidationHook",
    # Reference implementation
    "SimpleTypeResolver",
    # Types
    "BatchResult",
    "PersistResult",
    "PipelineResult",
    "TypeResolution",
    "ValidationResult",
]
