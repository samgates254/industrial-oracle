"""Data Transfer Objects for Outbox, Event Query, and Webhooks."""

from datetime import datetime
from typing import Any, Dict, List, Optional
try:
    from pydantic import BaseModel, Field
except ImportError:
    class BaseModel:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)


class OutboxEventDTO(BaseModel):
    id: str
    organization_id: str
    event_id: str
    event_type: str
    aggregate_type: str
    aggregate_id: str
    payload: Dict[str, Any]
    occurred_at: str
    created_at: str
    status: str
    attempts: int
    available_at: str
    processed_at: Optional[str] = None
    last_error: Optional[str] = None
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None
    version: int


class EventQueryFilterDTO(BaseModel):
    event_type: Optional[str] = None
    aggregate_type: Optional[str] = None
    aggregate_id: Optional[str] = None
    status: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    page: int = 1
    page_size: int = 50


class OutboxRetryResponseDTO(BaseModel):
    id: str
    event_id: str
    status: str
    attempts: int
    available_at: str
    message: str


class WebhookCreateDTO(BaseModel):
    name: str
    url: str
    subscribed_event_types: Optional[List[str]] = None
    secret: Optional[str] = None


class WebhookUpdateDTO(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    subscribed_event_types: Optional[List[str]] = None


class WebhookResponseDTO(BaseModel):
    id: str
    organization_id: str
    name: str
    url: str
    active: bool
    subscribed_event_types: List[str]
    created_at: str
    updated_at: str
    secret: str  # Masked secret


class OutboxHealthDTO(BaseModel):
    pending_count: int
    failed_count: int
    processing_count: int
    published_count: int
    oldest_pending_age_seconds: Optional[float] = None
