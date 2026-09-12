"""Integration tests for user management and RBAC authorization."""

import asyncio
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


class TestUserManagementAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.org = Organization(name="Operations Corp", slug=f"ops-corp-{uuid.uuid4().hex[:6]}")
        
        # Admin user
        self.admin = User(
            email=f"admin_{uuid.uuid4().hex[:6]}@example.com",
            password_hash=hash_password("AdminPass123!"),
            full_name="Admin User",
        )
        self.admin_membership = Membership(
            user_id=self.admin.id,
            organization_id=self.org.id,
            role="ADMIN",
        )

        # Operator user (has no users.create or users.read permission)
        self.operator = User(
            email=f"operator_{uuid.uuid4().hex[:6]}@example.com",
            password_hash=hash_password("OperatorPass123!"),
            full_name="Operator User",
        )
        self.operator_membership = Membership(
            user_id=self.operator.id,
            organization_id=self.org.id,
            role="OPERATOR",
        )

        async def init():
            await organization_repo.add(self.org)
            await user_repo.add(self.admin)
            await user_repo.add(self.operator)
            await membership_repo.add(self.admin_membership)
            await membership_repo.add(self.operator_membership)

        asyncio.run(init())

        self.admin_token = create_access_token(self.admin.id, self.admin.email)
        self.operator_token = create_access_token(self.operator.id, self.operator.email)

    def test_admin_can_list_users(self):
        response = self.client.get(
            "/api/v1/users",
            headers={
                "Authorization": f"Bearer {self.admin_token}",
                "X-Organization-ID": str(self.org.id),
            },
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 2)
        # Verify passwords never leaked in list responses
        for u in data:
            self.assertNotIn("password", u)
            self.assertNotIn("password_hash", u)

    def test_operator_cannot_list_users(self):
        response = self.client.get(
            "/api/v1/users",
            headers={
                "Authorization": f"Bearer {self.operator_token}",
                "X-Organization-ID": str(self.org.id),
            },
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["error"]["code"], "FORBIDDEN")

    def test_admin_can_create_user(self):
        new_email = f"engineer_{uuid.uuid4().hex[:6]}@example.com"
        payload = {
            "email": new_email,
            "password": "StrongPassword123!",
            "full_name": "New Engineer",
            "role": "ENGINEER",
        }
        response = self.client.post(
            "/api/v1/users",
            json=payload,
            headers={
                "Authorization": f"Bearer {self.admin_token}",
                "X-Organization-ID": str(self.org.id),
            },
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["email"], new_email)
        self.assertNotIn("password", data)
        self.assertNotIn("password_hash", data)

    def test_operator_cannot_create_user(self):
        payload = {
            "email": f"unauthorized_{uuid.uuid4().hex[:6]}@example.com",
            "password": "Password123!",
            "full_name": "Unauthorized Attempt",
            "role": "VIEWER",
        }
        response = self.client.post(
            "/api/v1/users",
            json=payload,
            headers={
                "Authorization": f"Bearer {self.operator_token}",
                "X-Organization-ID": str(self.org.id),
            },
        )
        self.assertEqual(response.status_code, 403)

    def test_admin_can_update_user(self):
        response = self.client.patch(
            f"/api/v1/users/{self.operator.id}",
            json={"full_name": "Updated Operator Name"},
            headers={
                "Authorization": f"Bearer {self.admin_token}",
                "X-Organization-ID": str(self.org.id),
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["full_name"], "Updated Operator Name")

    def test_admin_can_deactivate_user(self):
        response = self.client.patch(
            f"/api/v1/users/{self.operator.id}/status",
            json={"is_active": False},
            headers={
                "Authorization": f"Bearer {self.admin_token}",
                "X-Organization-ID": str(self.org.id),
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["is_active"])

        # Deactivated user should now be rejected at login
        login_res = self.client.post(
            "/api/v1/auth/login",
            json={"email": self.operator.email, "password": "OperatorPass123!"},
        )
        self.assertEqual(login_res.status_code, 401)


if __name__ == "__main__":
    unittest.main()
