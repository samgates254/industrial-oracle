"""End-to-end tests verifying request lifecycle and request-id propagation."""

import unittest
import uuid
from fastapi.testclient import TestClient
from apps.api.main import app


class TestRequestLifecycle(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_request_id_injected_if_omitted(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        req_id = response.headers.get("X-Request-ID")
        self.assertIsNotNone(req_id)
        # Verify valid UUID format
        parsed = uuid.UUID(req_id)
        self.assertEqual(str(parsed), req_id)

    def test_request_id_preserved_if_provided(self):
        custom_id = "test-req-custom-12345"
        response = self.client.get("/health", headers={"X-Request-ID": custom_id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("X-Request-ID"), custom_id)


if __name__ == "__main__":
    unittest.main()
