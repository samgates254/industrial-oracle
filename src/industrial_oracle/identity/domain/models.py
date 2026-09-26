"""Identity domain models."""

from datetime import datetime, timezone
from typing import Optional
import uuid

from industrial_oracle.core.exceptions import BusinessRuleViolationException
from industrial_oracle.core.security import hash_password, verify_password
from industrial_oracle.shared.domain.entity import Entity


class User(Entity):
    """User entity representing authenticated human and service actors."""

    def __init__(
        self,
        email: str,
        password_hash: str,
        full_name: str,
        id: Optional[uuid.UUID] = None,
        is_active: bool = True,
        is_superuser: bool = False,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ) -> None:
        super().__init__(id=id, created_at=created_at, updated_at=updated_at)
        self.email = email.strip().lower()
        self.password_hash = password_hash
        self.full_name = full_name.strip()
        self.is_active = is_active
        self.is_superuser = is_superuser

    def verify_password(self, plain_password: str) -> bool:
        """Verifies candidate plaintext password against stored hash."""
        return verify_password(plain_password, self.password_hash)

    def change_password(self, new_plain_password: str) -> None:
        """Updates user's password hash."""
        if len(new_plain_password) < 8:
            raise BusinessRuleViolationException(
                "Password must be at least 8 characters in length.",
                rule_name="PASSWORD_MIN_LENGTH",
            )
        self.password_hash = hash_password(new_plain_password)
        self.updated_at = datetime.now(timezone.utc)

    def deactivate(self) -> None:
        """Deactivates account access."""
        self.is_active = False
        self.updated_at = datetime.now(timezone.utc)

    def activate(self) -> None:
        """Restores account access."""
        self.is_active = True
        self.updated_at = datetime.now(timezone.utc)

    def update_profile(self, full_name: Optional[str] = None, email: Optional[str] = None) -> None:
        """Updates profile attributes."""
        if full_name is not None and full_name.strip():
            self.full_name = full_name.strip()
        if email is not None and email.strip():
            self.email = email.strip().lower()
        self.updated_at = datetime.now(timezone.utc)
