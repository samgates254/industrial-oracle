"""Integration tests for observability /health and /ready endpoints."""

import unittest
from fastapi.testclient import TestClient
from apps.api.main import app


class TestObservabilityAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health_endpoint(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["version"], "0.1.0")
        self.assertIn("timestamp", data)
        self.assertIn("X-Request-ID", response.headers)

    def test_ready_endpoint(self):
        response = self.client.get("/ready")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ready")
        self.assertIn("checks", data)
        self.assertEqual(data["checks"]["database"], "up")
        self.assertEqual(data["checks"]["redis"], "up")

    def test_api_v1_root(self):
        response = self.client.get("/api/v1/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["project"], "Industrial Oracle")
        self.assertEqual(data["api_version"], "v1")
        self.assertIn("domains", data)
        self.assertIn("assets", data["domains"])


if __name__ == "__main__":
    unittest.main()
