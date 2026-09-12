"""Objective vector compiler (OBJ-001) delegating to EconomicCompiler."""

from typing import Tuple
from industrial_oracle.normalization.factory import NormalizedFactory
from industrial_oracle.model.variables import VariableRegistry
from industrial_oracle.economics.compiler import EconomicCompiler, EconomicObjective


def compile_objective(
    factory: NormalizedFactory,
    registry: VariableRegistry,
) -> Tuple[Tuple[float, ...], float]:
    """Generate linear cost vector c and additive fixed charge for OBJ-001."""
    econ_obj = EconomicCompiler.compile(factory, registry)
    return econ_obj.c, econ_obj.fixed_charge
