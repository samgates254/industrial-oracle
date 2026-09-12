"""Level 1 Schema and Type Validation."""

import math
from typing import Any, Mapping
from .exceptions import SchemaValidationError


def check_string_non_empty(value: Any, entity_name: str, field_name: str) -> None:
    """Validate that a field is a non-empty, non-whitespace string."""
    if not isinstance(value, str):
        raise SchemaValidationError(
            f"{entity_name}: {field_name} must be a string, got {type(value).__name__}."
        )
    if not value.strip():
        raise SchemaValidationError(
            f"{entity_name}: {field_name} must not be empty or whitespace-only."
        )


def check_finite_number(value: Any, entity_name: str, field_name: str) -> None:
    """Validate that a numeric value is finite (not NaN, +Inf, or -Inf)."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SchemaValidationError(
            f"{entity_name}: {field_name} must be a finite number, got {type(value).__name__}."
        )
    if not math.isfinite(value):
        raise SchemaValidationError(
            f"{entity_name}: {field_name} must be finite (got {value})."
        )


def check_strict_int(value: Any, entity_name: str, field_name: str) -> None:
    """Validate that a field is strictly an integer (rejects bool, float, str)."""
    if type(value) is not int:
        raise SchemaValidationError(
            f"{entity_name}: {field_name} must be a strict integer, got {type(value).__name__}."
        )


def check_strict_float(value: Any, entity_name: str, field_name: str) -> None:
    """Validate that a field is numeric float/int (rejects bool, str, non-finite)."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SchemaValidationError(
            f"{entity_name}: {field_name} must be a numeric float/int, got {type(value).__name__}."
        )
    if not math.isfinite(value):
        raise SchemaValidationError(
            f"{entity_name}: {field_name} must be finite (got {value})."
        )


def check_strict_bool(value: Any, entity_name: str, field_name: str) -> None:
    """Validate that a field is strictly a boolean."""
    if type(value) is not bool:
        raise SchemaValidationError(
            f"{entity_name}: {field_name} must be a boolean, got {type(value).__name__}."
        )


def check_mapping_finite_numbers(
    mapping: Mapping[str, Any], entity_name: str, field_name: str
) -> None:
    """Validate that mapping keys are non-empty strings and values are finite numbers."""
    if not isinstance(mapping, Mapping):
        raise SchemaValidationError(
            f"{entity_name}: {field_name} must be a mapping, got {type(mapping).__name__}."
        )
    for k, v in mapping.items():
        check_string_non_empty(k, entity_name, f"{field_name} key '{k}'")
        check_finite_number(v, entity_name, f"{field_name}['{k}']")
