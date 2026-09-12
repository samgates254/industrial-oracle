# Web Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement real API endpoints for Industrial Oracle web application by integrating with core engine.

**Architecture:** Use `FastAPI` for API endpoints. Utilize existing `industrial_oracle` domain modules (`cli.main`, `normalization`, `model.compiler`) to perform backend processing.

**Tech Stack:** `FastAPI`, `Pydantic` (for input validation), `industrial_oracle` domain.

---

### Task 1: Setup Infrastructure & Validate Endpoint

**Files:**
- Modify: `src/industrial_oracle/web/app.py`
- Test: `tests/web/test_api_validate.py`

- [ ] **Step 1: Create failing test for `POST /api/validate`**

```python
import pytest
from fastapi.testclient import TestClient
from industrial_oracle.web.app import app

client = TestClient(app)

def test_validate_endpoint():
    # Use a dummy yaml payload
    data = "contract_title: test\ntime_horizon:\n  num_periods: 1\n  delta_t: 1"
    response = client.post("/api/validate", data=data)
    # Expecting failure for now as the endpoint is not implemented
    assert response.status_code == 200
    assert response.json()["status"] == "success"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/web/test_api_validate.py`
Expected: FAIL

- [ ] **Step 3: Implement minimal `/api/validate`**

Modify `src/industrial_oracle/web/app.py` to import `industrial_oracle.cli.main.parse_and_validate_configuration` and use it in `/api/validate`.

```python
from fastapi import FastAPI, Request, HTTPException
import yaml
from industrial_oracle.cli.main import parse_and_validate_configuration

# ... (app setup)

@app.post("/api/validate")
async def validate_model(request: Request):
    try:
        body = await request.body()
        data = yaml.safe_load(body)
        parse_and_validate_configuration(data)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/web/test_api_validate.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/industrial_oracle/web/app.py tests/web/test_api_validate.py
git commit -m "feat: implement /api/validate endpoint"
```

### Task 2: Implement `/api/inspect`

**Files:**
- Modify: `src/industrial_oracle/web/app.py`
- Test: `tests/web/test_api_inspect.py`

- [ ] **Step 1: Write failing test**
- [ ] **Step 2: Run test**
- [ ] **Step 3: Implement**
- [ ] **Step 4: Run test**
- [ ] **Step 5: Commit**

(Follow same pattern as Task 1 using `ModelCompiler`)

### Task 3: Implement `/api/run`

**Files:**
- Modify: `src/industrial_oracle/web/app.py`
- Test: `tests/web/test_api_run.py`

(Follow same pattern using `DiagnosticsEngine` and `HiGHSSolver`)

### Task 4: Integration & Regression Tests

- [ ] **Step 1: Run original 170 tests**
- [ ] **Step 2: Run new integration tests**
- [ ] **Step 3: Commit**
