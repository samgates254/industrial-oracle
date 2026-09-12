"""Integration tests for Asset API endpoints and RBAC."""

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


class TestAssetAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.org = Organization(name="Asset Test Org", slug=f"asset-org-{uuid.uuid4().hex[:6]}")
        self.site = Site(organization_id=self.org.id, name="Test Site", code="TS-1")
        self.plant = Plant(organization_id=self.org.id, site_id=self.site.id, name="Test Plant", code="TP-1")

        # Admin user
        self.admin = User(
            email=f"admin_{uuid.uuid4().hex[:6]}@example.com",
            password_hash=hash_password("Pass123!"),
            full_name="Asset Admin",
        )
        self.admin_membership = Membership(user_id=self.admin.id, organization_id=self.org.id, role="ADMIN")

        # Viewer user (cannot create or delete assets)
        self.viewer = User(
            email=f"viewer_{uuid.uuid4().hex[:6]}@example.com",
            password_hash=hash_password("Pass123!"),
            full_name="Asset Viewer",
        )
        self.viewer_membership = Membership(user_id=self.viewer.id, organization_id=self.org.id, role="VIEWER")

        async def init():
            await organization_repo.add(self.org)
            await site_repo.add(self.site)
            await plant_repo.add(self.plant)
            await user_repo.add(self.admin)
            await user_repo.add(self.viewer)
            await membership_repo.add(self.admin_membership)
            await membership_repo.add(self.viewer_membership)

        asyncio.run(init())
        self.admin_token = create_access_token(self.admin.id, self.admin.email)
        self.viewer_token = create_access_token(self.viewer.id, self.viewer.email)

    def test_create_and_read_asset(self):
        tag = f"AST-{uuid.uuid4().hex[:6].upper()}"
        payload = {
            "name": "Stamping Press 1000T",
            "asset_tag": tag,
            "asset_type": "HYDRAULIC",
            "plant_id": str(self.plant.id),
            "critical": True,
            "location_in_plant": "Bay 3",
        }
        res = self.client.post(
            "/api/v1/assets",
            json=payload,
            headers={"Authorization": f"Bearer {self.admin_token}", "X-Organization-ID": str(self.org.id)},
        )
        self.assertEqual(res.status_code, 201)
        data = res.json()
        asset_id = data["id"]
        self.assertEqual(data["asset_tag"], tag)
        self.assertEqual(data["status"], "IN_SERVICE")

        # Read back asset
        get_res = self.client.get(
            f"/api/v1/assets/{asset_id}",
            headers={"Authorization": f"Bearer {self.admin_token}", "X-Organization-ID": str(self.org.id)},
        )
        self.assertEqual(get_res.status_code, 200)
        self.assertEqual(get_res.json()["name"], "Stamping Press 1000T")

    def test_unique_asset_tag_enforced_in_organization(self):
        tag = f"AST-DUP-{uuid.uuid4().hex[:6].upper()}"
        payload = {
            "name": "Original Asset",
            "asset_tag": tag,
            "asset_type": "MECHANICAL",
        }
        res1 = self.client.post(
            "/api/v1/assets",
            json=payload,
            headers={"Authorization": f"Bearer {self.admin_token}", "X-Organization-ID": str(self.org.id)},
        )
        self.assertEqual(res1.status_code, 201)

        # Duplicate tag attempt
        res2 = self.client.post(
            "/api/v1/assets",
            json=payload,
            headers={"Authorization": f"Bearer {self.admin_token}", "X-Organization-ID": str(self.org.id)},
        )
        self.assertEqual(res2.status_code, 409)
        self.assertEqual(res2.json()["error"]["code"], "ALREADY_EXISTS")

    def test_asset_status_transition(self):
        tag = f"AST-ST-{uuid.uuid4().hex[:6].upper()}"
        res = self.client.post(
            "/api/v1/assets",
            json={"name": "Status Asset", "asset_tag": tag, "asset_type": "HVAC"},
            headers={"Authorization": f"Bearer {self.admin_token}", "X-Organization-ID": str(self.org.id)},
        )
        asset_id = res.json()["id"]

        # Transition to MAINTENANCE
        patch_res = self.client.patch(
            f"/api/v1/assets/{asset_id}/status",
            json={"status": "MAINTENANCE"},
            headers={"Authorization": f"Bearer {self.admin_token}", "X-Organization-ID": str(self.org.id)},
        )
        self.assertEqual(patch_res.status_code, 200)
        self.assertEqual(patch_res.json()["status"], "MAINTENANCE")

    def test_delete_asset(self):
        tag = f"AST-DEL-{uuid.uuid4().hex[:6].upper()}"
        res = self.client.post(
            "/api/v1/assets",
            json={"name": "Asset to Delete", "asset_tag": tag, "asset_type": "ELECTRICAL"},
            headers={"Authorization": f"Bearer {self.admin_token}", "X-Organization-ID": str(self.org.id)},
        )
        asset_id = res.json()["id"]

        del_res = self.client.delete(
            f"/api/v1/assets/{asset_id}",
            headers={"Authorization": f"Bearer {self.admin_token}", "X-Organization-ID": str(self.org.id)},
        )
        self.assertEqual(del_res.status_code, 204)

        # Confirm deleted
        get_res = self.client.get(
            f"/api/v1/assets/{asset_id}",
            headers={"Authorization": f"Bearer {self.admin_token}", "X-Organization-ID": str(self.org.id)},
        )
        self.assertEqual(get_res.status_code, 404)

    def test_viewer_rbac_restrictions(self):
        # Viewer can read
        list_res = self.client.get(
            "/api/v1/assets",
            headers={"Authorization": f"Bearer {self.viewer_token}", "X-Organization-ID": str(self.org.id)},
        )
        self.assertEqual(list_res.status_code, 200)

        # Viewer cannot create (requires assets.create)
        create_res = self.client.post(
            "/api/v1/assets",
            json={"name": "Unauthorized Asset", "asset_tag": "AST-NO", "asset_type": "HVAC"},
            headers={"Authorization": f"Bearer {self.viewer_token}", "X-Organization-ID": str(self.org.id)},
        )
        self.assertEqual(create_res.status_code, 403)


if __name__ == "__main__":
    unittest.main()
