"""ModelCompiler generating CanonicalModel from NormalizedFactory."""

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping, Tuple
from industrial_oracle.normalization.factory import NormalizedFactory
from .constraints import compile_constraints
from .equations import SparseRow
from .objective import compile_objective
from .variables import VariableRegistry, build_variable_registry


@dataclass(frozen=True)
class CanonicalModel:
    """Authoritative solver-independent canonical LP/MILP matrix representation."""

    c: Tuple[float, ...]
    fixed_charge: float
    A_ub_sparse: Tuple[SparseRow, ...]
    A_ub_dense: Tuple[Tuple[float, ...], ...]
    b_ub: Tuple[float, ...]
    A_eq_sparse: Tuple[SparseRow, ...]
    A_eq_dense: Tuple[Tuple[float, ...], ...]
    b_eq: Tuple[float, ...]
    l: Tuple[float, ...]
    u: Tuple[float, ...]
    integer_indices: Tuple[int, ...]
    variable_registry: VariableRegistry
    eq_row_ids: Tuple[str, ...]
    ub_row_ids: Tuple[str, ...]
    eq_row_to_id: Mapping[int, str]
    eq_id_to_row: Mapping[str, int]
    ub_row_to_id: Mapping[int, str]
    ub_id_to_row: Mapping[str, int]

    @property
    def num_variables(self) -> int:
        return len(self.c)

    @property
    def num_equalities(self) -> int:
        return len(self.b_eq)

    @property
    def num_inequalities(self) -> int:
        return len(self.b_ub)


class ModelCompiler:
    """Compiles NormalizedFactory into CanonicalModel."""

    @staticmethod
    def compile(factory: NormalizedFactory) -> CanonicalModel:
        """Deterministic compilation pipeline."""
        registry = build_variable_registry(factory)
        c, fixed_charge = compile_objective(factory, registry)
        eq_rows, ub_rows = compile_constraints(factory, registry)

        N_vars = len(registry)
        A_eq_dense = tuple(row.to_dense(N_vars) for row in eq_rows)
        b_eq = tuple(row.rhs for row in eq_rows)
        eq_row_ids = tuple(row.equation_id for row in eq_rows)

        A_ub_dense = tuple(row.to_dense(N_vars) for row in ub_rows)
        b_ub = tuple(row.rhs for row in ub_rows)
        ub_row_ids = tuple(row.equation_id for row in ub_rows)

        # Bijective equality row mappings (row_index <-> equation_id)
        eq_row_to_id = {idx: eq_id for idx, eq_id in enumerate(eq_row_ids)}
        eq_id_to_row = {eq_id: idx for idx, eq_id in enumerate(eq_row_ids)}

        # Bijective inequality row mappings (row_index <-> equation_id)
        ub_row_to_id = {idx: ub_id for idx, ub_id in enumerate(ub_row_ids)}
        ub_id_to_row = {ub_id: idx for idx, ub_id in enumerate(ub_row_ids)}

        return CanonicalModel(
            c=c,
            fixed_charge=fixed_charge,
            A_ub_sparse=ub_rows,
            A_ub_dense=A_ub_dense,
            b_ub=b_ub,
            A_eq_sparse=eq_rows,
            A_eq_dense=A_eq_dense,
            b_eq=b_eq,
            l=registry.lower_bounds,
            u=registry.upper_bounds,
            integer_indices=registry.integer_indices,
            variable_registry=registry,
            eq_row_ids=eq_row_ids,
            ub_row_ids=ub_row_ids,
            eq_row_to_id=MappingProxyType(eq_row_to_id),
            eq_id_to_row=MappingProxyType(eq_id_to_row),
            ub_row_to_id=MappingProxyType(ub_row_to_id),
            ub_id_to_row=MappingProxyType(ub_id_to_row),
        )
