"""Integration tests for authentication endpoints."""

import asyncio
from datetime import timedelta
import unittest
import uuid
from fastapi.testclient import TestClient

from apps.api.main import app
from industrial_oracle.core.security import create_access_token, hash_password
from industrial_oracle.identity.domain.models import User
from industrial_oracle.identity.infrastructure.repository import user_repo
from industrial_oracle.organization.domain.models import Membership, Organization
from industrial_oracle.organization.infrastructure.repository import (
    membership_repo,
    organization_repo,
)


class TestAuthAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.raw_password = "SecurePassword123!"
        self.user = User(
            email="auth_tester@example.com",
            password_hash=hash_password(self.raw_password),
            full_name="Auth Tester",
        )
        self.org = Organization(name="Auth Test Org", slug="auth-test-org")
        self.membership = Membership(
            user_id=self.user.id,
            organization_id=self.org.id,
            role="ADMIN",
        )

        async def setup():
            await user_repo.add(self.user)
            await organization_repo.add(self.org)
            await membership_repo.add(self.membership)

        asyncio.run(setup())

    def test_valid_login(self):
        response = self.client.post(
            "/api/v1/auth/login",
            json={"email": "auth_tester@example.com", "password": self.raw_password},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["token_type"], "bearer")
        self.assertGreater(data["expires_in"], 0)

    def test_invalid_password_returns_401(self):
        response = self.client.post(
            "/api/v1/auth/login",
            json={"email": "auth_tester@example.com", "password": "WrongPassword!"},
        )
        self.assertEqual(response.status_code, 401)
        data = response.json()
        self.assertIn("error", data)
        self.assertEqual(data["error"]["code"], "UNAUTHORIZED")
        self.assertEqual(data["error"]["message"], "Invalid email or password.")

    def test_nonexistent_user_returns_identical_401(self):
        response = self.client.post(
            "/api/v1/auth/login",
            json={"email": "nonexistent@example.com", "password": "AnyPassword123!"},
        )
        self.assertEqual(response.status_code, 401)
        data = response.json()
        # Ensure identical error message to prevent user enumeration
        self.assertEqual(data["error"]["message"], "Invalid email or password.")

    def test_inactive_user_login_rejected(self):
        inactive_user = User(
            email="inactive@example.com",
            password_hash=hash_password(self.raw_password),
            full_name="Inactive User",
            is_active=False,
        )
        asyncio.run(user_repo.add(inactive_user))

        response = self.client.post(
            "/api/v1/auth/login",
            json={"email": "inactive@example.com", "password": self.raw_password},
        )
        self.assertEqual(response.status_code, 401)
        data = response.json()
        self.assertIn("inactive", data["error"]["message"].lower())

    def test_get_me_profile_with_token(self):
        token = create_access_token(self.user.id, self.user.email)
        response = self.client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["email"], self.user.email)
        self.assertEqual(data["full_name"], self.user.full_name)
        self.assertNotIn("password", data)
        self.assertNotIn("password_hash", data)
        self.assertEqual(len(data["memberships"]), 1)
        self.assertEqual(data["memberships"][0]["role"], "ADMIN")

    def test_get_me_without_token_returns_401(self):
        response = self.client.get("/api/v1/users/me")
        self.assertEqual(response.status_code, 401)

    def test_get_me_with_expired_token_returns_401(self):
        expired_token = create_access_token(self.user.id, self.user.email, expires_delta=timedelta(seconds=-5))
        response = self.client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
