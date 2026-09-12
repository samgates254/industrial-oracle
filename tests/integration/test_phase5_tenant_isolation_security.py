"""Phase 5 Security & Multi-Tenant Isolation Attack Suite.

Validates that Tenant B can NEVER access, mutate, replay, or inspect Tenant A's outbox events,
event history, consumption records, or webhook endpoints under any condition.
"""

import asyncio
import unittest
import uuid
from fastapi.testclient import TestClient

from apps.api.main import app
from industrial_oracle.core.security import create_access_token, hash_password
from industrial_oracle.identity.domain.models import User
from industrial_oracle.identity.infrastructure.repository import user_repo
from industrial_oracle.integrations.domain.outbox import OutboxEvent, OutboxStatus
from industrial_oracle.integrations.domain.webhook import WebhookEndpoint
from industrial_oracle.integrations.infrastructure.repository import outbox_repository, webhook_repository
from industrial_oracle.organization.domain.models import Membership, Organization
from industrial_oracle.organization.infrastructure.repository import membership_repo, organization_repo


class TestPhase5TenantIsolationSecurity(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

        # Organization A
        self.org_a = Organization(name="Tenant Alpha Corp", slug=f"alpha-{uuid.uuid4().hex[:6]}")
        self.user_a = User(
            email=f"alice_{uuid.uuid4().hex[:6]}@alpha.com",
            password_hash=hash_password("Pass123!"),
            full_name="Alice Admin",
        )
        self.membership_a = Membership(user_id=self.user_a.id, organization_id=self.org_a.id, role="ADMIN")

        # Organization B (Attacker / Unrelated Tenant)
        self.org_b = Organization(name="Tenant Beta Corp", slug=f"beta-{uuid.uuid4().hex[:6]}")
        self.user_b = User(
            email=f"bob_{uuid.uuid4().hex[:6]}@beta.com",
            password_hash=hash_password("Pass123!"),
            full_name="Bob Admin",
        )
        self.membership_b = Membership(user_id=self.user_b.id, organization_id=self.org_b.id, role="ADMIN")

        # Operator in Org B
        self.operator_b = User(
            email=f"op_{uuid.uuid4().hex[:6]}@beta.com",
            password_hash=hash_password("Pass123!"),
            full_name="Bob Operator",
        )
        self.membership_op_b = Membership(user_id=self.operator_b.id, organization_id=self.org_b.id, role="OPERATOR")

        # Viewer in Org B
        self.viewer_b = User(
            email=f"view_{uuid.uuid4().hex[:6]}@beta.com",
            password_hash=hash_password("Pass123!"),
            full_name="Bob Viewer",
        )
        self.membership_view_b = Membership(user_id=self.viewer_b.id, organization_id=self.org_b.id, role="VIEWER")

        async def init():
            await organization_repo.add(self.org_a)
            await user_repo.add(self.user_a)
            await membership_repo.add(self.membership_a)

            await organization_repo.add(self.org_b)
            await user_repo.add(self.user_b)
            await membership_repo.add(self.membership_b)

            await user_repo.add(self.operator_b)
            await membership_repo.add(self.membership_op_b)

            await user_repo.add(self.viewer_b)
            await membership_repo.add(self.membership_view_b)

        asyncio.run(init())

        self.token_a = create_access_token(self.user_a.id, self.user_a.email)
        self.token_b = create_access_token(self.user_b.id, self.user_b.email)
        self.token_op_b = create_access_token(self.operator_b.id, self.operator_b.email)
        self.token_view_b = create_access_token(self.viewer_b.id, self.viewer_b.email)

        self.headers_a = {"Authorization": f"Bearer {self.token_a}", "X-Organization-ID": str(self.org_a.id)}
        self.headers_b = {"Authorization": f"Bearer {self.token_b}", "X-Organization-ID": str(self.org_b.id)}
        self.headers_op_b = {"Authorization": f"Bearer {self.token_op_b}", "X-Organization-ID": str(self.org_b.id)}
        self.headers_view_b = {"Authorization": f"Bearer {self.token_view_b}", "X-Organization-ID": str(self.org_b.id)}

    def test_attack_1_tenant_b_cannot_read_tenant_a_outbox_event(self):
        ev = OutboxEvent(
            organization_id=str(self.org_a.id),
            event_type="ConfidentialOperation.v1",
            aggregate_type="WorkOrder",
            aggregate_id="WO-SECRET-1",
        )
        asyncio.run(outbox_repository.append(ev))

        # User B attempts to read Org A's outbox event
        res = self.client.get(f"/api/v1/integration/outbox/{ev.id}", headers=self.headers_b)
        self.assertEqual(res.status_code, 404)

    def test_attack_2_tenant_b_cannot_read_tenant_a_event_history(self):
        ev = OutboxEvent(
            organization_id=str(self.org_a.id),
            event_type="ProprietaryFormulaUpdated.v1",
            aggregate_type="ProductionRun",
            aggregate_id="RUN-SECRET-2",
        )
        asyncio.run(outbox_repository.append(ev))

        res = self.client.get(f"/api/v1/integration/events/{ev.id}", headers=self.headers_b)
        self.assertEqual(res.status_code, 404)

    def test_attack_3_tenant_b_cannot_retry_tenant_a_outbox_event(self):
        ev = OutboxEvent(
            organization_id=str(self.org_a.id),
            event_type="SensitiveTransferFailed.v1",
            aggregate_type="Inventory",
            aggregate_id="BAL-A",
            status=OutboxStatus.FAILED,
            attempts=3,
        )
        asyncio.run(outbox_repository.append(ev))

        res = self.client.post(f"/api/v1/integration/outbox/{ev.id}/retry", headers=self.headers_b)
        self.assertEqual(res.status_code, 404)

    def test_attack_4_tenant_b_listing_never_leaks_tenant_a_events(self):
        ev_a = OutboxEvent(
            organization_id=str(self.org_a.id),
            event_type="SecretAlphaEvent.v1",
            aggregate_type="Machine",
            aggregate_id="M-A",
        )
        ev_b = OutboxEvent(
            organization_id=str(self.org_b.id),
            event_type="PublicBetaEvent.v1",
            aggregate_type="Machine",
            aggregate_id="M-B",
        )
        asyncio.run(outbox_repository.append(ev_a))
        asyncio.run(outbox_repository.append(ev_b))

        res = self.client.get("/api/v1/integration/events", headers=self.headers_b)
        self.assertEqual(res.status_code, 200)
        items = res.json()["items"]
        org_ids = [i["organization_id"] for i in items]
        self.assertNotIn(str(self.org_a.id), org_ids)
        self.assertTrue(all(o == str(self.org_b.id) for o in org_ids))

    def test_attack_5_tenant_b_listing_never_leaks_tenant_a_outbox(self):
        res = self.client.get("/api/v1/integration/outbox", headers=self.headers_b)
        self.assertEqual(res.status_code, 200)
        items = res.json()["items"]
        self.assertTrue(all(i["organization_id"] == str(self.org_b.id) for i in items))

    def test_attack_6_tenant_b_cannot_read_tenant_a_webhook(self):
        wh_a = WebhookEndpoint(
            organization_id=str(self.org_a.id),
            name="Alpha Webhook",
            url="https://alpha.internal/webhook",
        )
        asyncio.run(webhook_repository.create(wh_a))

        res = self.client.get(f"/api/v1/integration/webhooks/{wh_a.id}", headers=self.headers_b)
        self.assertEqual(res.status_code, 404)

    def test_attack_7_tenant_b_cannot_update_tenant_a_webhook(self):
        wh_a = WebhookEndpoint(
            organization_id=str(self.org_a.id),
            name="Alpha Webhook",
            url="https://alpha.internal/webhook",
        )
        asyncio.run(webhook_repository.create(wh_a))

        res = self.client.patch(
            f"/api/v1/integration/webhooks/{wh_a.id}",
            json={"url": "https://malicious.attacker.com/sink"},
            headers=self.headers_b,
        )
        self.assertEqual(res.status_code, 404)

    def test_attack_8_tenant_b_cannot_activate_tenant_a_webhook(self):
        wh_a = WebhookEndpoint(
            organization_id=str(self.org_a.id),
            name="Alpha Inactive Hook",
            url="https://alpha.internal/hook",
            active=False,
        )
        asyncio.run(webhook_repository.create(wh_a))

        res = self.client.post(f"/api/v1/integration/webhooks/{wh_a.id}/activate", headers=self.headers_b)
        self.assertEqual(res.status_code, 404)

    def test_attack_9_tenant_b_cannot_deactivate_tenant_a_webhook(self):
        wh_a = WebhookEndpoint(
            organization_id=str(self.org_a.id),
            name="Alpha Active Hook",
            url="https://alpha.internal/hook",
            active=True,
        )
        asyncio.run(webhook_repository.create(wh_a))

        res = self.client.post(f"/api/v1/integration/webhooks/{wh_a.id}/deactivate", headers=self.headers_b)
        self.assertEqual(res.status_code, 404)

    def test_attack_10_tenant_b_cannot_delete_tenant_a_webhook(self):
        wh_a = WebhookEndpoint(
            organization_id=str(self.org_a.id),
            name="Alpha Hook to Delete",
            url="https://alpha.internal/hook",
        )
        asyncio.run(webhook_repository.create(wh_a))

        res = self.client.delete(f"/api/v1/integration/webhooks/{wh_a.id}", headers=self.headers_b)
        self.assertEqual(res.status_code, 404)

    def test_attack_11_tenant_b_listing_never_leaks_tenant_a_webhooks(self):
        wh_a = WebhookEndpoint(organization_id=str(self.org_a.id), name="Hook A", url="https://a.org")
        wh_b = WebhookEndpoint(organization_id=str(self.org_b.id), name="Hook B", url="https://b.org")
        asyncio.run(webhook_repository.create(wh_a))
        asyncio.run(webhook_repository.create(wh_b))

        res = self.client.get("/api/v1/integration/webhooks", headers=self.headers_b)
        self.assertEqual(res.status_code, 200)
        items = res.json()
        org_ids = [w["organization_id"] for w in items]
        self.assertNotIn(str(self.org_a.id), org_ids)
        self.assertTrue(all(o == str(self.org_b.id) for o in org_ids))

    def test_attack_12_forged_header_to_tenant_a_rejected(self):
        # User B attempts to access Org A resources using forged header
        forged_headers = {"Authorization": f"Bearer {self.token_b}", "X-Organization-ID": str(self.org_a.id)}
        res = self.client.get("/api/v1/integration/events", headers=forged_headers)
        self.assertEqual(res.status_code, 403)

    def test_attack_13_operator_cannot_manage_or_retry_integrations(self):
        # Operator has no integration permissions
        ev = OutboxEvent(
            organization_id=str(self.org_b.id),
            event_type="TestEvent.v1",
            aggregate_type="Order",
            aggregate_id="1",
            status=OutboxStatus.FAILED,
        )
        asyncio.run(outbox_repository.append(ev))

        retry_res = self.client.post(f"/api/v1/integration/outbox/{ev.id}/retry", headers=self.headers_op_b)
        self.assertEqual(retry_res.status_code, 403)

        list_res = self.client.get("/api/v1/integration/events", headers=self.headers_op_b)
        self.assertEqual(list_res.status_code, 403)

    def test_attack_14_viewer_and_analyst_cannot_mutate_webhooks_or_retry(self):
        # Viewer has read-only integration permission, cannot mutate webhooks or retry outbox
        wh_payload = {"name": "Viewer Hook", "url": "https://viewer.org/hook"}
        create_res = self.client.post("/api/v1/integration/webhooks", json=wh_payload, headers=self.headers_view_b)
        self.assertEqual(create_res.status_code, 403)

        ev = OutboxEvent(
            organization_id=str(self.org_b.id),
            event_type="TestEvent.v1",
            aggregate_type="Order",
            aggregate_id="1",
            status=OutboxStatus.FAILED,
        )
        asyncio.run(outbox_repository.append(ev))
        retry_res = self.client.post(f"/api/v1/integration/outbox/{ev.id}/retry", headers=self.headers_view_b)
        self.assertEqual(retry_res.status_code, 403)


if __name__ == "__main__":
    unittest.main()
