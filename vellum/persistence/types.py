"""
Persistence Types
=================

Data classes for the dynamic persistence pipeline.

These types are shared between the DynamicPipeline (orchestration) and
Protocol implementations (backends, resolvers, hooks).
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class TypeResolution:
    """Result of resolving a payload to a registered model type."""

    model_name: Optional[str] = None
    confidence: float = 0.0
    matched_fields: List[str] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.model_name is not None


@dataclass
class ValidationResult:
    """Result of a validation operation (type validation or hook validation)."""

    valid: bool
    errors: List[str] = field(default_factory=list)
    error_code: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.valid


@dataclass
class PersistResult:
    """Result of a persist or update operation."""

    success: bool
    record_id: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineResult:
    """Result of the full pipeline execution for a single payload."""

    success: bool
    record_id: Optional[str] = None
    model_name: Optional[str] = None
    operation: str = "CREATE"
    type_resolution: Optional[TypeResolution] = None
    validation: Optional[ValidationResult] = None
    persist_result: Optional[PersistResult] = None
    error: Optional[str] = None
    duration_ms: float = 0.0


@dataclass
class BatchResult:
    """Result of batch pipeline processing."""

    results: List[PipelineResult] = field(default_factory=list)
    total: int = 0
    succeeded: int = 0
    failed: int = 0
