"""Integration tests for organization, site, and plant endpoints."""

import asyncio
import unittest
import uuid
from fastapi.testclient import TestClient

from apps.api.main import app
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


class TestOrganizationAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.user = User(
            email=f"org_user_{uuid.uuid4().hex[:6]}@example.com",
            password_hash=hash_password("Pass123!"),
            full_name="Org User",
        )
        self.org1 = Organization(name="Primary Facility Corp", slug=f"facility-1-{uuid.uuid4().hex[:6]}")
        self.org2 = Organization(name="Secondary Facility Corp", slug=f"facility-2-{uuid.uuid4().hex[:6]}")

        self.membership1 = Membership(user_id=self.user.id, organization_id=self.org1.id, role="ENGINEER")
        self.membership2 = Membership(user_id=self.user.id, organization_id=self.org2.id, role="VIEWER")

        self.site1 = Site(organization_id=self.org1.id, name="Site North", code="SN-1")
        self.plant1 = Plant(organization_id=self.org1.id, site_id=self.site1.id, name="Mill Plant 1", code="MP-1")

        async def init():
            await user_repo.add(self.user)
            await organization_repo.add(self.org1)
            await organization_repo.add(self.org2)
            await membership_repo.add(self.membership1)
            await membership_repo.add(self.membership2)
            await site_repo.add(self.site1)
            await plant_repo.add(self.plant1)

        asyncio.run(init())
        self.token = create_access_token(self.user.id, self.user.email)

    def test_list_my_organizations(self):
        response = self.client.get(
            "/api/v1/organizations",
            headers={"Authorization": f"Bearer {self.token}"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 2)
        org_names = {o["name"] for o in data}
        self.assertIn("Primary Facility Corp", org_names)
        self.assertIn("Secondary Facility Corp", org_names)

    def test_get_sites_tenant_scoped(self):
        response = self.client.get(
            "/api/v1/sites",
            headers={
                "Authorization": f"Bearer {self.token}",
                "X-Organization-ID": str(self.org1.id),
            },
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["code"], "SN-1")

    def test_get_plants_tenant_scoped(self):
        response = self.client.get(
            "/api/v1/plants",
            headers={
                "Authorization": f"Bearer {self.token}",
                "X-Organization-ID": str(self.org1.id),
            },
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["code"], "MP-1")

    def test_multi_organization_requires_header_disambiguation(self):
        # User belongs to 2 organizations, so omitting X-Organization-ID must raise validation error
        response = self.client.get(
            "/api/v1/sites",
            headers={"Authorization": f"Bearer {self.token}"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("X-Organization-ID", response.json()["error"]["message"])


if __name__ == "__main__":
    unittest.main()
