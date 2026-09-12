"""Validation exception hierarchy for V0.1."""


class DomainValidationError(Exception):
    """Base class for all Industrial Oracle domain validation failures."""


class SchemaValidationError(DomainValidationError):
    """Level 1 validation failure: schema, types, structure, or non-finite numbers."""


class PhysicalValidationError(DomainValidationError):
    """Level 2 physical or parameter sanity failure."""
