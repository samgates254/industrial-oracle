# Industrial Cost & Optimization Oracle V0.1

Generic, product-agnostic, discrete-time constrained industrial cost and optimization engine.

## Architecture Pipeline
1. **Domain Model (`domain/`)**: Ingestion of raw industrial system configurations.
2. **Validation (`validation/`)**: Level 1 (Schema/Type) and Level 2 (Physical Sanity) checking.
3. **Normalization (`normalization/`)**: Canonical representation, unit conversions, deterministic ordering, and indexing.
4. **Mathematical Model (`model/`)**: Variable registry, constraint compilation, and objective assembly (M2+).
5. **Solver (`solver/`)**: Solver-independent mathematical adapter interface.

## Running Tests
Execute from the repository root:
```bash
python3 -m unittest discover -s tests -p "test_*.py" -v
```
