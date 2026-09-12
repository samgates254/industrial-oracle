"""EconomicCompiler and EconomicObjective representation for M3.0.1."""

from dataclasses import dataclass
from types import MappingProxyType
from typing import Dict, List, Mapping, Tuple
from industrial_oracle.normalization.factory import NormalizedFactory
from industrial_oracle.model.variables import VariableRegistry
from .demand import compile_demand_charge
from .energy import compile_energy_coefficients
from .fixed import compile_fixed_charge
from .holding import compile_holding_costs
from .penalty import compile_penalty_costs
from .purchase import compile_purchase_costs
from .startup import compile_startup_costs
from .traceability import CoefficientProvenance


@dataclass(frozen=True)
class EconomicObjective:
    """Authoritative immutable economic objective representation (Z = c^T y + FixedCharge)."""

    c: Tuple[float, ...]
    fixed_charge: float
    provenance: Mapping[int, Tuple[CoefficientProvenance, ...]]


class EconomicCompiler:
    """Compiles normalized economic parameters into deterministic objective coefficients."""

    @staticmethod
    def compile(factory: NormalizedFactory, registry: VariableRegistry) -> EconomicObjective:
        """Compile all seven economic cost components into c and fixed_charge."""
        c: List[float] = [0.0] * len(registry)
        raw_prov: Dict[int, List[CoefficientProvenance]] = {}

        # 1. Electricity Energy Cost
        compile_energy_coefficients(factory, registry, c, raw_prov)

        # 2. Demand Charge Cost
        compile_demand_charge(factory, registry, c, raw_prov)

        # 3. Resource Purchase Cost
        compile_purchase_costs(factory, registry, c, raw_prov)

        # 4. Machine Startup Cost
        compile_startup_costs(factory, registry, c, raw_prov)

        # 5. Inventory Holding Cost
        compile_holding_costs(factory, registry, c, raw_prov)

        # 6. Demand Shortfall Penalty (if soft mode)
        compile_penalty_costs(factory, registry, c, raw_prov)

        # 7. Fixed Facility Charge
        fixed_charge = compile_fixed_charge(factory)

        # Freeze provenance mappings
        frozen_prov = {
            col: tuple(entries)
            for col, entries in sorted(raw_prov.items(), key=lambda x: x[0])
        }

        return EconomicObjective(
            c=tuple(c),
            fixed_charge=fixed_charge,
            provenance=MappingProxyType(frozen_prov),
        )
