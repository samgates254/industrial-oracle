"""External enterprise and industrial system adapters."""

import logging
from typing import Any, Dict, List

from industrial_oracle.integrations.application.interfaces import IERPAdapter

logger = logging.getLogger("industrial_oracle.integrations.adapters")


class MockERPAdapter(IERPAdapter):
    """Mock ERP integration adapter for external synchronization testing (SAP/Oracle/NetSuite)."""

    def __init__(self) -> None:
        self.synced_work_orders: List[Dict[str, Any]] = []
        self.synced_inventory_transactions: List[Dict[str, Any]] = []

    async def sync_work_order(self, work_order_id: str, payload: Dict[str, Any]) -> bool:
        """Simulates bidirectional work order sync with external ERP."""
        logger.info("Syncing work order %s to external ERP", work_order_id)
        self.synced_work_orders.append({
            "work_order_id": work_order_id,
            "payload": payload,
        })
        return True

    async def sync_inventory_transaction(self, transaction_id: str, payload: Dict[str, Any]) -> bool:
        """Simulates inventory ledger sync with external ERP."""
        logger.info("Syncing inventory transaction %s to external ERP", transaction_id)
        self.synced_inventory_transactions.append({
            "transaction_id": transaction_id,
            "payload": payload,
        })
        return True
