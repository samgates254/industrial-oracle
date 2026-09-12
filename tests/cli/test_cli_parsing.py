import os
import sys

_src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)
"""Tests for CLI argument parser configuration and subcommand routing."""

import unittest
from industrial_oracle.cli.main import build_parser


class TestCLIParsing(unittest.TestCase):
    """CLI argument parser specification tests."""

    def setUp(self):
        self.parser = build_parser()

    def test_validate_subcommand_parsing(self):
        args = self.parser.parse_args(["validate", "config.yaml"])
        self.assertEqual(args.command, "validate")
        self.assertEqual(args.config, "config.yaml")

    def test_inspect_subcommand_parsing(self):
        args = self.parser.parse_args(["inspect", "config.yaml", "--matrices"])
        self.assertEqual(args.command, "inspect")
        self.assertEqual(args.config, "config.yaml")
        self.assertTrue(args.matrices)

    def test_run_subcommand_parsing(self):
        args = self.parser.parse_args(["run", "config.yaml", "-o", "out.json", "--time-limit", "60.0"])
        self.assertEqual(args.command, "run")
        self.assertEqual(args.config, "config.yaml")
        self.assertEqual(args.output, "out.json")
        self.assertEqual(args.time_limit, 60.0)


if __name__ == "__main__":
    unittest.main()
