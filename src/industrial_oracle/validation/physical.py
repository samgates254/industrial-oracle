"""Level 2 Physical and Parameter Sanity Validation."""

from typing import Optional, Set
from industrial_oracle.domain.demand import DemandOrder
from industrial_oracle.domain.economics import Economics
from industrial_oracle.domain.electrical import ElectricalParameters
from industrial_oracle.domain.factory import ConfigurationPolicy, FactoryConfiguration
from industrial_oracle.domain.machines import Machine
from industrial_oracle.domain.processes import Process
from industrial_oracle.domain.resources import Resource
from industrial_oracle.domain.time import TimeHorizon
from .exceptions import PhysicalValidationError, SchemaValidationError
from .schema import (
    check_finite_number,
    check_mapping_finite_numbers,
    check_string_non_empty,
    check_strict_bool,
    check_strict_float,
    check_strict_int,
)


def validate_resource(res: Resource, num_periods: Optional[int] = None) -> None:
    """Validate Level 1 & Level 2 sanity for Resource."""
    # Level 1 Schema / Type
    check_string_non_empty(res.resource_id, "Resource", "resource_id")
    check_strict_float(res.initial_stock, f"Resource {res.resource_id}", "initial_stock")
    check_strict_float(res.safety_stock, f"Resource {res.resource_id}", "safety_stock")
    check_strict_float(res.max_storage, f"Resource {res.resource_id}", "max_storage")
    check_strict_bool(res.is_purchasable, f"Resource {res.resource_id}", "is_purchasable")

    # Level 2 Physical Sanity
    if res.initial_stock < 0.0:
        raise PhysicalValidationError(
            f"Resource {res.resource_id}: initial_stock={res.initial_stock} must be non-negative."
        )
    if res.safety_stock < 0.0:
        raise PhysicalValidationError(
            f"Resource {res.resource_id}: safety_stock={res.safety_stock} must be non-negative."
        )
    if res.max_storage < 0.0:
        raise PhysicalValidationError(
            f"Resource {res.resource_id}: max_storage={res.max_storage} must be non-negative."
        )
    if res.safety_stock > res.max_storage:
        raise PhysicalValidationError(
            f"Resource {res.resource_id}: safety_stock={res.safety_stock} exceeds max_storage={res.max_storage}."
        )

    if res.supply_cap is not None:
        if not isinstance(res.supply_cap, list):
            raise SchemaValidationError(
                f"Resource {res.resource_id}: supply_cap must be a list."
            )
        for idx, cap in enumerate(res.supply_cap):
            check_strict_float(cap, f"Resource {res.resource_id}", f"supply_cap[{idx}]")
            if cap < 0.0:
                raise PhysicalValidationError(
                    f"Resource {res.resource_id}: supply_cap[{idx}]={cap} must be non-negative."
                )
        if num_periods is not None and len(res.supply_cap) != num_periods:
            raise PhysicalValidationError(
                f"Resource {res.resource_id}: supply_cap length {len(res.supply_cap)} "
                f"does not match horizon length {num_periods}."
            )


def validate_process(proc: Process) -> None:
    """Validate Level 1 & Level 2 sanity for Process."""
    # Level 1 Schema / Type
    check_string_non_empty(proc.process_id, "Process", "process_id")
    check_mapping_finite_numbers(proc.input_coefficients, f"Process {proc.process_id}", "input_coefficients")
    check_mapping_finite_numbers(proc.output_coefficients, f"Process {proc.process_id}", "output_coefficients")

    # Level 2 Physical Sanity
    for r_id, a_rp in proc.input_coefficients.items():
        if a_rp < 0.0:
            raise PhysicalValidationError(
                f"Process {proc.process_id}: input coefficient for '{r_id}'={a_rp} must be non-negative."
            )

    for r_id, b_rp in proc.output_coefficients.items():
        if b_rp < 0.0:
            raise PhysicalValidationError(
                f"Process {proc.process_id}: output coefficient for '{r_id}'={b_rp} must be non-negative."
            )

    if len(proc.input_coefficients) == 0 and len(proc.output_coefficients) == 0:
        raise PhysicalValidationError(
            f"Process {proc.process_id}: both input and output coefficient mappings are empty."
        )


def validate_machine(mach: Machine) -> None:
    """Validate Level 1 & Level 2 sanity for Machine."""
    # Level 1 Schema / Type
    check_string_non_empty(mach.machine_id, "Machine", "machine_id")
    check_strict_float(mach.capacity_rate, f"Machine {mach.machine_id}", "capacity_rate")
    check_strict_float(mach.min_load_rate, f"Machine {mach.machine_id}", "min_load_rate")
    check_strict_float(mach.fixed_power, f"Machine {mach.machine_id}", "fixed_power")
    check_strict_int(mach.initial_state, f"Machine {mach.machine_id}", "initial_state")

    if not isinstance(mach.compatible_processes, list):
        raise SchemaValidationError(
            f"Machine {mach.machine_id}: compatible_processes must be a list."
        )
    for idx, p_id in enumerate(mach.compatible_processes):
        check_string_non_empty(p_id, f"Machine {mach.machine_id}", f"compatible_processes[{idx}]")

    check_mapping_finite_numbers(mach.variable_energy, f"Machine {mach.machine_id}", "variable_energy")

    # Level 2 Physical Sanity
    if mach.capacity_rate <= 0.0:
        raise PhysicalValidationError(
            f"Machine {mach.machine_id}: capacity_rate={mach.capacity_rate} must be strictly positive."
        )
    if mach.min_load_rate < 0.0:
        raise PhysicalValidationError(
            f"Machine {mach.machine_id}: min_load_rate={mach.min_load_rate} must be non-negative."
        )
    if mach.min_load_rate > mach.capacity_rate:
        raise PhysicalValidationError(
            f"Machine {mach.machine_id}: min_load_rate={mach.min_load_rate} exceeds capacity_rate={mach.capacity_rate}."
        )
    if mach.fixed_power < 0.0:
        raise PhysicalValidationError(
            f"Machine {mach.machine_id}: fixed_power={mach.fixed_power} must be non-negative."
        )
    if mach.initial_state not in (0, 1):
        raise PhysicalValidationError(
            f"Machine {mach.machine_id}: initial_state={mach.initial_state} must be binary (0 or 1)."
        )

    for p_id, e_var in mach.variable_energy.items():
        if e_var < 0.0:
            raise PhysicalValidationError(
                f"Machine {mach.machine_id}: variable_energy for '{p_id}'={e_var} must be non-negative."
            )


def validate_time_horizon(th: TimeHorizon) -> None:
    """Validate Level 1 & Level 2 sanity for TimeHorizon."""
    # Level 1 Schema / Type
    check_strict_int(th.num_periods, "TimeHorizon", "num_periods")
    check_strict_float(th.delta_t, "TimeHorizon", "delta_t")

    if th.num_periods < 1:
        raise PhysicalValidationError(
            f"TimeHorizon: num_periods={th.num_periods} must be at least 1."
        )
    if th.delta_t <= 0.0:
        raise PhysicalValidationError(
            f"TimeHorizon: delta_t={th.delta_t} must be strictly positive."
        )

    partition = th.tariff_partition
    partition_groups = [
        ("peak_periods", partition.peak_periods),
        ("offpeak_periods", partition.offpeak_periods),
        ("shoulder_periods", partition.shoulder_periods),
    ]

    for name, periods in partition_groups:
        if not isinstance(periods, list):
            raise SchemaValidationError(f"Tariff partition {name} must be a list.")
        for t in periods:
            if type(t) is not int:
                raise SchemaValidationError(
                    f"Period identifier {t} in {name} must be a strict integer."
                )
            if t < 1 or t > th.num_periods:
                raise PhysicalValidationError(
                    f"Period {t} in {name} is outside valid horizon [1, {th.num_periods}]."
                )
        if len(periods) != len(set(periods)):
            raise PhysicalValidationError(
                f"Tariff partition {name} contains duplicate periods."
            )

    s_peak = set(partition.peak_periods)
    s_offpeak = set(partition.offpeak_periods)
    s_shoulder = set(partition.shoulder_periods)

    if s_peak.intersection(s_offpeak):
        raise PhysicalValidationError(
            f"Tariff classes peak and offpeak overlap: {sorted(s_peak.intersection(s_offpeak))}."
        )
    if s_peak.intersection(s_shoulder):
        raise PhysicalValidationError(
            f"Tariff classes peak and shoulder overlap: {sorted(s_peak.intersection(s_shoulder))}."
        )
    if s_offpeak.intersection(s_shoulder):
        raise PhysicalValidationError(
            f"Tariff classes offpeak and shoulder overlap: {sorted(s_offpeak.intersection(s_shoulder))}."
        )

    union_periods = s_peak.union(s_offpeak).union(s_shoulder)
    expected_periods = set(range(1, th.num_periods + 1))
    if union_periods != expected_periods:
        missing = sorted(expected_periods - union_periods)
        extra = sorted(union_periods - expected_periods)
        raise PhysicalValidationError(
            f"Tariff partition does not form a complete cover of 1..{th.num_periods}. "
            f"Missing: {missing}, Extra: {extra}."
        )


def validate_economics(econ: Economics) -> None:
    """Validate Level 1 & Level 2 sanity for Economics."""
    # Level 1 Schema / Type
    check_strict_float(econ.energy_tariffs.c_peak, "EnergyTariffs", "c_peak")
    check_strict_float(econ.energy_tariffs.c_offpeak, "EnergyTariffs", "c_offpeak")
    check_strict_float(econ.energy_tariffs.c_shoulder, "EnergyTariffs", "c_shoulder")
    check_strict_float(econ.demand_charge_rate, "Economics", "demand_charge_rate")
    check_strict_float(econ.fixed_charge, "Economics", "fixed_charge")

    check_mapping_finite_numbers(econ.purchase_costs, "Economics", "purchase_costs")
    check_mapping_finite_numbers(econ.setup_costs, "Economics", "setup_costs")
    check_mapping_finite_numbers(econ.holding_costs, "Economics", "holding_costs")
    check_mapping_finite_numbers(econ.penalty_costs, "Economics", "penalty_costs")

    # Level 2 Physical Sanity
    if econ.energy_tariffs.c_peak < 0.0:
        raise PhysicalValidationError(
            f"Economics: c_peak={econ.energy_tariffs.c_peak} must be non-negative."
        )
    if econ.energy_tariffs.c_offpeak < 0.0:
        raise PhysicalValidationError(
            f"Economics: c_offpeak={econ.energy_tariffs.c_offpeak} must be non-negative."
        )
    if econ.energy_tariffs.c_shoulder < 0.0:
        raise PhysicalValidationError(
            f"Economics: c_shoulder={econ.energy_tariffs.c_shoulder} must be non-negative."
        )

    if econ.demand_charge_rate < 0.0:
        raise PhysicalValidationError(
            f"Economics: demand_charge_rate={econ.demand_charge_rate} must be non-negative."
        )
    if econ.fixed_charge < 0.0:
        raise PhysicalValidationError(
            f"Economics: fixed_charge={econ.fixed_charge} must be non-negative."
        )

    cost_maps = [
        ("purchase_costs", econ.purchase_costs),
        ("setup_costs", econ.setup_costs),
        ("holding_costs", econ.holding_costs),
        ("penalty_costs", econ.penalty_costs),
    ]
    for map_name, cost_map in cost_maps:
        for k, v in cost_map.items():
            if v < 0.0:
                raise PhysicalValidationError(
                    f"Economics: {map_name}['{k}']={v} must be non-negative."
                )


def validate_electrical(elec: ElectricalParameters) -> None:
    """Validate Level 1 & Level 2 sanity for ElectricalParameters."""
    # Level 1 Schema / Type
    check_strict_float(elec.power_factor, "ElectricalParameters", "power_factor")
    check_strict_float(elec.contract_limit_kva, "ElectricalParameters", "contract_limit_kva")

    # Level 2 Physical Sanity
    if elec.power_factor <= 0.0 or elec.power_factor > 1.0:
        raise PhysicalValidationError(
            f"ElectricalParameters: power_factor={elec.power_factor} must satisfy 0 < cos(phi) <= 1."
        )
    if elec.contract_limit_kva <= 0.0:
        raise PhysicalValidationError(
            f"ElectricalParameters: contract_limit_kva={elec.contract_limit_kva} must be strictly positive."
        )


def validate_demand_order(order: DemandOrder, num_periods: Optional[int] = None) -> None:
    """Validate Level 1 & Level 2 sanity for DemandOrder."""
    # Level 1 Schema / Type
    check_string_non_empty(order.resource_id, "DemandOrder", "resource_id")
    check_strict_int(order.period, "DemandOrder", "period")
    check_strict_float(order.quantity, "DemandOrder", "quantity")

    # Level 2 Physical Sanity
    if order.quantity < 0.0:
        raise PhysicalValidationError(
            f"DemandOrder for '{order.resource_id}' at period {order.period}: "
            f"quantity={order.quantity} must be non-negative."
        )
    if num_periods is not None:
        if order.period < 1 or order.period > num_periods:
            raise PhysicalValidationError(
                f"DemandOrder for '{order.resource_id}': period={order.period} is outside valid horizon [1, {num_periods}]."
            )


def validate_configuration_policy(policy: ConfigurationPolicy) -> None:
    """Validate Level 1 & Level 2 sanity for ConfigurationPolicy."""
    check_strict_bool(policy.allow_demand_shortfall, "ConfigurationPolicy", "allow_demand_shortfall")
    check_strict_float(policy.numerical_tolerance_epsilon, "ConfigurationPolicy", "numerical_tolerance_epsilon")
    check_string_non_empty(policy.base_currency, "ConfigurationPolicy", "base_currency")

    if policy.numerical_tolerance_epsilon <= 0.0:
        raise PhysicalValidationError(
            f"ConfigurationPolicy: numerical_tolerance_epsilon={policy.numerical_tolerance_epsilon} "
            f"must be strictly positive."
        )


def validate_factory(factory: FactoryConfiguration) -> None:
    """Deterministic factory-level validation in ordered sequence."""
    # 1. Factory metadata
    check_string_non_empty(factory.schema_version, "FactoryConfiguration", "schema_version")
    check_string_non_empty(factory.contract_title, "FactoryConfiguration", "contract_title")
    check_string_non_empty(factory.freeze_vector, "FactoryConfiguration", "freeze_vector")

    # 2. Configuration policy
    validate_configuration_policy(factory.configuration_policy)

    # 3. Time horizon
    validate_time_horizon(factory.time_horizon)
    num_periods = factory.time_horizon.num_periods

    # 4. Resources
    seen_resources: Set[str] = set()
    for res in factory.resources:
        if res.resource_id in seen_resources:
            raise PhysicalValidationError(
                f"Duplicate resource_id detected: '{res.resource_id}'."
            )
        seen_resources.add(res.resource_id)
        validate_resource(res, num_periods=num_periods)

    # 5. Processes
    seen_processes: Set[str] = set()
    for proc in factory.processes:
        if proc.process_id in seen_processes:
            raise PhysicalValidationError(
                f"Duplicate process_id detected: '{proc.process_id}'."
            )
        seen_processes.add(proc.process_id)
        validate_process(proc)

    # 6. Machines
    seen_machines: Set[str] = set()
    for mach in factory.machines:
        if mach.machine_id in seen_machines:
            raise PhysicalValidationError(
                f"Duplicate machine_id detected: '{mach.machine_id}'."
            )
        seen_machines.add(mach.machine_id)
        validate_machine(mach)

    # 7. Economics
    validate_economics(factory.economics)

    # 8. Electrical parameters
    validate_electrical(factory.electrical_parameters)

    # 9. Demand
    for order in factory.demand:
        validate_demand_order(order, num_periods=num_periods)
