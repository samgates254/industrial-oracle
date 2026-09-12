"""Factory root configuration object for V0.1."""

from typing import List
from pydantic import BaseModel, Field
from .demand import DemandOrder
from .economics import Economics
from .electrical import ElectricalParameters
from .machines import Machine
from .processes import Process
from .resources import Resource
from .time import TimeHorizon


class ConfigurationPolicy(BaseModel):
    """Governance and execution policy flags."""

    allow_demand_shortfall: bool = False
    numerical_tolerance_epsilon: float = 1e-6
    base_currency: str = "KSh"

    class Config:
        frozen = True


class FactoryConfiguration(BaseModel):
    """Authoritative root industrial system configuration."""

    schema_version: str
    contract_title: str
    freeze_vector: str

    configuration_policy: ConfigurationPolicy = Field(
        default_factory=ConfigurationPolicy
    )
    time_horizon: TimeHorizon

    resources: List[Resource]
    processes: List[Process]
    machines: List[Machine]

    economics: Economics
    electrical_parameters: ElectricalParameters

    demand: List[DemandOrder]

    class Config:
        frozen = True
