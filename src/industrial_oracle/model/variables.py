"""Authoritative VariableRegistry and column mapping for LP/MILP compilation."""

import math
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping, Optional, Tuple
from industrial_oracle.normalization.factory import NormalizedFactory


@dataclass(frozen=True)
class VariableRecord:
    """Metadata and bounds for a single optimization variable column."""

    symbol: str
    indices: Tuple[Any, ...]
    column_index: int
    is_integer: bool
    lower_bound: float
    upper_bound: float
    unit: str


class VariableRegistry:
    """Bijective mapping between symbolic (symbol, index_tuple) and matrix column indices."""

    def __init__(self, records: Tuple[VariableRecord, ...]):
        self._records = records
        sym_map = {}
        idx_map = {}
        int_indices = []
        low_bounds = []
        up_bounds = []

        for rec in records:
            key = (rec.symbol, rec.indices)
            sym_map[key] = rec.column_index
            idx_map[rec.column_index] = rec
            if rec.is_integer:
                int_indices.append(rec.column_index)
            low_bounds.append(rec.lower_bound)
            up_bounds.append(rec.upper_bound)

        self._symbol_to_index: Mapping[Tuple[str, Tuple[Any, ...]], int] = MappingProxyType(sym_map)
        self._index_to_record: Mapping[int, VariableRecord] = MappingProxyType(idx_map)
        self._integer_indices: Tuple[int, ...] = tuple(int_indices)
        self._lower_bounds: Tuple[float, ...] = tuple(low_bounds)
        self._upper_bounds: Tuple[float, ...] = tuple(up_bounds)

    @property
    def records(self) -> Tuple[VariableRecord, ...]:
        return self._records

    @property
    def integer_indices(self) -> Tuple[int, ...]:
        return self._integer_indices

    @property
    def lower_bounds(self) -> Tuple[float, ...]:
        return self._lower_bounds

    @property
    def upper_bounds(self) -> Tuple[float, ...]:
        return self._upper_bounds

    def __len__(self) -> int:
        return len(self._records)

    def get_index(self, symbol: str, indices: Tuple[Any, ...]) -> int:
        key = (symbol, indices)
        if key not in self._symbol_to_index:
            raise KeyError(f"Variable not registered: {key}")
        return self._symbol_to_index[key]

    def get_record(self, column_index: int) -> VariableRecord:
        if column_index not in self._index_to_record:
            raise IndexError(f"Column index out of bounds: {column_index}")
        return self._index_to_record[column_index]


def build_variable_registry(factory: NormalizedFactory) -> VariableRegistry:
    """Construct deterministic variable columns matching the V0.1 contract."""
    records = []
    col = 0
    N_T = factory.time_horizon.num_periods
    delta_t = factory.time_horizon.delta_t
    R_purchasable = {r.resource_id for r in factory.resources if r.is_purchasable}
    R_finished = {r.resource_id for r in factory.resources if r.category == "FINISHED"}
    res_map = {r.resource_id: r for r in factory.resources}

    # 1. x_{m,p,t}
    for m in factory.machines:
        m_id = m.machine_id
        cap_val = m.capacity_rate_kg_per_h * delta_t
        for p_id in m.compatible_processes:
            for t in factory.time_horizon.periods:
                records.append(
                    VariableRecord(
                        symbol="x",
                        indices=(m_id, p_id, t),
                        column_index=col,
                        is_integer=False,
                        lower_bound=0.0,
                        upper_bound=cap_val,
                        unit="kg",
                    )
                )
                col += 1

    # 2. z_{m,t}
    for m in factory.machines:
        m_id = m.machine_id
        for t in factory.time_horizon.periods:
            records.append(
                VariableRecord(
                    symbol="z",
                    indices=(m_id, t),
                    column_index=col,
                    is_integer=True,
                    lower_bound=0.0,
                    upper_bound=1.0,
                    unit="-",
                )
            )
            col += 1

    # 3. Startup_{m,t}
    for m in factory.machines:
        m_id = m.machine_id
        for t in factory.time_horizon.periods:
            records.append(
                VariableRecord(
                    symbol="Startup",
                    indices=(m_id, t),
                    column_index=col,
                    is_integer=True,
                    lower_bound=0.0,
                    upper_bound=1.0,
                    unit="-",
                )
            )
            col += 1

    # 4. Inv_{r,t} for t in 1..N_T
    for r in factory.resources:
        r_id = r.resource_id
        s_stock = r.safety_stock
        m_storage = r.max_storage
        for t in factory.time_horizon.periods:
            records.append(
                VariableRecord(
                    symbol="Inv",
                    indices=(r_id, t),
                    column_index=col,
                    is_integer=False,
                    lower_bound=s_stock,
                    upper_bound=m_storage,
                    unit="kg",
                )
            )
            col += 1

    # 5. Receipts_{r,t}
    for r in factory.resources:
        if r.resource_id in R_purchasable:
            r_id = r.resource_id
            for t in factory.time_horizon.periods:
                cap_t = r.supply_cap[t - 1]
                records.append(
                    VariableRecord(
                        symbol="Receipts",
                        indices=(r_id, t),
                        column_index=col,
                        is_integer=False,
                        lower_bound=0.0,
                        upper_bound=cap_t,
                        unit="kg",
                    )
                )
                col += 1

    # 6. Ship_{r,t}
    for r in factory.resources:
        if r.resource_id in R_finished:
            r_id = r.resource_id
            for t in factory.time_horizon.periods:
                records.append(
                    VariableRecord(
                        symbol="Ship",
                        indices=(r_id, t),
                        column_index=col,
                        is_integer=False,
                        lower_bound=0.0,
                        upper_bound=math.inf,
                        unit="kg",
                    )
                )
                col += 1

    # 7. Short_{r,t} (only if soft mode enabled)
    if factory.configuration_policy.allow_demand_shortfall:
        for r in factory.resources:
            if r.resource_id in R_finished:
                r_id = r.resource_id
                for t in factory.time_horizon.periods:
                    records.append(
                        VariableRecord(
                            symbol="Short",
                            indices=(r_id, t),
                            column_index=col,
                            is_integer=False,
                            lower_bound=0.0,
                            upper_bound=math.inf,
                            unit="kg",
                        )
                    )
                    col += 1

    # 8. PeakKVA
    records.append(
        VariableRecord(
            symbol="PeakKVA",
            indices=(),
            column_index=col,
            is_integer=False,
            lower_bound=0.0,
            upper_bound=factory.electrical.contract_limit_kva,
            unit="kVA",
        )
    )
    col += 1

    return VariableRegistry(tuple(records))
