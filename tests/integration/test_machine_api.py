"""Integration tests for Machine operational endpoints and state machine."""

import asyncio
import unittest
import uuid
from fastapi.testclient import TestClient

from apps.api.main import app
from industrial_oracle.assets.domain.models import Asset
from industrial_oracle.assets.infrastructure.repository import asset_repo
from industrial_oracle.core.security import create_access_token, hash_password
from industrial_oracle.identity.domain.models import User
from industrial_oracle.identity.infrastructure.repository import user_repo
from industrial_oracle.organization.domain.models import Membership, Organization
from industrial_oracle.organization.infrastructure.repository import (
    membership_repo,
    organization_repo,
)


class TestMachineAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.org = Organization(name="Machine Test Org", slug=f"machine-org-{uuid.uuid4().hex[:6]}")
        self.asset = Asset(
            organization_id=self.org.id,
            name="Host Asset",
            asset_tag=f"HOST-{uuid.uuid4().hex[:6].upper()}",
            asset_type="MECHANICAL",
        )
        self.operator = User(
            email=f"operator_{uuid.uuid4().hex[:6]}@example.com",
            password_hash=hash_password("Pass123!"),
            full_name="Machine Operator",
        )
        self.operator_membership = Membership(user_id=self.operator.id, organization_id=self.org.id, role="OPERATOR")

        self.engineer = User(
            email=f"engineer_{uuid.uuid4().hex[:6]}@example.com",
            password_hash=hash_password("Pass123!"),
            full_name="Machine Engineer",
        )
        self.engineer_membership = Membership(user_id=self.engineer.id, organization_id=self.org.id, role="ENGINEER")

        async def init():
            await organization_repo.add(self.org)
            await asset_repo.add(self.asset)
            await user_repo.add(self.operator)
            await user_repo.add(self.engineer)
            await membership_repo.add(self.operator_membership)
            await membership_repo.add(self.engineer_membership)

        asyncio.run(init())
        self.operator_token = create_access_token(self.operator.id, self.operator.email)
        self.engineer_token = create_access_token(self.engineer.id, self.engineer.email)

    def test_machine_lifecycle_and_state_machine_flow(self):
        # 1. Create machine (by Engineer who has assets.create)
        payload = {
            "asset_id": str(self.asset.id),
            "name": "Extruder Unit 5",
            "model": "EX-500-Z",
            "power_rating_kw": 110.0,
            "operating_hours": 250.0,
        }
        res = self.client.post(
            "/api/v1/machines",
            json=payload,
            headers={"Authorization": f"Bearer {self.engineer_token}", "X-Organization-ID": str(self.org.id)},
        )
        self.assertEqual(res.status_code, 201)
        machine = res.json()
        machine_id = machine["id"]
        self.assertEqual(machine["status"], "STOPPED")

        # 2. Operator starts machine -> transitions to RUNNING
        start_res = self.client.post(
            f"/api/v1/machines/{machine_id}/start",
            headers={"Authorization": f"Bearer {self.operator_token}", "X-Organization-ID": str(self.org.id)},
        )
        self.assertEqual(start_res.status_code, 200)
        self.assertEqual(start_res.json()["status"], "RUNNING")

        # 3. Fault detected -> transitions to FAULTED
        fault_res = self.client.post(
            f"/api/v1/machines/{machine_id}/fault",
            json={"fault_code": "FLT-THERMAL-01", "description": "Motor temperature exceeded maximum threshold"},
            headers={"Authorization": f"Bearer {self.operator_token}", "X-Organization-ID": str(self.org.id)},
        )
        self.assertEqual(fault_res.status_code, 200)
        self.assertEqual(fault_res.json()["status"], "FAULTED")
        self.assertEqual(fault_res.json()["fault_code"], "FLT-THERMAL-01")

        # 4. Attempting start while FAULTED -> 422 Business Rule Violation
        blocked_res = self.client.post(
            f"/api/v1/machines/{machine_id}/start",
            headers={"Authorization": f"Bearer {self.operator_token}", "X-Organization-ID": str(self.org.id)},
        )
        self.assertEqual(blocked_res.status_code, 422)
        self.assertEqual(blocked_res.json()["error"]["code"], "BUSINESS_RULE_VIOLATION")

        # 5. Clear fault -> transitions to STOPPED
        clear_res = self.client.post(
            f"/api/v1/machines/{machine_id}/clear-fault",
            headers={"Authorization": f"Bearer {self.operator_token}", "X-Organization-ID": str(self.org.id)},
        )
        self.assertEqual(clear_res.status_code, 200)
        self.assertEqual(clear_res.json()["status"], "STOPPED")
        self.assertIsNone(clear_res.json()["fault_code"])

        # 6. Restart machine -> RUNNING
        restart_res = self.client.post(
            f"/api/v1/machines/{machine_id}/start",
            headers={"Authorization": f"Bearer {self.operator_token}", "X-Organization-ID": str(self.org.id)},
        )
        self.assertEqual(restart_res.status_code, 200)
        self.assertEqual(restart_res.json()["status"], "RUNNING")

        # 7. Stop machine -> STOPPED
        stop_res = self.client.post(
            f"/api/v1/machines/{machine_id}/stop",
            headers={"Authorization": f"Bearer {self.operator_token}", "X-Organization-ID": str(self.org.id)},
        )
        self.assertEqual(stop_res.status_code, 200)
        self.assertEqual(stop_res.json()["status"], "STOPPED")


if __name__ == "__main__":
    unittest.main()
