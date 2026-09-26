"""Core exception hierarchy and standardized error formatting."""

from typing import Any, Dict, Optional


class DomainException(Exception):
    """Base exception for all domain business errors."""

    def __init__(
        self,
        message: str,
        code: str = "DOMAIN_ERROR",
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}


class EntityNotFoundException(DomainException):
    """Raised when an aggregate root or entity cannot be found."""

    def __init__(
        self,
        entity_name: str,
        entity_id: Any = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        if entity_id is not None:
            message = f"{entity_name} with identifier '{entity_id}' was not found."
            default_details = {"entity": entity_name, "id": str(entity_id)}
        else:
            message = str(entity_name)
            default_details = {"entity": entity_name}
        super().__init__(
            message=message,
            code="RESOURCE_NOT_FOUND",
            status_code=404,
            details=details or default_details,
        )


class EntityAlreadyExistsException(DomainException):
    """Raised when an entity with duplicate unique constraints already exists."""

    def __init__(
        self,
        entity_name: str,
        conflict_field: Optional[str] = None,
        value: Any = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        if conflict_field is not None:
            message = f"{entity_name} with {conflict_field}='{value}' already exists."
            default_details = {"entity": entity_name, "field": conflict_field, "value": str(value)}
        else:
            message = str(entity_name)
            default_details = {"entity": entity_name}
        super().__init__(
            message=message,
            code="ALREADY_EXISTS",
            status_code=409,
            details=details or default_details,
        )


class BusinessRuleViolationException(DomainException):
    """Raised when an invariant or business rule check fails."""

    def __init__(
        self,
        message: str,
        rule_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.rule_name = rule_name
        super().__init__(
            message=message,
            code="BUSINESS_RULE_VIOLATION",
            status_code=422,
            details=details or ({"rule": rule_name} if rule_name else {}),
        )


class ValidationException(DomainException):
    """Raised when input parameter validation fails."""

    def __init__(
        self,
        message: str = "Validation failed for request data.",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=400,
            details=details or {},
        )


class AuthenticationException(DomainException):
    """Raised when identity authentication fails."""

    def __init__(
        self,
        message: str = "Authentication credentials are invalid or expired.",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=message,
            code="UNAUTHORIZED",
            status_code=401,
            details=details or {},
        )


class AuthorizationException(DomainException):
    """Raised when role or permission check fails."""

    def __init__(
        self,
        message: str = "Insufficient permissions to perform this action.",
        required_role: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        err_details = details or {}
        if required_role:
            err_details["required_role"] = required_role
        super().__init__(
            message=message,
            code="FORBIDDEN",
            status_code=403,
            details=err_details,
        )


class ConflictException(DomainException):
    """Raised when concurrency or state conflict occurs."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=message,
            code="CONFLICT",
            status_code=409,
            details=details or {},
        )


class RateLimitExceededException(DomainException):
    """Raised when client exceeds rate limit threshold."""

    def __init__(
        self,
        message: str = "Rate limit exceeded. Please retry after some time.",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=message,
            code="RATE_LIMIT_EXCEEDED",
            status_code=429,
            details=details or {},
        )


class InfrastructureException(Exception):
    """Raised when external infrastructure (PostgreSQL, Redis, Solvers) encounters an error."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_SERVER_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}


def format_error_response(
    code: str,
    message: str,
    request_id: str,
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Generates the standardized API error format.

    Structure:
    {
        "error": {
            "code": "RESOURCE_NOT_FOUND",
            "message": "...",
            "request_id": "...",
            "details": {}
        }
    }
    """
    return {
        "error": {
            "code": code,
            "message": message,
            "request_id": request_id,
            "details": details if details is not None else {},
        }
    }
