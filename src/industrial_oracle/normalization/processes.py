"""Canonical process transformation representation."""

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping
from industrial_oracle.domain.processes import Process
from .identifiers import normalize_identifier


@dataclass(frozen=True)
class NormalizedProcess:
    """Canonical process transformation with deterministically ordered read-only mappings."""

    process_id: str
    input_coefficients: Mapping[str, float]
    output_coefficients: Mapping[str, float]


def normalize_process(proc: Process) -> NormalizedProcess:
    """Normalize Process entity with sorted resource keys and read-only mappings."""
    canonical_id = normalize_identifier(proc.process_id)

    sorted_inputs = {
        normalize_identifier(r): float(c)
        for r, c in sorted(proc.input_coefficients.items(), key=lambda item: normalize_identifier(item[0]))
    }
    sorted_outputs = {
        normalize_identifier(r): float(c)
        for r, c in sorted(proc.output_coefficients.items(), key=lambda item: normalize_identifier(item[0]))
    }

    return NormalizedProcess(
        process_id=canonical_id,
        input_coefficients=MappingProxyType(sorted_inputs),
        output_coefficients=MappingProxyType(sorted_outputs),
    )
