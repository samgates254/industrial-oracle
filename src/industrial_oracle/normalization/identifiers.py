"""Identifier normalization utilities."""

from .exceptions import NormalizationError


def normalize_identifier(identifier: str) -> str:
    """Return trimmed canonical identifier."""
    if not isinstance(identifier, str):
        raise NormalizationError(f"Identifier must be a string, got {type(identifier).__name__}.")
    cleaned = identifier.strip()
    if not cleaned:
        raise NormalizationError("Identifier cannot be empty or whitespace-only.")
    return cleaned
