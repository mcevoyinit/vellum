"""
Persistence Protocols
=====================

Abstract interfaces for the dynamic persistence pipeline.

Implementations handle the actual type resolution, ID generation,
validation, and storage. The DynamicPipeline delegates all domain-specific
and I/O operations to these protocols.

Pattern follows ``vellum.negotiation.proposal_store.ProposalStore``.
"""

from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from .types import PersistResult, TypeResolution, ValidationResult


@runtime_checkable
class TypeResolver(Protocol):
    """Resolves JSON payloads to registered model types.

    Implementations may use model introspection, JSON Schema matching,
    explicit ``type`` field lookup, or any other detection strategy.
    """

    def resolve(self, payload: Dict[str, Any]) -> TypeResolution:
        """Detect the model type from a payload's structure or fields.

        Returns a ``TypeResolution`` with the matched model name and
        confidence score.  Returns ``TypeResolution(model_name=None)``
        if no match is found.
        """
        ...

    def validate(
        self, payload: Dict[str, Any], model_name: str
    ) -> ValidationResult:
        """Validate a payload against a specific model type.

        Checks that required fields are present and values conform to
        the model's constraints.
        """
        ...

    def list_types(self) -> List[str]:
        """Return the names of all registered model types."""
        ...


@runtime_checkable
class IDGenerator(Protocol):
    """Generates unique record identifiers.

    Implementations control the ID format — UUIDs, domain-prefixed IDs,
    sequential counters, etc.  The pipeline calls this when a payload
    does not already contain an ``id`` field.
    """

    def generate(self, model_name: str, payload: Dict[str, Any]) -> str:
        """Generate a unique ID for a record of the given type."""
        ...


@runtime_checkable
class ValidationHook(Protocol):
    """Domain-specific validation that runs before persistence.

    Multiple hooks can be registered on a pipeline.  All must pass
    for the operation to proceed.  Use this to enforce business rules
    such as access control, immutability constraints, or state-machine
    invariants.

    The ``context`` dict carries caller-provided metadata (actor info,
    auth tokens, etc.).  Vellum does not define its contents — host
    applications do.
    """

    def validate(
        self,
        record_id: str,
        model_name: str,
        payload: Dict[str, Any],
        operation: str,
        context: Dict[str, Any],
    ) -> ValidationResult:
        """Validate the operation.

        Args:
            record_id: The record being created or updated.
            model_name: Resolved model type name.
            payload: The record data.
            operation: ``"CREATE"`` or ``"UPDATE"``.
            context: Caller-provided metadata.

        Returns:
            ``ValidationResult`` — ``valid=True`` to allow, ``valid=False``
            with ``errors`` and optional ``error_code`` to block.
        """
        ...


@runtime_checkable
class PersistenceBackend(Protocol):
    """Backend that handles actual record storage and retrieval.

    Implementations wrap the concrete storage technology — SQL databases,
    document stores, graph databases, in-memory dicts, etc.  Serialization
    is the backend's responsibility, not the pipeline's.

    When ``DynamicPipeline`` is created without a backend (``backend=None``),
    the pipeline runs in validate-only mode — type resolution, ID generation,
    and validation hooks still execute, but no persistence occurs.
    """

    def persist(
        self,
        record_id: str,
        model_name: str,
        data: Dict[str, Any],
        operation: str,
    ) -> PersistResult:
        """Persist a record.

        Args:
            record_id: Unique record identifier.
            model_name: Resolved model type name.
            data: The record data as a dict.
            operation: ``"CREATE"`` or ``"UPDATE"``.

        Returns:
            ``PersistResult`` indicating success or failure.
        """
        ...

    def fetch(
        self, record_id: str, model_name: str
    ) -> Optional[Dict[str, Any]]:
        """Fetch a record by ID.  Returns ``None`` if not found."""
        ...

    def query(
        self, model_name: str, filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Query records by type and filter criteria."""
        ...
