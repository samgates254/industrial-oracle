"""Webhook endpoint configuration and subscription filtering domain model."""

from datetime import datetime, timezone
import secrets
from typing import Any, Dict, List, Optional
import uuid


class WebhookEndpoint:
    """Represents an outbound webhook endpoint registered by an organization tenant."""

    def __init__(
        self,
        id: Optional[str] = None,
        organization_id: str = "",
        name: str = "",
        url: str = "",
        secret: Optional[str] = None,
        active: bool = True,
        subscribed_event_types: Optional[List[str]] = None,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
    ) -> None:
        now_str = datetime.now(timezone.utc).isoformat()
        self.id = id or str(uuid.uuid4())
        self.organization_id = str(organization_id)
        self.name = name
        self.url = url
        self.secret = secret or f"whsec_{secrets.token_hex(24)}"
        self.active = active
        self.subscribed_event_types = subscribed_event_types if subscribed_event_types is not None else ["*"]
        self.created_at = created_at or now_str
        self.updated_at = updated_at or now_str

    def activate(self) -> None:
        """Activates the webhook endpoint to receive notifications."""
        self.active = True
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def deactivate(self) -> None:
        """Deactivates the webhook endpoint, halting event dispatch."""
        self.active = False
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def matches_event(self, event_type: str) -> bool:
        """Evaluates whether this endpoint is subscribed to the specified event type."""
        import fnmatch
        if not self.active:
            return False
        if "*" in self.subscribed_event_types:
            return True
        for pattern in self.subscribed_event_types:
            if fnmatch.fnmatch(event_type, pattern):
                return True
        return False

    def masked_secret(self) -> str:
        """Returns a masked representation of the webhook signing secret for secure display."""
        if not self.secret:
            return ""
        if len(self.secret) <= 10:
            return "whsec_****"
        return f"{self.secret[:6]}****{self.secret[-4:]}"

    def to_dict(self, include_secret: bool = False) -> Dict[str, Any]:
        """Converts endpoint to dictionary representation with secret protection."""
        data = {
            "id": self.id,
            "organization_id": self.organization_id,
            "name": self.name,
            "url": self.url,
            "active": self.active,
            "subscribed_event_types": self.subscribed_event_types,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "secret": self.masked_secret() if not include_secret else self.secret,
        }
        return data
