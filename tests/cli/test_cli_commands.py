import os
import sys

_src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)
"""Tests for CLI command execution: validate, inspect, run, exit codes, and file export."""

import os
import tempfile
import unittest
from industrial_oracle.cli.main import execute_inspect, execute_run, execute_validate, main


class TestCLICommands(unittest.TestCase):
    """Verification of CLI execution functions and exit codes."""

    def setUp(self):
        self.metals_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..', 'examples', 'supported', 'manufacturing_metals.yaml')
        )
        self.unsupported_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..', 'examples', 'unsupported', 'cold_storage_thermodynamics.yaml')
        )

    def test_execute_validate_success(self):
        rc = execute_validate(self.metals_path)
        self.assertEqual(rc, 0)

    def test_execute_validate_rejection_of_unsupported(self):
        rc = execute_validate(self.unsupported_path)
        self.assertEqual(rc, 1)

    def test_execute_inspect(self):
        rc = execute_inspect(self.metals_path, show_matrices=True)
        self.assertEqual(rc, 0)

    def test_execute_run_with_json_export(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            rc = execute_run(self.metals_path, output_path=tmp_path)
            self.assertEqual(rc, 0)
            self.assertTrue(os.path.exists(tmp_path))
            self.assertGreater(os.path.getsize(tmp_path), 500)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_main_cli_dispatch(self):
        # Dispatched via main()
        rc = main(["validate", self.metals_path])
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
