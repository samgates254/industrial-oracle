import os
import sys

_src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)
"""Tests for Multi-Industry Configuration Library:
- Supported manufacturing and chemical configurations
- Supported with limitations compute cluster configuration
- Honest rejection of unsupported thermodynamics configuration
"""

import os
import unittest
from industrial_oracle.cli.main import execute_inspect, execute_run, execute_validate


class TestMultiIndustryLibrary(unittest.TestCase):
    """Multi-Industry Library verification across all 4 archetypes."""

    def setUp(self):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'examples'))
        self.metals_path = os.path.join(base_dir, 'supported', 'manufacturing_metals.yaml')
        self.chemical_path = os.path.join(base_dir, 'supported', 'chemical_blending.yaml')
        self.compute_path = os.path.join(base_dir, 'supported_with_limitations', 'batch_compute_cluster.yaml')
        self.cold_path = os.path.join(base_dir, 'unsupported', 'cold_storage_thermodynamics.yaml')

    def test_supported_continuous_metals(self):
        """SUPPORTED_BY_V0.1: Continuous steel/metals extrusion solves to OPTIMAL."""
        self.assertEqual(execute_validate(self.metals_path), 0)
        self.assertEqual(execute_inspect(self.metals_path), 0)
        self.assertEqual(execute_run(self.metals_path), 0)

    def test_supported_chemical_blending(self):
        """SUPPORTED_BY_V0.1: Multi-input stoichiometric chemical blending solves to OPTIMAL."""
        self.assertEqual(execute_validate(self.chemical_path), 0)
        self.assertEqual(execute_inspect(self.chemical_path), 0)
        self.assertEqual(execute_run(self.chemical_path), 0)

    def test_supported_with_limitations_compute_cluster(self):
        """SUPPORTED_WITH_LIMITATIONS: Batch compute workload queue solves to OPTIMAL."""
        self.assertEqual(execute_validate(self.compute_path), 0)
        self.assertEqual(execute_inspect(self.compute_path), 0)
        self.assertEqual(execute_run(self.compute_path), 0)

    def test_honest_rejection_of_unsupported_thermodynamics(self):
        """NOT_REPRESENTABLE_IN_V0.1: Cold storage thermal state dynamics are honestly rejected."""
        # Validation must reject unsupported thermal dynamics schema
        self.assertEqual(execute_validate(self.cold_path), 1)
        # Inspection must reject
        self.assertEqual(execute_inspect(self.cold_path), 1)
        # Execution must fail safely with code 3 (Execution Error)
        self.assertEqual(execute_run(self.cold_path), 3)


if __name__ == "__main__":
    unittest.main()
