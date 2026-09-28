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

## Development Identity Bootstrap

With a reachable PostgreSQL database configured through `DATABASE_URL`, apply the
existing migrations and create a development administrator interactively:

```bash
python -m alembic upgrade head
python -m apps.cli.create_dev_admin
```

The bootstrap command is disabled unless `ENVIRONMENT=development`. It prompts
for the account details without echoing the password, creates an active
`ADMIN` membership in the development organization, and seeds the existing
role/permission tables. Re-running it does not reset an existing password or
change an existing account's role; it refuses to elevate an existing account
that lacks an active administrator membership. Do not use development
credentials or this command in production.
