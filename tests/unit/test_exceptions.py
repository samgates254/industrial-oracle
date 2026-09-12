"""Unit tests for domain exceptions and error envelope formatting."""

import unittest
import uuid
from industrial_oracle.core.exceptions import (
    DomainException,
    EntityNotFoundException,
    EntityAlreadyExistsException,
    BusinessRuleViolationException,
    ValidationException,
    AuthenticationException,
    AuthorizationException,
    ConflictException,
    RateLimitExceededException,
    InfrastructureException,
    format_error_response,
)


class TestExceptions(unittest.TestCase):
    def test_format_error_response(self):
        req_id = str(uuid.uuid4())
        res = format_error_response(
            code="TEST_ERROR",
            message="Test message",
            request_id=req_id,
            details={"field": "value"},
        )
        self.assertIn("error", res)
        err = res["error"]
        self.assertEqual(err["code"], "TEST_ERROR")
        self.assertEqual(err["message"], "Test message")
        self.assertEqual(err["request_id"], req_id)
        self.assertEqual(err["details"], {"field": "value"})

    def test_entity_not_found_exception(self):
        exc = EntityNotFoundException("Machine", "M-100")
        self.assertEqual(exc.status_code, 404)
        self.assertEqual(exc.code, "RESOURCE_NOT_FOUND")
        self.assertIn("Machine with identifier 'M-100' was not found.", exc.message)
        self.assertEqual(exc.details["entity"], "Machine")

    def test_entity_already_exists_exception(self):
        exc = EntityAlreadyExistsException("Site", "code", "NBO-01")
        self.assertEqual(exc.status_code, 409)
        self.assertEqual(exc.code, "ALREADY_EXISTS")
        self.assertEqual(exc.details["field"], "code")

    def test_business_rule_violation_exception(self):
        exc = BusinessRuleViolationException("Capacity exceeded", rule_name="MAX_CAPACITY")
        self.assertEqual(exc.status_code, 422)
        self.assertEqual(exc.code, "BUSINESS_RULE_VIOLATION")
        self.assertEqual(exc.details["rule"], "MAX_CAPACITY")

    def test_auth_exceptions(self):
        auth_exc = AuthenticationException()
        self.assertEqual(auth_exc.status_code, 401)
        self.assertEqual(auth_exc.code, "UNAUTHORIZED")

        forbid_exc = AuthorizationException(required_role="ADMIN")
        self.assertEqual(forbid_exc.status_code, 403)
        self.assertEqual(forbid_exc.code, "FORBIDDEN")
        self.assertEqual(forbid_exc.details["required_role"], "ADMIN")

    def test_rate_limit_and_infra_exceptions(self):
        rate_exc = RateLimitExceededException()
        self.assertEqual(rate_exc.status_code, 429)
        self.assertEqual(rate_exc.code, "RATE_LIMIT_EXCEEDED")

        infra_exc = InfrastructureException("DB Connection Timeout")
        self.assertEqual(infra_exc.status_code, 500)
        self.assertEqual(infra_exc.code, "INTERNAL_SERVER_ERROR")


if __name__ == "__main__":
    unittest.main()
