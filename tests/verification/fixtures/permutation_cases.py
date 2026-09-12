import os
import sys

_src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)
"""Fixtures for permutation invariance testing."""

from industrial_oracle.domain.demand import DemandOrder
from industrial_oracle.domain.economics import Economics, EnergyTariffs
from industrial_oracle.domain.electrical import ElectricalParameters
from industrial_oracle.domain.enums import ResourceCategory
from industrial_oracle.domain.factory import ConfigurationPolicy, FactoryConfiguration
from industrial_oracle.domain.machines import Machine
from industrial_oracle.domain.processes import Process
from industrial_oracle.domain.resources import Resource
from industrial_oracle.domain.time import TariffPartition, TimeHorizon


def make_permuted_factory_pair():
    """Return two FactoryConfigurations with identical data but permuted declaration orders."""
    r_raw = Resource(resource_id="RAW", category=ResourceCategory.RAW, initial_stock=100.0, safety_stock=0.0, max_storage=1000.0, is_purchasable=False)
    r_int = Resource(resource_id="INT", category=ResourceCategory.WIP, initial_stock=0.0, safety_stock=0.0, max_storage=500.0, is_purchasable=False)
    r_fin = Resource(resource_id="FIN", category=ResourceCategory.FINISHED, initial_stock=0.0, safety_stock=0.0, max_storage=1000.0, is_purchasable=False)

    p1 = Process(process_id="P1", input_coefficients={"RAW": 1.0}, output_coefficients={"INT": 1.0})
    p2 = Process(process_id="P2", input_coefficients={"INT": 1.0}, output_coefficients={"FIN": 1.0})

    m1 = Machine(machine_id="M1", capacity_rate=50.0, min_load_rate=0.0, fixed_power=0.0, initial_state=0, compatible_processes=["P1"], variable_energy={"P1": 0.5})
    m2 = Machine(machine_id="M2", capacity_rate=50.0, min_load_rate=0.0, fixed_power=0.0, initial_state=0, compatible_processes=["P2"], variable_energy={"P2": 0.5})

    th = TimeHorizon(num_periods=2, delta_t=1.0, tariff_partition=TariffPartition(peak_periods=[1], offpeak_periods=[2], shoulder_periods=[]))
    econ = Economics(energy_tariffs=EnergyTariffs(c_peak=20.0, c_offpeak=10.0, c_shoulder=0.0), demand_charge_rate=500.0, fixed_charge=0.0, purchase_costs={}, setup_costs={}, holding_costs={}, penalty_costs={})
    elec = ElectricalParameters(power_factor=0.80, contract_limit_kva=100.0)
    dmd = [DemandOrder(resource_id="FIN", period=2, quantity=36.0)]

    # Ordering 1
    f1 = FactoryConfiguration(
        schema_version="0.1.0", contract_title="V0.1", freeze_vector="(A,A,A,A,B,A,A,A)",
        configuration_policy=ConfigurationPolicy(), time_horizon=th,
        resources=[r_raw, r_int, r_fin],
        processes=[p1, p2],
        machines=[m1, m2],
        economics=econ, electrical_parameters=elec, demand=dmd
    )

    # Ordering 2 (reverse declarations)
    f2 = FactoryConfiguration(
        schema_version="0.1.0", contract_title="V0.1", freeze_vector="(A,A,A,A,B,A,A,A)",
        configuration_policy=ConfigurationPolicy(), time_horizon=th,
        resources=[r_fin, r_raw, r_int],
        processes=[p2, p1],
        machines=[m2, m1],
        economics=econ, electrical_parameters=elec, demand=dmd
    )

    return f1, f2
