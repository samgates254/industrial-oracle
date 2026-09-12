# Industrial Oracle Web Design

## Overview
Implement API endpoints for the Industrial Oracle V1 web application by integrating with the core domain/cli logic.

## Architecture
- FastAPI application in `src/industrial_oracle/web/app.py`.
- Stateless design. All operations take a YAML configuration as input.
- Endpoints:
  - `POST /api/validate`
  - `POST /api/inspect`
  - `POST /api/run`
  - `GET /api/examples/{example_id}` (optional convenience)

## Data Flow
1. API endpoint receives YAML (str).
2. `app.py` invokes `industrial_oracle.cli.main.parse_and_validate_configuration(data)`.
3. If successful, processes the configuration using the respective module (normalization -> model -> solver/diagnostics).
4. Returns result as JSON.

## Error Handling
- Map custom exceptions (DomainValidationError, SchemaValidationError) to 400 Bad Request.

## Testing Strategy
- Add new integration tests in `tests/web/`.
- Ensure original 170 tests still pass.
