"""Unit tests verifying Alembic migration configuration and asyncpg driver resolution."""

import importlib.util
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

if "alembic" not in sys.modules:
    mock_alembic = MagicMock()
    mock_alembic.op = MagicMock()
    sys.modules["alembic"] = mock_alembic
    sys.modules["alembic.op"] = mock_alembic.op

if "sqlalchemy" not in sys.modules:
    mock_sa = MagicMock()
    sys.modules["sqlalchemy"] = mock_sa
    sys.modules["sqlalchemy.dialects"] = MagicMock()
    sys.modules["sqlalchemy.dialects.postgresql"] = MagicMock()

# Ensure src is in python path
this_file = globals().get("__file__") or os.path.abspath("tests/unit/test_migration_env.py")
project_root = os.path.abspath(os.path.join(os.path.dirname(this_file), "..", ".."))
sys.path.insert(0, os.path.join(project_root, "src"))

from industrial_oracle.core.config import Settings


class TestMigrationEnvConfig(unittest.TestCase):
    def test_default_database_url_is_asyncpg(self):
        """Authoritative database configuration must use postgresql+asyncpg."""
        settings = Settings()
        self.assertTrue(
            settings.DATABASE_URL.startswith("postgresql+asyncpg://"),
            f"Expected postgresql+asyncpg:// URL, got {settings.DATABASE_URL}",
        )

    def test_alembic_env_url_configuration(self):
        """Verifies migrations/env.py assigns postgresql+asyncpg to alembic sqlalchemy.url."""
        env_py_path = os.path.join(project_root, "migrations", "env.py")
        self.assertTrue(os.path.exists(env_py_path), "migrations/env.py must exist")

        with open(env_py_path, "r") as f:
            code = f.read()

        # Verify async engine usage
        self.assertIn("async_engine_from_config", code)
        self.assertIn("connection.run_sync(do_run_migrations)", code)
        self.assertIn("run_async_migrations", code)
        self.assertNotIn("psycopg2", code, "migrations/env.py must not reference psycopg2")

        # Verify configuration loads DATABASE_URL
        self.assertIn('config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)', code)

    def test_migration_chain_integrity(self):
        """Verifies migration chain strictly follows 0001 -> 0002 -> 0003 -> 0004 -> 0005."""
        versions_dir = os.path.join(project_root, "migrations", "versions")
        revisions = {}

        for fname in sorted(os.listdir(versions_dir)):
            if fname.endswith(".py") and not fname.startswith("__"):
                fpath = os.path.join(versions_dir, fname)
                spec = importlib.util.spec_from_file_location(fname[:-3], fpath)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                revisions[mod.revision] = mod.down_revision

        self.assertIn("0001_initial_schema", revisions)
        self.assertIsNone(revisions["0001_initial_schema"])

        self.assertEqual(revisions.get("0002_identity_organization_rbac"), "0001_initial_schema")
        self.assertEqual(revisions.get("0003_assets_production_lines_machines"), "0002_identity_organization_rbac")
        self.assertEqual(revisions.get("0004_operational_execution"), "0003_assets_production_lines_machines")
        self.assertEqual(revisions.get("0005_integration_event_infrastructure"), "0004_operational_execution")


if __name__ == "__main__":
    unittest.main()
