import os
import sys

_src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)
"""Fixtures for pathological boundary conditions."""

from industrial_oracle.domain.demand import DemandOrder
from industrial_oracle.domain.economics import Economics, EnergyTariffs
from industrial_oracle.domain.electrical import ElectricalParameters
from industrial_oracle.domain.enums import ResourceCategory
from industrial_oracle.domain.factory import ConfigurationPolicy, FactoryConfiguration
from industrial_oracle.domain.machines import Machine
from industrial_oracle.domain.processes import Process
from industrial_oracle.domain.resources import Resource
from industrial_oracle.domain.time import TariffPartition, TimeHorizon


def make_exact_capacity_bottleneck_fixture() -> FactoryConfiguration:
    """Pillar III.1: Demand exactly equals total machine capacity (100% saturation)."""
    resources = [
        Resource(resource_id="RAW", category=ResourceCategory.RAW, initial_stock=200.0, safety_stock=0.0, max_storage=1000.0, is_purchasable=False),
        Resource(resource_id="FIN", category=ResourceCategory.FINISHED, initial_stock=0.0, safety_stock=0.0, max_storage=1000.0, is_purchasable=False),
    ]
    processes = [Process(process_id="P", input_coefficients={"RAW": 1.0}, output_coefficients={"FIN": 1.0})]
    machines = [Machine(machine_id="M", capacity_rate=50.0, min_load_rate=0.0, fixed_power=0.0, initial_state=0, compatible_processes=["P"], variable_energy={"P": 0.5})]
    time_horizon = TimeHorizon(num_periods=2, delta_t=1.0, tariff_partition=TariffPartition(peak_periods=[1], offpeak_periods=[2], shoulder_periods=[]))
    economics = Economics(energy_tariffs=EnergyTariffs(c_peak=10.0, c_offpeak=10.0, c_shoulder=0.0), demand_charge_rate=100.0, fixed_charge=0.0, purchase_costs={}, setup_costs={}, holding_costs={}, penalty_costs={})
    electrical = ElectricalParameters(power_factor=1.0, contract_limit_kva=100.0)
    demand = [DemandOrder(resource_id="FIN", period=2, quantity=100.0)]  # 2 * 50 = 100 kg exactly
    return FactoryConfiguration(
        schema_version="0.1.0", contract_title="V0.1", freeze_vector="(A,A,A,A,B,A,A,A)",
        configuration_policy=ConfigurationPolicy(allow_demand_shortfall=False),
        time_horizon=time_horizon, resources=resources, processes=processes, machines=machines,
        economics=economics, electrical_parameters=electrical, demand=demand
    )


def make_demand_beyond_capacity_fixture() -> FactoryConfiguration:
    """Pillar III.2: Demand exceeds total capacity (120 kg > 100 kg). Must be INFEASIBLE in hard mode."""
    factory = make_exact_capacity_bottleneck_fixture()
    demand = [DemandOrder(resource_id="FIN", period=2, quantity=120.0)]
    return factory.copy(update={"demand": demand})


def make_zero_initial_stock_with_safety_stock_fixture() -> FactoryConfiguration:
    """Pillar III.3: InitialStock = 0, SafetyStock = 20, non-purchasable raw material -> INFEASIBLE."""
    resources = [
        Resource(resource_id="RAW", category=ResourceCategory.RAW, initial_stock=0.0, safety_stock=20.0, max_storage=1000.0, is_purchasable=False),
        Resource(resource_id="FIN", category=ResourceCategory.FINISHED, initial_stock=0.0, safety_stock=0.0, max_storage=1000.0, is_purchasable=False),
    ]
    processes = [Process(process_id="P", input_coefficients={"RAW": 1.0}, output_coefficients={"FIN": 1.0})]
    machines = [Machine(machine_id="M", capacity_rate=50.0, min_load_rate=0.0, fixed_power=0.0, initial_state=0, compatible_processes=["P"], variable_energy={"P": 0.5})]
    time_horizon = TimeHorizon(num_periods=2, delta_t=1.0, tariff_partition=TariffPartition(peak_periods=[1], offpeak_periods=[2], shoulder_periods=[]))
    economics = Economics(energy_tariffs=EnergyTariffs(c_peak=10.0, c_offpeak=10.0, c_shoulder=0.0), demand_charge_rate=100.0, fixed_charge=0.0, purchase_costs={}, setup_costs={}, holding_costs={}, penalty_costs={})
    electrical = ElectricalParameters(power_factor=1.0, contract_limit_kva=100.0)
    demand = [DemandOrder(resource_id="FIN", period=2, quantity=10.0)]
    return FactoryConfiguration(
        schema_version="0.1.0", contract_title="V0.1", freeze_vector="(A,A,A,A,B,A,A,A)",
        configuration_policy=ConfigurationPolicy(allow_demand_shortfall=False),
        time_horizon=time_horizon, resources=resources, processes=processes, machines=machines,
        economics=economics, electrical_parameters=electrical, demand=demand
    )


def make_single_period_demand_spike_fixture() -> FactoryConfiguration:
    """Pillar III.4: Single-period demand spike (80 kg at t=2) exceeding single-period capacity (50 kg).
    Forces production shift to t=1 and inventory storage."""
    resources = [
        Resource(resource_id="RAW", category=ResourceCategory.RAW, initial_stock=200.0, safety_stock=0.0, max_storage=1000.0, is_purchasable=False),
        Resource(resource_id="FIN", category=ResourceCategory.FINISHED, initial_stock=0.0, safety_stock=0.0, max_storage=1000.0, is_purchasable=False),
    ]
    processes = [Process(process_id="P", input_coefficients={"RAW": 1.0}, output_coefficients={"FIN": 1.0})]
    machines = [Machine(machine_id="M", capacity_rate=50.0, min_load_rate=0.0, fixed_power=0.0, initial_state=0, compatible_processes=["P"], variable_energy={"P": 0.5})]
    time_horizon = TimeHorizon(num_periods=2, delta_t=1.0, tariff_partition=TariffPartition(peak_periods=[1], offpeak_periods=[2], shoulder_periods=[]))
    economics = Economics(energy_tariffs=EnergyTariffs(c_peak=10.0, c_offpeak=10.0, c_shoulder=0.0), demand_charge_rate=100.0, fixed_charge=0.0, purchase_costs={}, setup_costs={}, holding_costs={}, penalty_costs={})
    electrical = ElectricalParameters(power_factor=1.0, contract_limit_kva=100.0)
    demand = [DemandOrder(resource_id="FIN", period=2, quantity=80.0)]
    return FactoryConfiguration(
        schema_version="0.1.0", contract_title="V0.1", freeze_vector="(A,A,A,A,B,A,A,A)",
        configuration_policy=ConfigurationPolicy(allow_demand_shortfall=False),
        time_horizon=time_horizon, resources=resources, processes=processes, machines=machines,
        economics=economics, electrical_parameters=electrical, demand=demand
    )
