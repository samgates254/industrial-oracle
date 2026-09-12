"""Unit tests for configuration management."""

import unittest
from industrial_oracle.core.config import Settings


class TestConfig(unittest.TestCase):
    def test_default_settings(self):
        settings = Settings()
        self.assertEqual(settings.PROJECT_NAME, "Industrial Oracle")
        self.assertEqual(settings.VERSION, "0.1.0")
        self.assertEqual(settings.API_V1_STR, "/api/v1")
        self.assertEqual(settings.ENVIRONMENT, "development")
        self.assertFalse(settings.DEBUG)
        self.assertEqual(settings.DATABASE_POOL_SIZE, 20)
        self.assertEqual(settings.RATE_LIMIT_PER_MINUTE, 60)

    def test_custom_override(self):
        custom = Settings(PROJECT_NAME="Custom Factory", DEBUG=True, RATE_LIMIT_PER_MINUTE=100)
        self.assertEqual(custom.PROJECT_NAME, "Custom Factory")
        self.assertTrue(custom.DEBUG)
        self.assertEqual(custom.RATE_LIMIT_PER_MINUTE, 100)


if __name__ == "__main__":
    unittest.main()
