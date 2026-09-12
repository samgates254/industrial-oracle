"""SparseRow and EquationRegistry for linear model constraints."""

from dataclasses import dataclass
from types import MappingProxyType
from typing import Dict, Mapping, Tuple


@dataclass(frozen=True)
class SparseRow:
    """Sparse linear equation row: sum(coeffs[j] * y[j]) [rel] rhs."""

    equation_id: str
    coefficients: Mapping[int, float]
    rhs: float
    description: str

    def to_dense(self, num_vars: int) -> Tuple[float, ...]:
        """Convert sparse row to dense tuple of length num_vars."""
        dense = [0.0] * num_vars
        for col, val in self.coefficients.items():
            dense[col] = val
        return tuple(dense)


def make_sparse_row(
    equation_id: str,
    raw_coeffs: Dict[int, float],
    rhs: float,
    description: str,
    epsilon: float = 1e-12,
) -> SparseRow:
    """Create a deterministic SparseRow omitting zeros."""
    filtered = {
        col: val for col, val in sorted(raw_coeffs.items(), key=lambda x: x[0])
        if abs(val) > epsilon
    }
    return SparseRow(
        equation_id=equation_id,
        coefficients=MappingProxyType(filtered),
        rhs=float(rhs),
        description=description,
    )
