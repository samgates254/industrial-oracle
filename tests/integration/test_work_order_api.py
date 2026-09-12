"""Integration tests for Work Order endpoints and RBAC."""

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


class TestWorkOrderAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.org = Organization(name="WO Test Org", slug=f"wo-org-{uuid.uuid4().hex[:6]}")
        self.site = Site(organization_id=self.org.id, name="WO Site", code="WOS-1")
        self.plant = Plant(organization_id=self.org.id, site_id=self.site.id, name="WO Plant", code="WOP-1")

        self.engineer = User(
            email=f"wo_eng_{uuid.uuid4().hex[:6]}@example.com",
            password_hash=hash_password("Pass123!"),
            full_name="WO Engineer",
        )
        self.engineer_membership = Membership(user_id=self.engineer.id, organization_id=self.org.id, role="ENGINEER")

        self.viewer = User(
            email=f"wo_view_{uuid.uuid4().hex[:6]}@example.com",
            password_hash=hash_password("Pass123!"),
            full_name="WO Viewer",
        )
        self.viewer_membership = Membership(user_id=self.viewer.id, organization_id=self.org.id, role="VIEWER")

        async def init():
            await organization_repo.add(self.org)
            await site_repo.add(self.site)
            await plant_repo.add(self.plant)
            await user_repo.add(self.engineer)
            await user_repo.add(self.viewer)
            await membership_repo.add(self.engineer_membership)
            await membership_repo.add(self.viewer_membership)

        asyncio.run(init())
        self.token = create_access_token(self.engineer.id, self.engineer.email)
        self.viewer_token = create_access_token(self.viewer.id, self.viewer.email)

    def test_create_and_read_work_order(self):
        wo_num = f"WO-{uuid.uuid4().hex[:6].upper()}"
        payload = {
            "site_id": str(self.site.id),
            "plant_id": str(self.plant.id),
            "work_order_number": wo_num,
            "title": "Assemble 500 Sub-assemblies",
            "work_order_type": "PRODUCTION",
            "priority": "HIGH",
        }
        res = self.client.post(
            "/api/v1/work-orders",
            json=payload,
            headers={"Authorization": f"Bearer {self.token}", "X-Organization-ID": str(self.org.id)},
        )
        self.assertEqual(res.status_code, 201)
        data = res.json()
        wo_id = data["id"]
        self.assertEqual(data["status"], "DRAFT")
        self.assertEqual(data["work_order_number"], wo_num)

        # Read back
        get_res = self.client.get(
            f"/api/v1/work-orders/{wo_id}",
            headers={"Authorization": f"Bearer {self.token}", "X-Organization-ID": str(self.org.id)},
        )
        self.assertEqual(get_res.status_code, 200)
        self.assertEqual(get_res.json()["title"], "Assemble 500 Sub-assemblies")

    def test_work_order_full_lifecycle(self):
        wo_num = f"WO-LC-{uuid.uuid4().hex[:6].upper()}"
        res = self.client.post(
            "/api/v1/work-orders",
            json={
                "site_id": str(self.site.id),
                "plant_id": str(self.plant.id),
                "work_order_number": wo_num,
                "title": "Lifecycle Work Order",
            },
            headers={"Authorization": f"Bearer {self.token}", "X-Organization-ID": str(self.org.id)},
        )
        wo_id = res.json()["id"]

        # 1. Release
        rel_res = self.client.post(
            f"/api/v1/work-orders/{wo_id}/release",
            headers={"Authorization": f"Bearer {self.token}", "X-Organization-ID": str(self.org.id)},
        )
        self.assertEqual(rel_res.status_code, 200)
        self.assertEqual(rel_res.json()["status"], "RELEASED")

        # 2. Start
        start_res = self.client.post(
            f"/api/v1/work-orders/{wo_id}/start",
            headers={"Authorization": f"Bearer {self.token}", "X-Organization-ID": str(self.org.id)},
        )
        self.assertEqual(start_res.status_code, 200)
        self.assertEqual(start_res.json()["status"], "IN_PROGRESS")

        # 3. Hold
        hold_res = self.client.post(
            f"/api/v1/work-orders/{wo_id}/hold",
            json={"reason": "Missing fastener kit"},
            headers={"Authorization": f"Bearer {self.token}", "X-Organization-ID": str(self.org.id)},
        )
        self.assertEqual(hold_res.status_code, 200)
        self.assertEqual(hold_res.json()["status"], "ON_HOLD")

        # 4. Resume
        res_res = self.client.post(
            f"/api/v1/work-orders/{wo_id}/resume",
            headers={"Authorization": f"Bearer {self.token}", "X-Organization-ID": str(self.org.id)},
        )
        self.assertEqual(res_res.status_code, 200)
        self.assertEqual(res_res.json()["status"], "IN_PROGRESS")

        # 5. Complete
        comp_res = self.client.post(
            f"/api/v1/work-orders/{wo_id}/complete",
            headers={"Authorization": f"Bearer {self.token}", "X-Organization-ID": str(self.org.id)},
        )
        self.assertEqual(comp_res.status_code, 200)
        self.assertEqual(comp_res.json()["status"], "COMPLETED")

    def test_cancel_work_order(self):
        wo_num = f"WO-CAN-{uuid.uuid4().hex[:6].upper()}"
        res = self.client.post(
            "/api/v1/work-orders",
            json={
                "site_id": str(self.site.id),
                "plant_id": str(self.plant.id),
                "work_order_number": wo_num,
                "title": "To Cancel Work Order",
            },
            headers={"Authorization": f"Bearer {self.token}", "X-Organization-ID": str(self.org.id)},
        )
        wo_id = res.json()["id"]

        can_res = self.client.post(
            f"/api/v1/work-orders/{wo_id}/cancel",
            json={"reason": "Customer cancelled order"},
            headers={"Authorization": f"Bearer {self.token}", "X-Organization-ID": str(self.org.id)},
        )
        self.assertEqual(can_res.status_code, 200)
        self.assertEqual(can_res.json()["status"], "CANCELLED")

    def test_duplicate_work_order_number_rejected(self):
        wo_num = f"WO-DUP-{uuid.uuid4().hex[:6].upper()}"
        payload = {
            "site_id": str(self.site.id),
            "plant_id": str(self.plant.id),
            "work_order_number": wo_num,
            "title": "First Work Order",
        }
        res1 = self.client.post(
            "/api/v1/work-orders",
            json=payload,
            headers={"Authorization": f"Bearer {self.token}", "X-Organization-ID": str(self.org.id)},
        )
        self.assertEqual(res1.status_code, 201)

        res2 = self.client.post(
            "/api/v1/work-orders",
            json=payload,
            headers={"Authorization": f"Bearer {self.token}", "X-Organization-ID": str(self.org.id)},
        )
        self.assertEqual(res2.status_code, 409)

    def test_viewer_cannot_create_or_mutate_work_order(self):
        wo_num = f"WO-NO-{uuid.uuid4().hex[:6].upper()}"
        res = self.client.post(
            "/api/v1/work-orders",
            json={
                "site_id": str(self.site.id),
                "plant_id": str(self.plant.id),
                "work_order_number": wo_num,
                "title": "Unauthorized Work Order",
            },
            headers={"Authorization": f"Bearer {self.viewer_token}", "X-Organization-ID": str(self.org.id)},
        )
        self.assertEqual(res.status_code, 403)


if __name__ == "__main__":
    unittest.main()
