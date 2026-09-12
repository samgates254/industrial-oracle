"""Integration tests for Integration & Event API endpoints (Outbox, Events, Replay, Webhooks)."""

import asyncio
import unittest
import uuid
from fastapi.testclient import TestClient

from apps.api.main import app
from industrial_oracle.core.security import create_access_token, hash_password
from industrial_oracle.identity.domain.models import User
from industrial_oracle.identity.infrastructure.repository import user_repo
from industrial_oracle.integrations.domain.outbox import OutboxEvent, OutboxStatus
from industrial_oracle.integrations.infrastructure.repository import outbox_repository, webhook_repository
from industrial_oracle.organization.domain.models import Membership, Organization
from industrial_oracle.organization.infrastructure.repository import membership_repo, organization_repo


class TestIntegrationAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.org = Organization(name="Integration Test Org", slug=f"int-org-{uuid.uuid4().hex[:6]}")
        self.admin = User(
            email=f"admin_{uuid.uuid4().hex[:6]}@example.com",
            password_hash=hash_password("Secret123!"),
            full_name="Integration Admin",
        )
        self.membership = Membership(user_id=self.admin.id, organization_id=self.org.id, role="ADMIN")

        async def init():
            await organization_repo.add(self.org)
            await user_repo.add(self.admin)
            await membership_repo.add(self.membership)

        asyncio.run(init())
        self.token = create_access_token(self.admin.id, self.admin.email)
        self.headers = {"Authorization": f"Bearer {self.token}", "X-Organization-ID": str(self.org.id)}

    def test_list_events_tenant_scoped_and_filtered(self):
        async def seed():
            ev1 = OutboxEvent(
                organization_id=str(self.org.id),
                event_type="WorkOrderCreated.v1",
                aggregate_type="WorkOrder",
                aggregate_id="WO-555",
            )
            ev2 = OutboxEvent(
                organization_id=str(self.org.id),
                event_type="MaterialConsumed.v1",
                aggregate_type="ProductionRun",
                aggregate_id="RUN-777",
            )
            await outbox_repository.append(ev1)
            await outbox_repository.append(ev2)

        asyncio.run(seed())

        res = self.client.get("/api/v1/integration/events?aggregate_type=WorkOrder", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("items", data)
        self.assertGreaterEqual(data["total"], 1)
        items = data["items"]
        self.assertTrue(all(item["aggregate_type"] == "WorkOrder" for item in items))

    def test_get_single_event_details(self):
        ev = OutboxEvent(
            organization_id=str(self.org.id),
            event_type="InventoryReceived.v1",
            aggregate_type="InventoryBalance",
            aggregate_id="BAL-999",
            payload={"quantity": 40.0},
        )
        asyncio.run(outbox_repository.append(ev))

        res = self.client.get(f"/api/v1/integration/events/{ev.id}", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["event_type"], "InventoryReceived.v1")
        self.assertEqual(data["payload"]["quantity"], 40.0)

    def test_list_outbox_operational_view(self):
        res = self.client.get("/api/v1/integration/outbox", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("items", data)
        self.assertIn("total", data)

    def test_admin_can_retry_failed_outbox_event(self):
        ev = OutboxEvent(
            organization_id=str(self.org.id),
            event_type="FaultyEvent.v1",
            aggregate_type="Machine",
            aggregate_id="M-1",
            status=OutboxStatus.FAILED,
            attempts=3,
            last_error="Remote system unavailable",
        )
        asyncio.run(outbox_repository.append(ev))

        retry_res = self.client.post(f"/api/v1/integration/outbox/{ev.id}/retry", headers=self.headers)
        self.assertEqual(retry_res.status_code, 200)
        data = retry_res.json()
        self.assertEqual(data["status"], "PENDING")
        self.assertEqual(data["id"], ev.id)

        # Verify state in repository
        stored = asyncio.run(outbox_repository.get_by_id(ev.id))
        self.assertEqual(stored.status, OutboxStatus.PENDING)

    def test_retry_non_failed_outbox_event_rejected(self):
        ev = OutboxEvent(
            organization_id=str(self.org.id),
            event_type="SuccessEvent.v1",
            aggregate_type="Order",
            aggregate_id="1",
            status=OutboxStatus.PUBLISHED,
        )
        asyncio.run(outbox_repository.append(ev))

        res = self.client.post(f"/api/v1/integration/outbox/{ev.id}/retry", headers=self.headers)
        self.assertEqual(res.status_code, 422)

    def test_webhook_crud_lifecycle(self):
        # 1. Create Webhook
        payload = {
            "name": "ERP Synchronizer",
            "url": "https://erp.example.com/webhooks/listener",
            "subscribed_event_types": ["WorkOrder*.v1", "MaterialConsumed.v1"],
        }
        create_res = self.client.post("/api/v1/integration/webhooks", json=payload, headers=self.headers)
        self.assertEqual(create_res.status_code, 201)
        wh_data = create_res.json()
        wh_id = wh_data["id"]
        self.assertEqual(wh_data["name"], "ERP Synchronizer")
        self.assertTrue(wh_data["active"])

        # 2. Get Webhook
        get_res = self.client.get(f"/api/v1/integration/webhooks/{wh_id}", headers=self.headers)
        self.assertEqual(get_res.status_code, 200)

        # 3. Update Webhook
        update_res = self.client.patch(
            f"/api/v1/integration/webhooks/{wh_id}",
            json={"name": "ERP Synchronizer V2"},
            headers=self.headers,
        )
        self.assertEqual(update_res.status_code, 200)
        self.assertEqual(update_res.json()["name"], "ERP Synchronizer V2")

        # 4. Deactivate Webhook
        deact_res = self.client.post(f"/api/v1/integration/webhooks/{wh_id}/deactivate", headers=self.headers)
        self.assertEqual(deact_res.status_code, 200)
        self.assertFalse(deact_res.json()["active"])

        # 5. Activate Webhook
        act_res = self.client.post(f"/api/v1/integration/webhooks/{wh_id}/activate", headers=self.headers)
        self.assertEqual(act_res.status_code, 200)
        self.assertTrue(act_res.json()["active"])

        # 6. Delete Webhook
        del_res = self.client.delete(f"/api/v1/integration/webhooks/{wh_id}", headers=self.headers)
        self.assertEqual(del_res.status_code, 204)

        # 7. Get after delete -> 404
        get_after = self.client.get(f"/api/v1/integration/webhooks/{wh_id}", headers=self.headers)
        self.assertEqual(get_after.status_code, 404)

    def test_webhook_secret_never_exposed_in_api(self):
        payload = {
            "name": "Secure Webhook",
            "url": "https://secure.example.com/hook",
            "secret": "whsec_supersecrettoken1234567890abcdef",
        }
        res = self.client.post("/api/v1/integration/webhooks", json=payload, headers=self.headers)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        secret_field = data.get("secret", "")
        self.assertNotIn("supersecrettoken1234567890abcdef", secret_field)
        self.assertTrue("whsec_" in secret_field)
        self.assertTrue("****" in secret_field)


if __name__ == "__main__":
    unittest.main()
