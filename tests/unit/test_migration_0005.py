"""Unit tests verifying Alembic migration 0005 structure and downgrade definitions."""

import importlib.util
import os
import sys
from unittest.mock import MagicMock
import unittest

if "alembic" not in sys.modules:
    mock_alembic = MagicMock()
    mock_op = MagicMock()
    mock_alembic.op = mock_op
    sys.modules["alembic"] = mock_alembic
    sys.modules["alembic.op"] = mock_op

if "sqlalchemy" not in sys.modules:
    mock_sa = MagicMock()
    sys.modules["sqlalchemy"] = mock_sa
    sys.modules["sqlalchemy.dialects"] = MagicMock()
    sys.modules["sqlalchemy.dialects.postgresql"] = MagicMock()


class TestMigration0005(unittest.TestCase):
    def setUp(self):
        migration_path = "/working_dir/c_020f8ea48fd27ffd/migrations/versions/0005_integration_event_infrastructure.py"
        self.assertTrue(os.path.exists(migration_path))
        spec = importlib.util.spec_from_file_location("migration_0005", migration_path)
        self.migration = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.migration)

    def test_migration_0005_metadata_and_revisions(self):
        self.assertEqual(self.migration.revision, "0005_integration_event_infrastructure")
        self.assertEqual(self.migration.down_revision, "0004_operational_execution")
        self.assertTrue(callable(getattr(self.migration, "upgrade", None)))
        self.assertTrue(callable(getattr(self.migration, "downgrade", None)))

    def test_migration_0005_table_definitions(self):
        with open("/working_dir/c_020f8ea48fd27ffd/migrations/versions/0005_integration_event_infrastructure.py") as f:
            code = f.read()

        # Check tables created
        self.assertIn('"outbox_events"', code)
        self.assertIn('"event_consumptions"', code)
        self.assertIn('"webhook_endpoints"', code)

        # Check required fields
        self.assertIn('"event_id"', code)
        self.assertIn('"status"', code)
        self.assertIn('"attempts"', code)
        self.assertIn('"consumer_name"', code)
        self.assertIn('"subscribed_event_types"', code)

        # Check downgrade drops tables
        self.assertIn('op.drop_table("webhook_endpoints")', code)
        self.assertIn('op.drop_table("event_consumptions")', code)
        self.assertIn('op.drop_table("outbox_events")', code)


if __name__ == "__main__":
    unittest.main()
