"""Canonical unit definitions and conversion constants."""

MASS_UNIT = "kg"
ENERGY_UNIT = "kWh"
ACTIVE_POWER_UNIT = "kW"
APPARENT_POWER_UNIT = "kVA"
TIME_UNIT = "h"
CURRENCY_UNIT = "KSh"

TONNES_TO_KG = 1000.0
MWH_TO_KWH = 1000.0
MW_TO_KW = 1000.0


def convert_tonnes_to_kg(val: float) -> float:
    """Convert metric tonnes to canonical kilograms."""
    return float(val) * TONNES_TO_KG


def convert_mwh_to_kwh(val: float) -> float:
    """Convert megawatt-hours to canonical kilowatt-hours."""
    return float(val) * MWH_TO_KWH


def convert_mw_to_kw(val: float) -> float:
    """Convert megawatts to canonical kilowatts."""
    return float(val) * MW_TO_KW
