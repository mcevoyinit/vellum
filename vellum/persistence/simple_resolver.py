"""
Simple Type Resolver
====================

Reference implementation of ``TypeResolver`` using field-set matching.

No external dependencies.  Register model
types as ``{name: required_fields}`` dicts and resolve payloads by
checking which registered type's required fields are all present.
"""

from typing import Any, Dict, FrozenSet, List, Optional, Set, Union

from .types import TypeResolution, ValidationResult


class SimpleTypeResolver:
    """Resolve payload types by matching against registered field signatures.

    Resolution strategy (in priority order):

    1. **Explicit type field** — if the payload contains a ``type`` or
       ``model_type`` key whose value matches a registered name, that
       wins immediately with confidence 1.0.
    2. **Field-set matching** — for each registered type, check whether
       all of its required fields appear in the payload.  The type with
       the highest field-overlap ratio wins.  Ties are broken by the
       type with fewer total required fields (more specific match).
    """

    def __init__(self) -> None:
        self._types: Dict[str, FrozenSet[str]] = {}
        self._optional_fields: Dict[str, FrozenSet[str]] = {}
        self._type_field_names: tuple = ("type", "model_type", "__type")

    def register(
        self,
        name: str,
        required_fields: Union[Set[str], FrozenSet[str]],
        optional_fields: Union[Set[str], FrozenSet[str], None] = None,
    ) -> None:
        """Register a model type with its required field signature."""
        self._types[name] = frozenset(required_fields)
        self._optional_fields[name] = frozenset(optional_fields or set())

    def resolve(self, payload: Dict[str, Any]) -> TypeResolution:
        """Detect model type from the payload."""
        if not isinstance(payload, dict) or not payload:
            return TypeResolution(error="Empty or non-dict payload")

        # Strategy 1: explicit type field
        for field_name in self._type_field_names:
            declared = payload.get(field_name)
            if isinstance(declared, str) and declared in self._types:
                return TypeResolution(
                    model_name=declared,
                    confidence=1.0,
                    matched_fields=list(self._types[declared]),
                )

        # Strategy 2: field-set matching
        payload_keys = set(payload.keys())
        best: Optional[TypeResolution] = None

        for name, required in self._types.items():
            if not required:
                continue

            # All required fields must be present
            if not required.issubset(payload_keys):
                continue

            # Score: ratio of matched required fields to payload fields
            all_known = required | self._optional_fields.get(name, frozenset())
            matched = payload_keys & all_known
            score = len(matched) / max(len(payload_keys), 1)

            if best is None or score > best.confidence:
                best = TypeResolution(
                    model_name=name,
                    confidence=round(score, 3),
                    matched_fields=sorted(matched),
                )
            elif (
                score == best.confidence
                and len(required) > len(self._types.get(best.model_name or "", frozenset()))
            ):
                # Tie-break: prefer more required fields (more specific)
                best = TypeResolution(
                    model_name=name,
                    confidence=round(score, 3),
                    matched_fields=sorted(matched),
                )

        return best or TypeResolution(error="No matching type found")

    def validate(
        self, payload: Dict[str, Any], model_name: str
    ) -> ValidationResult:
        """Validate that a payload satisfies a type's required fields."""
        required = self._types.get(model_name)
        if required is None:
            return ValidationResult(
                valid=False,
                errors=[f"Unknown model type: {model_name}"],
            )

        payload_keys = set(payload.keys())
        missing = required - payload_keys
        if missing:
            return ValidationResult(
                valid=False,
                errors=[f"Missing required fields: {sorted(missing)}"],
            )

        return ValidationResult(valid=True)

    def list_types(self) -> List[str]:
        """Return all registered type names."""
        return sorted(self._types.keys())
