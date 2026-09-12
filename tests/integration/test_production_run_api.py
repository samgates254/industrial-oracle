"""Integration tests for Production Run execution, pause/resume, and scrap recording."""

import asyncio
import unittest
import uuid
from fastapi.testclient import TestClient

from apps.api.main import app
from industrial_oracle.assets.domain.models import ProductionLine
from industrial_oracle.assets.infrastructure.repository import production_line_repo
from industrial_oracle.core.security import create_access_token, hash_password
from industrial_oracle.identity.domain.models import User
from industrial_oracle.identity.infrastructure.repository import user_repo
from industrial_oracle.operations.domain.work_order import WorkOrder
from industrial_oracle.operations.infrastructure.repository import work_order_repo
from industrial_oracle.organization.domain.models import Membership, Organization, Plant, Site
from industrial_oracle.organization.infrastructure.repository import (
    membership_repo,
    organization_repo,
    plant_repo,
    site_repo,
)


class TestProductionRunAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.org = Organization(name="Run Test Org", slug=f"run-org-{uuid.uuid4().hex[:6]}")
        self.site = Site(organization_id=self.org.id, name="Run Site", code="RS-1")
        self.plant = Plant(organization_id=self.org.id, site_id=self.site.id, name="Run Plant", code="RP-1")
        self.line = ProductionLine(
            organization_id=self.org.id,
            plant_id=self.plant.id,
            name="Packaging Line 2",
            code=f"PL2-{uuid.uuid4().hex[:4].upper()}",
        )
        self.wo = WorkOrder(
            organization_id=self.org.id,
            site_id=self.site.id,
            plant_id=self.plant.id,
            production_line_id=self.line.id,
            work_order_number=f"WO-RUN-{uuid.uuid4().hex[:6].upper()}",
            title="Batch Production Run Host",
        )
        self.operator = User(
            email=f"run_op_{uuid.uuid4().hex[:6]}@example.com",
            password_hash=hash_password("Pass123!"),
            full_name="Run Operator",
        )
        self.operator_membership = Membership(user_id=self.operator.id, organization_id=self.org.id, role="OPERATOR")

        async def init():
            await organization_repo.add(self.org)
            await site_repo.add(self.site)
            await plant_repo.add(self.plant)
            await production_line_repo.add(self.line)
            await work_order_repo.add(self.wo)
            await user_repo.add(self.operator)
            await membership_repo.add(self.operator_membership)

        asyncio.run(init())
        self.token = create_access_token(self.operator.id, self.operator.email)

    def test_production_run_execution_and_quantity_recording(self):
        run_num = f"PR-{uuid.uuid4().hex[:6].upper()}"
        payload = {
            "site_id": str(self.site.id),
            "plant_id": str(self.plant.id),
            "production_line_id": str(self.line.id),
            "work_order_id": str(self.wo.id),
            "run_number": run_num,
            "product_code": "SKU-BEVERAGE-500ML",
            "planned_quantity": 1000.0,
            "unit_of_measure": "BOTTLES",
        }
        res = self.client.post(
            "/api/v1/production-runs",
            json=payload,
            headers={"Authorization": f"Bearer {self.token}", "X-Organization-ID": str(self.org.id)},
        )
        self.assertEqual(res.status_code, 201)
        run_data = res.json()
        run_id = run_data["id"]
        self.assertEqual(run_data["status"], "PLANNED")

        # Start run
        start_res = self.client.post(
            f"/api/v1/production-runs/{run_id}/start",
            headers={"Authorization": f"Bearer {self.token}", "X-Organization-ID": str(self.org.id)},
        )
        self.assertEqual(start_res.status_code, 200)
        self.assertEqual(start_res.json()["status"], "RUNNING")

        # Record quantity (batch 1: 450 good, 10 scrap)
        q1_res = self.client.post(
            f"/api/v1/production-runs/{run_id}/quantity",
            json={"good_quantity": 450.0, "rejected_quantity": 10.0},
            headers={"Authorization": f"Bearer {self.token}", "X-Organization-ID": str(self.org.id)},
        )
        self.assertEqual(q1_res.status_code, 200)
        self.assertEqual(q1_res.json()["actual_quantity"], 460.0)
        self.assertEqual(q1_res.json()["rejected_quantity"], 10.0)

        # Pause and resume
        pause_res = self.client.post(
            f"/api/v1/production-runs/{run_id}/pause",
            headers={"Authorization": f"Bearer {self.token}", "X-Organization-ID": str(self.org.id)},
        )
        self.assertEqual(pause_res.status_code, 200)
        self.assertEqual(pause_res.json()["status"], "PAUSED")

        resume_res = self.client.post(
            f"/api/v1/production-runs/{run_id}/resume",
            headers={"Authorization": f"Bearer {self.token}", "X-Organization-ID": str(self.org.id)},
        )
        self.assertEqual(resume_res.status_code, 200)
        self.assertEqual(resume_res.json()["status"], "RUNNING")

        # Complete run
        comp_res = self.client.post(
            f"/api/v1/production-runs/{run_id}/complete",
            headers={"Authorization": f"Bearer {self.token}", "X-Organization-ID": str(self.org.id)},
        )
        self.assertEqual(comp_res.status_code, 200)
        self.assertEqual(comp_res.json()["status"], "COMPLETED")

    def test_abort_production_run(self):
        run_num = f"PR-ABT-{uuid.uuid4().hex[:6].upper()}"
        res = self.client.post(
            "/api/v1/production-runs",
            json={
                "site_id": str(self.site.id),
                "plant_id": str(self.plant.id),
                "production_line_id": str(self.line.id),
                "work_order_id": str(self.wo.id),
                "run_number": run_num,
                "product_code": "SKU-BEVERAGE-1L",
                "planned_quantity": 500.0,
                "unit_of_measure": "BOTTLES",
            },
            headers={"Authorization": f"Bearer {self.token}", "X-Organization-ID": str(self.org.id)},
        )
        run_id = res.json()["id"]

        abort_res = self.client.post(
            f"/api/v1/production-runs/{run_id}/abort",
            json={"reason": "Major mechanical jam upstream"},
            headers={"Authorization": f"Bearer {self.token}", "X-Organization-ID": str(self.org.id)},
        )
        self.assertEqual(abort_res.status_code, 200)
        self.assertEqual(abort_res.json()["status"], "ABORTED")


if __name__ == "__main__":
    unittest.main()
