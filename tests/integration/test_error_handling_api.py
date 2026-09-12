"""Integration tests for standardized error envelope format and exception handling."""

import unittest
from fastapi.testclient import TestClient
from fastapi import APIRouter
from apps.api.main import app
from industrial_oracle.core.exceptions import (
    EntityNotFoundException,
    BusinessRuleViolationException,
    AuthorizationException,
)

# Test router to trigger specific exceptions
test_router = APIRouter(prefix="/test-errors")


@test_router.get("/not-found")
async def trigger_not_found():
    raise EntityNotFoundException("Asset", "AST-999")


@test_router.get("/rule-violation")
async def trigger_rule_violation():
    raise BusinessRuleViolationException(
        "Machine operating hours exceed maintenance threshold.",
        rule_name="MAX_HOURS_EXCEEDED",
    )


@test_router.get("/forbidden")
async def trigger_forbidden():
    raise AuthorizationException("Access denied to Plant 4", required_role="ENGINEER")


@test_router.get("/unhandled")
async def trigger_unhandled():
    raise RuntimeError("Simulated internal catastrophic error")


app.include_router(test_router)


class TestErrorHandlingAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_404_domain_exception(self):
        response = self.client.get("/test-errors/not-found")
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertIn("error", data)
        err = data["error"]
        self.assertEqual(err["code"], "RESOURCE_NOT_FOUND")
        self.assertIn("Asset with identifier 'AST-999' was not found.", err["message"])
        self.assertIn("request_id", err)
        self.assertEqual(err["details"]["entity"], "Asset")
        self.assertIn("X-Request-ID", response.headers)

    def test_422_business_rule_violation(self):
        response = self.client.get("/test-errors/rule-violation")
        self.assertEqual(response.status_code, 422)
        data = response.json()
        self.assertIn("error", data)
        err = data["error"]
        self.assertEqual(err["code"], "BUSINESS_RULE_VIOLATION")
        self.assertEqual(err["details"]["rule"], "MAX_HOURS_EXCEEDED")

    def test_403_authorization_exception(self):
        response = self.client.get("/test-errors/forbidden")
        self.assertEqual(response.status_code, 403)
        data = response.json()
        err = data["error"]
        self.assertEqual(err["code"], "FORBIDDEN")
        self.assertEqual(err["details"]["required_role"], "ENGINEER")

    def test_500_unhandled_exception(self):
        response = self.client.get("/test-errors/unhandled")
        self.assertEqual(response.status_code, 500)
        data = response.json()
        err = data["error"]
        self.assertEqual(err["code"], "INTERNAL_SERVER_ERROR")
        self.assertIn("unexpected internal server error", err["message"])


if __name__ == "__main__":
    unittest.main()
