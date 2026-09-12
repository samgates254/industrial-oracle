"""Contract tests for OpenAPI schema and specification compliance."""

import unittest
from fastapi.testclient import TestClient
from apps.api.main import app


class TestAPIContract(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_openapi_spec_structure(self):
        response = self.client.get("/api/v1/openapi.json")
        self.assertEqual(response.status_code, 200)
        spec = response.json()

        self.assertIn("openapi", spec)
        self.assertIn("info", spec)
        self.assertEqual(spec["info"]["title"], "Industrial Oracle")
        self.assertEqual(spec["info"]["version"], "0.1.0")
        self.assertIn("paths", spec)
        self.assertIn("/health", spec["paths"])
        self.assertIn("/ready", spec["paths"])
        self.assertIn("/api/v1/", spec["paths"])


if __name__ == "__main__":
    unittest.main()
