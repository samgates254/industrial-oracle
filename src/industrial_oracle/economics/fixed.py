"""Fixed facility charge extraction (scalar F)."""

from industrial_oracle.normalization.factory import NormalizedFactory


def compile_fixed_charge(factory: NormalizedFactory) -> float:
    """Extract single additive horizon-level fixed charge scalar F [KSh]."""
    return float(factory.economics.fixed_charge)
