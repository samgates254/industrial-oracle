"""Canonical deterministic index sets and sparse compatibility relations."""

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping, Sequence, Tuple
from .identifiers import normalize_identifier
from .machines import NormalizedMachine
from .processes import NormalizedProcess
from .resources import NormalizedResource
from .time import NormalizedTimeHorizon


@dataclass(frozen=True)
class CanonicalIndexSets:
    """Canonical structural sets and read-only sparse compatibility mappings."""

    R: Tuple[str, ...]
    P: Tuple[str, ...]
    M: Tuple[str, ...]
    T: Tuple[int, ...]
    M_p: Mapping[str, Tuple[str, ...]]
    P_m: Mapping[str, Tuple[str, ...]]

    num_resources: int
    num_processes: int
    num_machines: int
    num_periods: int
    num_compatible_pairs: int


def build_canonical_indexes(
    resources: Sequence[NormalizedResource],
    processes: Sequence[NormalizedProcess],
    machines: Sequence[NormalizedMachine],
    time_horizon: NormalizedTimeHorizon,
) -> CanonicalIndexSets:
    """Build deterministic sorted index sets and read-only sparse compatibility maps."""
    canonical_R = tuple(sorted(normalize_identifier(r.resource_id) for r in resources))
    canonical_P = tuple(sorted(normalize_identifier(p.process_id) for p in processes))
    canonical_M = tuple(sorted(normalize_identifier(m.machine_id) for m in machines))
    canonical_T = time_horizon.periods

    # P_m: machine -> compatible processes (already normalized tuples)
    P_m = {}
    for m in machines:
        m_id = normalize_identifier(m.machine_id)
        P_m[m_id] = tuple(sorted(normalize_identifier(p) for p in m.compatible_processes))

    # M_p: process -> compatible machines
    p_to_machines = {p: [] for p in canonical_P}
    for m in machines:
        m_id = normalize_identifier(m.machine_id)
        for p in m.compatible_processes:
            p_clean = normalize_identifier(p)
            if p_clean in p_to_machines:
                p_to_machines[p_clean].append(m_id)

    M_p = {
        p: tuple(sorted(p_to_machines[p]))
        for p in canonical_P
    }

    total_pairs = sum(len(procs) for procs in P_m.values())

    return CanonicalIndexSets(
        R=canonical_R,
        P=canonical_P,
        M=canonical_M,
        T=canonical_T,
        M_p=MappingProxyType(M_p),
        P_m=MappingProxyType(P_m),
        num_resources=len(canonical_R),
        num_processes=len(canonical_P),
        num_machines=len(canonical_M),
        num_periods=len(canonical_T),
        num_compatible_pairs=total_pairs,
    )
