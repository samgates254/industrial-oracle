"""Industrial Oracle API Main Application."""

import logging
import time
from datetime import datetime, timezone
import uuid
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from industrial_oracle.assets.api.router import router as assets_router
from industrial_oracle.inventory.api.router import router as inventory_router
from industrial_oracle.maintenance.api.router import router as maintenance_router
from industrial_oracle.operations.api.router import router as operations_router
from industrial_oracle.integrations.api.router import router as integration_router
from industrial_oracle.integrations.infrastructure.repository import outbox_repository
from industrial_oracle.core.config import settings
from industrial_oracle.core.database import db_manager
from industrial_oracle.core.exceptions import (
    DomainException,
    format_error_response,
)
from industrial_oracle.core.logging import (
    logger,
    request_id_ctx,
    setup_logging,
)
from industrial_oracle.core.redis import redis_manager
from industrial_oracle.identity.api.router import router as identity_router
from industrial_oracle.organization.api.router import router as organization_router

# Initialize structured logging
setup_logging(log_level=settings.LOG_LEVEL, json_format=(settings.LOG_FORMAT == "json"))

# Create FastAPI application instance
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Industrial Operations Intelligence, Simulation, and Optimization Platform",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# Configure Cross-Origin Resource Sharing
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_tracing_and_logging_middleware(request: Request, call_next: Any) -> Response:
    """Middleware attaching request_id, injecting contextvars, and logging request lifecycle."""
    req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = req_id
    token = request_id_ctx.set(req_id)

    start_time = time.perf_counter()
    logger.info("Incoming HTTP Request: %s %s", request.method, request.url.path)

    try:
        response: Response = await call_next(request)
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        response.headers["X-Request-ID"] = req_id
        logger.info(
            "HTTP Response completed: %s %s [status=%d] [%.2fms]",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response
    except DomainException as exc:
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.warning(
            "Domain Exception on %s %s [%.2fms]: %s",
            request.method,
            request.url.path,
            duration_ms,
            exc.message,
        )
        payload = format_error_response(
            code=exc.code,
            message=exc.message,
            request_id=req_id,
            details=exc.details,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=payload,
            headers={"X-Request-ID": req_id},
        )
    except Exception as exc:
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.error(
            "Unhandled exception processing HTTP request %s %s [%.2fms]: %s",
            request.method,
            request.url.path,
            duration_ms,
            exc,
            exc_info=True,
        )
        payload = format_error_response(
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected internal server error occurred. Please contact system support.",
            request_id=req_id,
            details={},
        )
        return JSONResponse(
            status_code=500,
            content=payload,
            headers={"X-Request-ID": req_id},
        )
    finally:
        request_id_ctx.reset(token)


# Exception Handlers for Route-Level Exceptions
@app.exception_handler(DomainException)
async def domain_exception_handler(request: Request, exc: DomainException) -> JSONResponse:
    """Handles domain and business logic exceptions using the standard error schema."""
    req_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    payload = format_error_response(
        code=exc.code,
        message=exc.message,
        request_id=req_id,
        details=exc.details,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=payload,
        headers={"X-Request-ID": req_id},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handles Pydantic request validation errors using the standard error schema."""
    req_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    errors_detail = []
    for err in exc.errors():
        errors_detail.append({
            "loc": err.get("loc"),
            "msg": err.get("msg"),
            "type": err.get("type"),
        })

    payload = format_error_response(
        code="VALIDATION_ERROR",
        message="Request parameters or body validation failed.",
        request_id=req_id,
        details={"validation_errors": errors_detail},
    )
    return JSONResponse(
        status_code=422,
        content=payload,
        headers={"X-Request-ID": req_id},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handles FastAPI HTTPExceptions using standard error schema."""
    req_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    code = "RESOURCE_NOT_FOUND" if exc.status_code == 404 else "HTTP_ERROR"
    payload = format_error_response(
        code=code,
        message=str(exc.detail),
        request_id=req_id,
        details={},
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=payload,
        headers={"X-Request-ID": req_id},
    )


# Observability Endpoints
@app.get("/health", tags=["Observability"])
async def get_health() -> Dict[str, Any]:
    """Liveness probe reporting process status."""
    pending_count = await outbox_repository.count_pending()
    failed_count = await outbox_repository.count_failed()
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "outbox": {
            "pending_events": pending_count,
            "failed_events": failed_count,
        },
    }


@app.get("/ready", tags=["Observability"])
async def get_readiness() -> JSONResponse:
    """Readiness probe verifying backing dependencies."""
    db_ok = await db_manager.check_health()
    redis_client = await redis_manager.get_client()
    redis_ok = await redis_client.ping()

    status = "ready" if (db_ok and redis_ok) else "degraded"
    status_code = 200 if status == "ready" else 503

    pending_count = await outbox_repository.count_pending()
    failed_count = await outbox_repository.count_failed()
    oldest_age = await outbox_repository.get_oldest_pending_age_seconds()

    return JSONResponse(
        status_code=status_code,
        content={
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": {
                "database": "up" if db_ok else "down",
                "redis": "up" if redis_ok else "down",
                "outbox": "up",
            },
            "outbox_metrics": {
                "pending_events": pending_count,
                "failed_events": failed_count,
                "oldest_pending_age_seconds": oldest_age,
            },
        },
    )


# Root API v1 Router
@app.get(f"{settings.API_V1_STR}/", tags=["System"])
async def get_api_v1_index() -> Dict[str, Any]:
    """Root metadata endpoint for API v1."""
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "api_version": "v1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "domains": [
            "identity",
            "organization",
            "assets",
            "operations",
            "inventory",
            "maintenance",
            "energy",
            "telemetry",
            "optimization",
            "audit",
            "integrations",
        ],
    }


# Include Domain Routers
app.include_router(identity_router)
app.include_router(organization_router)
app.include_router(assets_router)
app.include_router(operations_router)
app.include_router(maintenance_router)
app.include_router(inventory_router)
app.include_router(integration_router)


@app.on_event("startup")
async def startup_event() -> None:
    """Initializes backing connections on application start."""
    logger.info("Starting up %s v%s...", settings.PROJECT_NAME, settings.VERSION)
    db_manager.initialize()
    await redis_manager.initialize()


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Gracefully shuts down connection pools on application exit."""
    logger.info("Shutting down %s...", settings.PROJECT_NAME)
    await db_manager.close()
    await redis_manager.close()
