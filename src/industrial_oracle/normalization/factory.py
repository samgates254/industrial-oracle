"""Root canonical factory normalization pipeline."""

from dataclasses import dataclass
from typing import Tuple
from industrial_oracle.domain.factory import ConfigurationPolicy, FactoryConfiguration
from industrial_oracle.validation.physical import validate_factory
from .demand import NormalizedDemand, normalize_demand
from .economics import NormalizedEconomics, normalize_economics
from .electrical import NormalizedElectricalParameters, normalize_electrical
from .indexes import CanonicalIndexSets, build_canonical_indexes
from .machines import NormalizedMachine, normalize_machine
from .processes import NormalizedProcess, normalize_process
from .resources import NormalizedResource, normalize_resource
from .tariffs import NormalizedTariffSchedule, normalize_tariffs
from .time import NormalizedTimeHorizon, normalize_time_horizon


@dataclass(frozen=True)
class NormalizedFactory:
    """Authoritative canonical normalized representation of an industrial system."""

    schema_version: str
    contract_title: str
    freeze_vector: str
    configuration_policy: ConfigurationPolicy
    time_horizon: NormalizedTimeHorizon
    tariff_schedule: NormalizedTariffSchedule
    resources: Tuple[NormalizedResource, ...]
    processes: Tuple[NormalizedProcess, ...]
    machines: Tuple[NormalizedMachine, ...]
    economics: NormalizedEconomics
    electrical: NormalizedElectricalParameters
    demand: NormalizedDemand
    indexes: CanonicalIndexSets


def normalize_factory(factory: FactoryConfiguration, validate: bool = True) -> NormalizedFactory:
    """Execute deterministic canonical normalization on a validated factory configuration."""
    if validate:
        validate_factory(factory)

    norm_time = normalize_time_horizon(factory.time_horizon)
    norm_tariffs = normalize_tariffs(factory.time_horizon, factory.economics)

    norm_resources = tuple(
        sorted(
            (normalize_resource(r, norm_time.num_periods) for r in factory.resources),
            key=lambda item: item.resource_id,
        )
    )

    norm_processes = tuple(
        sorted(
            (normalize_process(p) for p in factory.processes),
            key=lambda item: item.process_id,
        )
    )

    norm_machines = tuple(
        sorted(
            (normalize_machine(m) for m in factory.machines),
            key=lambda item: item.machine_id,
        )
    )

    norm_econ = normalize_economics(factory.economics)
    norm_elec = normalize_electrical(factory.electrical_parameters)
    norm_demand = normalize_demand(factory.demand)

    indexes = build_canonical_indexes(
        resources=norm_resources,
        processes=norm_processes,
        machines=norm_machines,
        time_horizon=norm_time,
    )

    return NormalizedFactory(
        schema_version=factory.schema_version,
        contract_title=factory.contract_title,
        freeze_vector=factory.freeze_vector,
        configuration_policy=factory.configuration_policy,
        time_horizon=norm_time,
        tariff_schedule=norm_tariffs,
        resources=norm_resources,
        processes=norm_processes,
        machines=norm_machines,
        economics=norm_econ,
        electrical=norm_elec,
        demand=norm_demand,
        indexes=indexes,
    )
