import os
import sys

_src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)
"""Tests for Machine normalization and Canonical Index Sets."""

import unittest
from industrial_oracle.domain.machines import Machine
from industrial_oracle.domain.time import TariffPartition, TimeHorizon
from industrial_oracle.normalization.indexes import build_canonical_indexes
from industrial_oracle.normalization.machines import normalize_machine
from industrial_oracle.normalization.processes import NormalizedProcess
from industrial_oracle.normalization.resources import NormalizedResource
from industrial_oracle.normalization.time import normalize_time_horizon


class TestMachinesIndexesNormalization(unittest.TestCase):
    """Machine normalization and bipartite compatibility indexing."""

    def test_machine_normalization_sorting(self):
        mach = Machine(
            machine_id="M1",
            capacity_rate=100.0,
            min_load_rate=20.0,
            fixed_power=5.0,
            initial_state=0,
            compatible_processes=["P2", "P1"],
            variable_energy={"P2": 0.7, "P1": 0.5},
        )
        norm_mach = normalize_machine(mach)
        self.assertEqual(norm_mach.compatible_processes, ("P1", "P2"))
        self.assertEqual(list(norm_mach.variable_energy_kwh_per_kg.keys()), ["P1", "P2"])

    def test_bipartite_compatibility_relation(self):
        th = normalize_time_horizon(
            TimeHorizon(
                num_periods=2,
                delta_t=1.0,
                tariff_partition=TariffPartition(peak_periods=[1], offpeak_periods=[2], shoulder_periods=[]),
            )
        )
        resources = [
            NormalizedResource("R1", "RAW", 0, 0, 100, True, (float('inf'), float('inf'))),
            NormalizedResource("R2", "FINISHED", 0, 0, 100, False, (float('inf'), float('inf'))),
        ]
        processes = [
            NormalizedProcess("P1", {"R1": 1.0}, {"R2": 1.0}),
            NormalizedProcess("P2", {"R1": 1.0}, {"R2": 1.0}),
        ]
        machines = [
            normalize_machine(
                Machine(
                    machine_id="M1",
                    capacity_rate=100.0,
                    min_load_rate=0.0,
                    fixed_power=0.0,
                    initial_state=0,
                    compatible_processes=["P1"],
                    variable_energy={"P1": 0.5},
                )
            ),
            normalize_machine(
                Machine(
                    machine_id="M2",
                    capacity_rate=80.0,
                    min_load_rate=0.0,
                    fixed_power=0.0,
                    initial_state=0,
                    compatible_processes=["P1", "P2"],
                    variable_energy={"P1": 0.5, "P2": 0.6},
                )
            ),
        ]
        indexes = build_canonical_indexes(resources, processes, machines, th)

        # Invariant: p in P_m <=> m in M_p
        for m_id, procs in indexes.P_m.items():
            for p_id in procs:
                self.assertIn(m_id, indexes.M_p[p_id])

        for p_id, machs in indexes.M_p.items():
            for m_id in machs:
                self.assertIn(p_id, indexes.P_m[m_id])

        self.assertEqual(indexes.M_p["P1"], ("M1", "M2"))
        self.assertEqual(indexes.M_p["P2"], ("M2",))
        self.assertEqual(indexes.num_compatible_pairs, 3)


if __name__ == "__main__":
    unittest.main()
