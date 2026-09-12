import os
import sys

_src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)
"""Fixtures for parameter perturbation and monotonicity checking."""

from .analytical_truth_sets import make_micro_factory_fixture
from industrial_oracle.domain.demand import DemandOrder
from industrial_oracle.domain.economics import Economics, EnergyTariffs
from industrial_oracle.domain.electrical import ElectricalParameters
from industrial_oracle.domain.machines import Machine


def make_tariff_perturbed_pair():
    f_base = make_micro_factory_fixture()
    econ_high = Economics(
        energy_tariffs=EnergyTariffs(c_peak=35.0, c_offpeak=15.0, c_shoulder=0.0),
        demand_charge_rate=500.0, fixed_charge=0.0, purchase_costs={}, setup_costs={}, holding_costs={}, penalty_costs={}
    )
    f_high = f_base.copy(update={"economics": econ_high})
    return f_base, f_high


def make_power_factor_perturbed_pair():
    f_high_pf = make_micro_factory_fixture() # cos_phi = 0.80
    elec_low = ElectricalParameters(power_factor=0.60, contract_limit_kva=100.0)
    f_low_pf = f_high_pf.copy(update={"electrical_parameters": elec_low})
    return f_high_pf, f_low_pf


def make_demand_perturbed_pair():
    f_base = make_micro_factory_fixture() # demand = 36 kg
    dmd_high = [DemandOrder(resource_id="FIN", period=2, quantity=40.0)]
    f_high = f_base.copy(update={"demand": dmd_high})
    return f_base, f_high


def make_capacity_perturbed_pair():
    f_base = make_micro_factory_fixture() # cap = 50 kg/h
    mach_high = [
        Machine(machine_id="M", capacity_rate=70.0, min_load_rate=0.0, fixed_power=0.0, initial_state=0, compatible_processes=["P"], variable_energy={"P": 0.5})
    ]
    f_high = f_base.copy(update={"machines": mach_high})
    return f_base, f_high
