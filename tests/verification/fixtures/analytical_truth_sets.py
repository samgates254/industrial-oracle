import os
import sys

_src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)
"""Analytical Truth Fixtures with independently derived expected optima."""

from industrial_oracle.domain.demand import DemandOrder
from industrial_oracle.domain.economics import Economics, EnergyTariffs
from industrial_oracle.domain.electrical import ElectricalParameters
from industrial_oracle.domain.enums import ResourceCategory
from industrial_oracle.domain.factory import ConfigurationPolicy, FactoryConfiguration
from industrial_oracle.domain.machines import Machine
from industrial_oracle.domain.processes import Process
from industrial_oracle.domain.resources import Resource
from industrial_oracle.domain.time import TariffPartition, TimeHorizon


def make_micro_factory_fixture() -> FactoryConfiguration:
    """1. Two-Period Micro-Factory Benchmark."""
    resources = [
        Resource(resource_id="RAW", category=ResourceCategory.RAW, initial_stock=100.0, safety_stock=0.0, max_storage=1000.0, is_purchasable=False),
        Resource(resource_id="FIN", category=ResourceCategory.FINISHED, initial_stock=0.0, safety_stock=0.0, max_storage=1000.0, is_purchasable=False),
    ]
    processes = [
        Process(process_id="P", input_coefficients={"RAW": 1.0}, output_coefficients={"FIN": 0.90})
    ]
    machines = [
        Machine(machine_id="M", capacity_rate=50.0, min_load_rate=0.0, fixed_power=0.0, initial_state=0, compatible_processes=["P"], variable_energy={"P": 0.5})
    ]
    time_horizon = TimeHorizon(
        num_periods=2,
        delta_t=1.0,
        tariff_partition=TariffPartition(peak_periods=[1], offpeak_periods=[2], shoulder_periods=[]),
    )
    economics = Economics(
        energy_tariffs=EnergyTariffs(c_peak=20.0, c_offpeak=10.0, c_shoulder=0.0),
        demand_charge_rate=500.0,
        fixed_charge=0.0,
        purchase_costs={},
        setup_costs={},
        holding_costs={},
        penalty_costs={},
    )
    electrical = ElectricalParameters(power_factor=0.80, contract_limit_kva=100.0)
    demand = [DemandOrder(resource_id="FIN", period=2, quantity=36.0)]

    return FactoryConfiguration(
        schema_version="0.1.0",
        contract_title="V0.1",
        freeze_vector="(A,A,A,A,B,A,A,A)",
        configuration_policy=ConfigurationPolicy(allow_demand_shortfall=False),
        time_horizon=time_horizon,
        resources=resources,
        processes=processes,
        machines=machines,
        economics=economics,
        electrical_parameters=electrical,
        demand=demand,
    )


def make_multi_stage_supply_chain_fixture() -> FactoryConfiguration:
    """2. Multi-Stage Supply Chain Benchmark (RAW -> INT -> FIN)."""
    resources = [
        Resource(resource_id="RAW", category=ResourceCategory.RAW, initial_stock=100.0, safety_stock=0.0, max_storage=1000.0, is_purchasable=False),
        Resource(resource_id="INT", category=ResourceCategory.WIP, initial_stock=0.0, safety_stock=0.0, max_storage=500.0, is_purchasable=False),
        Resource(resource_id="FIN", category=ResourceCategory.FINISHED, initial_stock=0.0, safety_stock=0.0, max_storage=1000.0, is_purchasable=False),
    ]
    processes = [
        Process(process_id="P1", input_coefficients={"RAW": 1.0}, output_coefficients={"INT": 1.0}),
        Process(process_id="P2", input_coefficients={"INT": 1.0}, output_coefficients={"FIN": 1.0}),
    ]
    machines = [
        Machine(machine_id="M1", capacity_rate=50.0, min_load_rate=0.0, fixed_power=0.0, initial_state=0, compatible_processes=["P1"], variable_energy={"P1": 0.5}),
        Machine(machine_id="M2", capacity_rate=50.0, min_load_rate=0.0, fixed_power=0.0, initial_state=0, compatible_processes=["P2"], variable_energy={"P2": 0.5}),
    ]
    time_horizon = TimeHorizon(
        num_periods=2,
        delta_t=1.0,
        tariff_partition=TariffPartition(peak_periods=[1], offpeak_periods=[2], shoulder_periods=[]),
    )
    economics = Economics(
        energy_tariffs=EnergyTariffs(c_peak=10.0, c_offpeak=10.0, c_shoulder=0.0),
        demand_charge_rate=100.0,
        fixed_charge=0.0,
        purchase_costs={},
        setup_costs={},
        holding_costs={},
        penalty_costs={},
    )
    electrical = ElectricalParameters(power_factor=1.0, contract_limit_kva=100.0)
    demand = [DemandOrder(resource_id="FIN", period=2, quantity=40.0)]

    return FactoryConfiguration(
        schema_version="0.1.0",
        contract_title="V0.1",
        freeze_vector="(A,A,A,A,B,A,A,A)",
        configuration_policy=ConfigurationPolicy(allow_demand_shortfall=False),
        time_horizon=time_horizon,
        resources=resources,
        processes=processes,
        machines=machines,
        economics=economics,
        electrical_parameters=electrical,
        demand=demand,
    )


def make_asymmetric_dispatch_fixture() -> FactoryConfiguration:
    """3. Asymmetric Multi-Machine Dispatch Benchmark (M1: 0.2 kWh/kg vs M2: 0.8 kWh/kg)."""
    resources = [
        Resource(resource_id="RAW", category=ResourceCategory.RAW, initial_stock=100.0, safety_stock=0.0, max_storage=1000.0, is_purchasable=False),
        Resource(resource_id="FIN", category=ResourceCategory.FINISHED, initial_stock=0.0, safety_stock=0.0, max_storage=1000.0, is_purchasable=False),
    ]
    processes = [
        Process(process_id="P", input_coefficients={"RAW": 1.0}, output_coefficients={"FIN": 1.0})
    ]
    machines = [
        Machine(machine_id="M1", capacity_rate=30.0, min_load_rate=0.0, fixed_power=0.0, initial_state=0, compatible_processes=["P"], variable_energy={"P": 0.2}),
        Machine(machine_id="M2", capacity_rate=30.0, min_load_rate=0.0, fixed_power=0.0, initial_state=0, compatible_processes=["P"], variable_energy={"P": 0.8}),
    ]
    time_horizon = TimeHorizon(
        num_periods=1,
        delta_t=1.0,
        tariff_partition=TariffPartition(peak_periods=[1], offpeak_periods=[], shoulder_periods=[]),
    )
    economics = Economics(
        energy_tariffs=EnergyTariffs(c_peak=10.0, c_offpeak=0.0, c_shoulder=0.0),
        demand_charge_rate=100.0,
        fixed_charge=0.0,
        purchase_costs={},
        setup_costs={},
        holding_costs={},
        penalty_costs={},
    )
    electrical = ElectricalParameters(power_factor=1.0, contract_limit_kva=100.0)
    demand = [DemandOrder(resource_id="FIN", period=1, quantity=36.0)]

    return FactoryConfiguration(
        schema_version="0.1.0",
        contract_title="V0.1",
        freeze_vector="(A,A,A,A,B,A,A,A)",
        configuration_policy=ConfigurationPolicy(allow_demand_shortfall=False),
        time_horizon=time_horizon,
        resources=resources,
        processes=processes,
        machines=machines,
        economics=economics,
        electrical_parameters=electrical,
        demand=demand,
    )
