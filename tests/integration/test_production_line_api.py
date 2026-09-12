"""Integration tests for Production Line API endpoints."""

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


class TestProductionLineAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.org = Organization(name="Line Test Org", slug=f"line-org-{uuid.uuid4().hex[:6]}")
        self.site = Site(organization_id=self.org.id, name="Test Site", code="LS-1")
        self.plant = Plant(organization_id=self.org.id, site_id=self.site.id, name="Test Plant", code="LP-1")

        self.engineer = User(
            email=f"eng_{uuid.uuid4().hex[:6]}@example.com",
            password_hash=hash_password("Pass123!"),
            full_name="Line Engineer",
        )
        self.membership = Membership(user_id=self.engineer.id, organization_id=self.org.id, role="ENGINEER")

        async def init():
            await organization_repo.add(self.org)
            await site_repo.add(self.site)
            await plant_repo.add(self.plant)
            await user_repo.add(self.engineer)
            await membership_repo.add(self.membership)

        asyncio.run(init())
        self.token = create_access_token(self.engineer.id, self.engineer.email)

    def test_create_and_list_production_lines(self):
        payload = {
            "plant_id": str(self.plant.id),
            "name": "Packaging Line 1",
            "code": "PKG-01",
            "capacity_units_per_hour": 1500.0,
        }
        create_res = self.client.post(
            "/api/v1/production-lines",
            json=payload,
            headers={"Authorization": f"Bearer {self.token}", "X-Organization-ID": str(self.org.id)},
        )
        self.assertEqual(create_res.status_code, 201)
        data = create_res.json()
        line_id = data["id"]
        self.assertEqual(data["code"], "PKG-01")
        self.assertEqual(data["capacity_units_per_hour"], 1500.0)

        # Read back
        get_res = self.client.get(
            f"/api/v1/production-lines/{line_id}",
            headers={"Authorization": f"Bearer {self.token}", "X-Organization-ID": str(self.org.id)},
        )
        self.assertEqual(get_res.status_code, 200)
        self.assertEqual(get_res.json()["name"], "Packaging Line 1")

        # List
        list_res = self.client.get(
            "/api/v1/production-lines",
            headers={"Authorization": f"Bearer {self.token}", "X-Organization-ID": str(self.org.id)},
        )
        self.assertEqual(list_res.status_code, 200)
        self.assertGreaterEqual(len(list_res.json()), 1)


if __name__ == "__main__":
    unittest.main()
