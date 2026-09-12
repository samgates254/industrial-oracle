"""Mandatory Cross-Tenant Security and Isolation Tests.

Hard Security Invariant:
DATA BELONGING TO ORGANIZATION A MUST NEVER BE READABLE, MUTABLE,
OR ACCESSIBLE BY A USER OF ORGANIZATION B.
"""

import asyncio
import unittest
import uuid
from fastapi.testclient import TestClient

from apps.api.main import app
from industrial_oracle.audit.application.service import audit_service
from industrial_oracle.audit.infrastructure.repository import audit_repo
from industrial_oracle.core.security import create_access_token, hash_password
from industrial_oracle.identity.domain.models import User
from industrial_oracle.identity.infrastructure.repository import user_repo
from industrial_oracle.organization.domain.models import Membership, Organization, Plant, Site
from industrial_oracle.organization.infrastructure.repository import (
    membership_repo,
    organization_repo,
    plant_repo,
    site_repo,
)


class TestTenantIsolationSecurity(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

        # 1. Organization A and its assets
        self.org_a = Organization(name="Organization Alpha", slug=f"org-alpha-{uuid.uuid4().hex[:6]}")
        self.user_a = User(
            email=f"admin_a_{uuid.uuid4().hex[:6]}@alpha.com",
            password_hash=hash_password("AlphaSecret123!"),
            full_name="Alpha Admin",
        )
        self.member_a_regular = User(
            email=f"staff_a_{uuid.uuid4().hex[:6]}@alpha.com",
            password_hash=hash_password("StaffPass123!"),
            full_name="Alpha Staff",
        )
        self.membership_a1 = Membership(user_id=self.user_a.id, organization_id=self.org_a.id, role="ADMIN")
        self.membership_a2 = Membership(user_id=self.member_a_regular.id, organization_id=self.org_a.id, role="OPERATOR")

        self.site_a = Site(organization_id=self.org_a.id, name="Alpha Complex 1", code="ALPHA-SITE-1")
        self.plant_a = Plant(organization_id=self.org_a.id, site_id=self.site_a.id, name="Alpha Smelter", code="ALPHA-PLANT-1")

        # 2. Organization B and its assets
        self.org_b = Organization(name="Organization Beta", slug=f"org-beta-{uuid.uuid4().hex[:6]}")
        self.user_b = User(
            email=f"admin_b_{uuid.uuid4().hex[:6]}@beta.com",
            password_hash=hash_password("BetaSecret123!"),
            full_name="Beta Admin",
        )
        self.membership_b = Membership(user_id=self.user_b.id, organization_id=self.org_b.id, role="ADMIN")

        self.site_b = Site(organization_id=self.org_b.id, name="Beta Complex 1", code="BETA-SITE-1")
        self.plant_b = Plant(organization_id=self.org_b.id, site_id=self.site_b.id, name="Beta Assembly", code="BETA-PLANT-1")

        async def seed():
            # Seed Org A
            await organization_repo.add(self.org_a)
            await user_repo.add(self.user_a)
            await user_repo.add(self.member_a_regular)
            await membership_repo.add(self.membership_a1)
            await membership_repo.add(self.membership_a2)
            await site_repo.add(self.site_a)
            await plant_repo.add(self.plant_a)

            # Seed Org B
            await organization_repo.add(self.org_b)
            await user_repo.add(self.user_b)
            await membership_repo.add(self.membership_b)
            await site_repo.add(self.site_b)
            await plant_repo.add(self.plant_b)

            # Audit log records for Org A
            await audit_service.record_action(
                organization_id=self.org_a.id,
                actor_id=self.user_a.id,
                action="CONFIDENTIAL_ALPHA_MUTATION",
                resource_type="Plant",
                resource_id=str(self.plant_a.id),
                new_value={"confidential": "alpha_production_targets"},
            )

        asyncio.run(seed())

        # Tokens
        self.token_a = create_access_token(self.user_a.id, self.user_a.email)
        self.token_b = create_access_token(self.user_b.id, self.user_b.email)

    def test_attack_1_user_b_manipulates_org_id_header_to_org_a(self):
        """User B passes Organization A's UUID in the X-Organization-ID header."""
        response = self.client.get(
            "/api/v1/sites",
            headers={
                "Authorization": f"Bearer {self.token_b}",
                "X-Organization-ID": str(self.org_a.id),
            },
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["error"]["code"], "FORBIDDEN")
        self.assertIn("not an active member", response.json()["error"]["message"])

    def test_attack_2_user_b_cannot_read_org_a_plants_via_header_forgery(self):
        """User B attempts to read plants of Organization A via forged header."""
        response = self.client.get(
            "/api/v1/plants",
            headers={
                "Authorization": f"Bearer {self.token_b}",
                "X-Organization-ID": str(self.org_a.id),
            },
        )
        self.assertEqual(response.status_code, 403)

    def test_attack_3_user_b_cannot_read_org_a_users_via_header_forgery(self):
        """User B attempts to list users of Organization A."""
        response = self.client.get(
            "/api/v1/users",
            headers={
                "Authorization": f"Bearer {self.token_b}",
                "X-Organization-ID": str(self.org_a.id),
            },
        )
        self.assertEqual(response.status_code, 403)

    def test_attack_4_normal_user_b_queries_never_leak_org_a_sites(self):
        """Authenticated User B listing sites in Org B receives strictly Org B sites."""
        response = self.client.get(
            "/api/v1/sites",
            headers={
                "Authorization": f"Bearer {self.token_b}",
                "X-Organization-ID": str(self.org_b.id),
            },
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        site_codes = [s["code"] for s in data]
        self.assertIn("BETA-SITE-1", site_codes)
        self.assertNotIn("ALPHA-SITE-1", site_codes)

    def test_attack_5_normal_user_b_queries_never_leak_org_a_plants(self):
        """Authenticated User B listing plants in Org B receives strictly Org B plants."""
        response = self.client.get(
            "/api/v1/plants",
            headers={
                "Authorization": f"Bearer {self.token_b}",
                "X-Organization-ID": str(self.org_b.id),
            },
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        plant_codes = [p["code"] for p in data]
        self.assertIn("BETA-PLANT-1", plant_codes)
        self.assertNotIn("ALPHA-PLANT-1", plant_codes)

    def test_attack_6_normal_user_b_queries_never_leak_org_a_users(self):
        """Authenticated User B listing users in Org B receives strictly Org B users."""
        response = self.client.get(
            "/api/v1/users",
            headers={
                "Authorization": f"Bearer {self.token_b}",
                "X-Organization-ID": str(self.org_b.id),
            },
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        user_emails = [u["email"] for u in data]
        self.assertIn(self.user_b.email, user_emails)
        self.assertNotIn(self.user_a.email, user_emails)
        self.assertNotIn(self.member_a_regular.email, user_emails)

    def test_attack_7_user_b_cannot_update_org_a_user_profile(self):
        """User B attempts to modify profile of User A directly."""
        response = self.client.patch(
            f"/api/v1/users/{self.user_a.id}",
            json={"full_name": "Hacked Alpha Admin"},
            headers={
                "Authorization": f"Bearer {self.token_b}",
                "X-Organization-ID": str(self.org_b.id),
            },
        )
        # Must return 404 because user does not exist in Org B
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"]["code"], "RESOURCE_NOT_FOUND")

    def test_attack_8_user_b_cannot_deactivate_org_a_user(self):
        """User B attempts to deactivate a member of Organization A."""
        response = self.client.patch(
            f"/api/v1/users/{self.member_a_regular.id}/status",
            json={"is_active": False},
            headers={
                "Authorization": f"Bearer {self.token_b}",
                "X-Organization-ID": str(self.org_b.id),
            },
        )
        self.assertEqual(response.status_code, 404)
        # Verify member of A is still active
        async def verify():
            user = await user_repo.get_by_id(self.member_a_regular.id)
            return user.is_active
        self.assertTrue(asyncio.run(verify()))

    def test_attack_9_user_b_cannot_access_org_a_audit_logs(self):
        """Audit records for Organization A must never be accessible under Organization B context."""
        async def check_audit():
            logs_for_b = await audit_repo.list(self.org_b.id)
            return logs_for_b
        logs = asyncio.run(check_audit())
        # Org B should have 0 logs for Org A actions
        for log in logs:
            self.assertEqual(log.organization_id, self.org_b.id)
            self.assertNotEqual(log.action, "CONFIDENTIAL_ALPHA_MUTATION")

    def test_attack_10_invalid_uuid_org_header_rejected(self):
        """Client supplying invalid non-UUID header format is rejected."""
        response = self.client.get(
            "/api/v1/sites",
            headers={
                "Authorization": f"Bearer {self.token_b}",
                "X-Organization-ID": "invalid-uuid-12345",
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "VALIDATION_ERROR")


if __name__ == "__main__":
    unittest.main()
