"""Inventory application service orchestrating stock movements, concurrency control, and audit."""

from datetime import datetime, timezone
from typing import Any, List, Optional, Tuple
import uuid

from industrial_oracle.audit.application.service import audit_service
from industrial_oracle.core.exceptions import (
    BusinessRuleViolationException,
    EntityAlreadyExistsException,
    EntityNotFoundException,
)
from industrial_oracle.inventory.application.dtos import (
    InventoryAdjustmentDTO,
    InventoryBalanceResponseDTO,
    InventoryIssueDTO,
    InventoryLocationCreateDTO,
    InventoryLocationResponseDTO,
    InventoryReceiptDTO,
    InventoryTransactionResponseDTO,
    InventoryTransferDTO,
    ItemCreateDTO,
    ItemResponseDTO,
    ItemUpdateDTO,
)
from industrial_oracle.inventory.application.interfaces import (
    IInventoryBalanceRepository,
    IInventoryLocationRepository,
    IInventoryTransactionRepository,
    IItemRepository,
)
from industrial_oracle.inventory.domain.models import (
    InventoryBalance,
    InventoryLocation,
    InventoryTransaction,
    Item,
    TransactionType,
)
from industrial_oracle.inventory.infrastructure.repository import (
    inventory_balance_repo,
    inventory_location_repo,
    inventory_transaction_repo,
    item_repo,
)
from industrial_oracle.organization.infrastructure.repository import site_repo
from industrial_oracle.shared.domain.events import DomainEvent
from industrial_oracle.shared.infrastructure.event_bus import event_bus
from industrial_oracle.integrations.infrastructure.repository import outbox_repository


class InventoryService:
    def __init__(
        self,
        item_repository: IItemRepository = item_repo,
        location_repository: IInventoryLocationRepository = inventory_location_repo,
        balance_repository: IInventoryBalanceRepository = inventory_balance_repo,
        transaction_repository: IInventoryTransactionRepository = inventory_transaction_repo,
        outbox_repo = None,
    ) -> None:
        self._item_repo = item_repository
        self._loc_repo = location_repository
        self._bal_repo = balance_repository
        self._tx_repo = transaction_repository
        self._outbox_repo = outbox_repo or outbox_repository

    async def _emit(self, ev: DomainEvent, session: Optional[Any] = None) -> None:
        # Synchronous request path offloads event dispatch to durable outbox worker
        await self._outbox_repo.append_domain_event(ev, session=session)

    # --------------------------------------------------------------------------
    # Items
    # --------------------------------------------------------------------------

    async def create_item(self, organization_id: uuid.UUID, dto: ItemCreateDTO, actor_id: uuid.UUID) -> ItemResponseDTO:
        existing = await self._item_repo.get_by_sku(organization_id, dto.sku)
        if existing:
            raise EntityAlreadyExistsException(f"Item with SKU '{dto.sku}' already exists in organization.")

        item = Item(
            organization_id=organization_id,
            sku=dto.sku,
            name=dto.name,
            unit_of_measure=dto.unit_of_measure,
            category=dto.category,
            description=dto.description,
            active=True,
        )
        saved = await self._item_repo.add(item)
        await audit_service.log_action(
            actor_id=actor_id,
            organization_id=organization_id,
            action="ITEM_CREATED",
            resource_type="Item",
            resource_id=saved.id,
            metadata={"sku": saved.sku, "name": saved.name, "category": saved.category},
        )
        return self._to_item_dto(saved)

    async def get_item(self, organization_id: uuid.UUID, item_id: uuid.UUID) -> ItemResponseDTO:
        item = await self._item_repo.get_by_id(item_id)
        if not item or item.organization_id != organization_id:
            raise EntityNotFoundException("Item not found in this organization.")
        return self._to_item_dto(item)

    async def list_items(
        self, organization_id: uuid.UUID, category: Optional[str] = None, limit: int = 100, offset: int = 0
    ) -> List[ItemResponseDTO]:
        items = await self._item_repo.list_by_organization(
            organization_id, category=category, active_only=False, limit=limit, offset=offset
        )
        return [self._to_item_dto(i) for i in items]

    async def update_item(
        self, organization_id: uuid.UUID, item_id: uuid.UUID, dto: ItemUpdateDTO, actor_id: uuid.UUID
    ) -> ItemResponseDTO:
        item = await self._item_repo.get_by_id(item_id)
        if not item or item.organization_id != organization_id:
            raise EntityNotFoundException("Item not found in this organization.")

        if dto.name is not None:
            item.name = dto.name.strip()
        if dto.category is not None:
            item.category = dto.category
        if dto.description is not None:
            item.description = dto.description
        if dto.active is not None:
            item.active = dto.active
        item.updated_at = datetime.now(timezone.utc)

        updated = await self._item_repo.update(item)
        await audit_service.log_action(
            actor_id=actor_id,
            organization_id=organization_id,
            action="ITEM_UPDATED",
            resource_type="Item",
            resource_id=updated.id,
            metadata={"sku": updated.sku, "active": updated.active},
        )
        return self._to_item_dto(updated)

    # --------------------------------------------------------------------------
    # Inventory Locations
    # --------------------------------------------------------------------------

    async def create_location(
        self, organization_id: uuid.UUID, dto: InventoryLocationCreateDTO, actor_id: uuid.UUID
    ) -> InventoryLocationResponseDTO:
        site = await site_repo.get_by_id(dto.site_id)
        if not site or site.organization_id != organization_id:
            raise EntityNotFoundException("Site not found in this organization.")

        existing = await self._loc_repo.get_by_code(organization_id, dto.site_id, dto.code)
        if existing:
            raise EntityAlreadyExistsException(f"Location with code '{dto.code}' already exists at this site.")

        loc = InventoryLocation(
            organization_id=organization_id,
            site_id=dto.site_id,
            plant_id=dto.plant_id,
            code=dto.code,
            name=dto.name,
            active=True,
        )
        saved = await self._loc_repo.add(loc)
        return self._to_loc_dto(saved)

    async def list_locations(
        self, organization_id: uuid.UUID, site_id: Optional[uuid.UUID] = None, limit: int = 100, offset: int = 0
    ) -> List[InventoryLocationResponseDTO]:
        locs = await self._loc_repo.list_by_organization(organization_id, site_id=site_id, limit=limit, offset=offset)
        return [self._to_loc_dto(l) for l in locs]

    # --------------------------------------------------------------------------
    # Inventory Stock Movements
    # --------------------------------------------------------------------------

    async def receive_stock(
        self, organization_id: uuid.UUID, dto: InventoryReceiptDTO, actor_id: uuid.UUID
    ) -> InventoryBalanceResponseDTO:
        item = await self._item_repo.get_by_id(dto.item_id)
        if not item or item.organization_id != organization_id:
            raise EntityNotFoundException("Item not found in this organization.")

        loc = await self._loc_repo.get_by_id(dto.location_id)
        if not loc or loc.organization_id != organization_id:
            raise EntityNotFoundException("Location not found in this organization.")

        balance = await self._bal_repo.get_by_item_and_location(organization_id, dto.item_id, dto.location_id)
        if not balance:
            balance = InventoryBalance(
                organization_id=organization_id,
                item_id=dto.item_id,
                location_id=dto.location_id,
                quantity=dto.quantity,
            )
            balance = await self._bal_repo.add(balance)
        else:
            balance.increase(dto.quantity)
            balance = await self._bal_repo.update(balance)

        tx = InventoryTransaction(
            organization_id=organization_id,
            item_id=dto.item_id,
            location_id=dto.location_id,
            transaction_type=TransactionType.RECEIPT.value,
            quantity=dto.quantity,
            created_by=actor_id,
            reference_type=dto.reference_type,
            reference_id=dto.reference_id,
        )
        await self._tx_repo.add(tx)

        await self._emit(
            DomainEvent(
                event_type="InventoryReceived",
                aggregate_id=str(balance.id),
                aggregate_type="InventoryBalance",
                organization_id=str(organization_id),
                payload={
                    "item_id": str(dto.item_id),
                    "location_id": str(dto.location_id),
                    "quantity": dto.quantity,
                    "new_balance": balance.quantity,
                },
            )
        )

        await audit_service.log_action(
            actor_id=actor_id,
            organization_id=organization_id,
            action="INVENTORY_RECEIVED",
            resource_type="InventoryBalance",
            resource_id=balance.id,
            metadata={"item_id": str(dto.item_id), "location_id": str(dto.location_id), "quantity": dto.quantity},
        )
        return self._to_balance_dto(balance)

    async def issue_stock(
        self, organization_id: uuid.UUID, dto: InventoryIssueDTO, actor_id: uuid.UUID
    ) -> InventoryBalanceResponseDTO:
        item = await self._item_repo.get_by_id(dto.item_id)
        if not item or item.organization_id != organization_id:
            raise EntityNotFoundException("Item not found in this organization.")

        loc = await self._loc_repo.get_by_id(dto.location_id)
        if not loc or loc.organization_id != organization_id:
            raise EntityNotFoundException("Location not found in this organization.")

        balance = await self._bal_repo.get_by_item_and_location(organization_id, dto.item_id, dto.location_id)
        if not balance:
            raise BusinessRuleViolationException(
                f"No inventory balance exists for item '{dto.item_id}' at location '{dto.location_id}'.",
                rule_name="INSUFFICIENT_INVENTORY",
            )

        balance.decrease(dto.quantity)
        balance = await self._bal_repo.update(balance)

        tx = InventoryTransaction(
            organization_id=organization_id,
            item_id=dto.item_id,
            location_id=dto.location_id,
            transaction_type=TransactionType.ISSUE.value,
            quantity=-dto.quantity,
            created_by=actor_id,
            reference_type=dto.reference_type,
            reference_id=dto.reference_id,
        )
        await self._tx_repo.add(tx)

        await self._emit(
            DomainEvent(
                event_type="InventoryIssued",
                aggregate_id=str(balance.id),
                aggregate_type="InventoryBalance",
                organization_id=str(organization_id),
                payload={
                    "item_id": str(dto.item_id),
                    "location_id": str(dto.location_id),
                    "quantity": dto.quantity,
                    "new_balance": balance.quantity,
                },
            )
        )

        await audit_service.log_action(
            actor_id=actor_id,
            organization_id=organization_id,
            action="INVENTORY_ISSUED",
            resource_type="InventoryBalance",
            resource_id=balance.id,
            metadata={"item_id": str(dto.item_id), "location_id": str(dto.location_id), "quantity": dto.quantity},
        )
        return self._to_balance_dto(balance)

    async def adjust_stock(
        self, organization_id: uuid.UUID, dto: InventoryAdjustmentDTO, actor_id: uuid.UUID
    ) -> InventoryBalanceResponseDTO:
        item = await self._item_repo.get_by_id(dto.item_id)
        if not item or item.organization_id != organization_id:
            raise EntityNotFoundException("Item not found in this organization.")

        loc = await self._loc_repo.get_by_id(dto.location_id)
        if not loc or loc.organization_id != organization_id:
            raise EntityNotFoundException("Location not found in this organization.")

        balance = await self._bal_repo.get_by_item_and_location(organization_id, dto.item_id, dto.location_id)
        if not balance:
            balance = InventoryBalance(
                organization_id=organization_id,
                item_id=dto.item_id,
                location_id=dto.location_id,
                quantity=dto.new_quantity,
            )
            balance = await self._bal_repo.add(balance)
            delta = dto.new_quantity
        else:
            delta = balance.adjust(dto.new_quantity)
            balance = await self._bal_repo.update(balance)

        tx = InventoryTransaction(
            organization_id=organization_id,
            item_id=dto.item_id,
            location_id=dto.location_id,
            transaction_type=TransactionType.ADJUSTMENT.value,
            quantity=delta,
            created_by=actor_id,
            reference_type="MANUAL_ADJUSTMENT",
        )
        await self._tx_repo.add(tx)

        await self._emit(
            DomainEvent(
                event_type="InventoryAdjusted",
                aggregate_id=str(balance.id),
                aggregate_type="InventoryBalance",
                organization_id=str(organization_id),
                payload={
                    "item_id": str(dto.item_id),
                    "location_id": str(dto.location_id),
                    "delta": delta,
                    "new_balance": balance.quantity,
                    "reason": dto.reason,
                },
            )
        )

        await audit_service.log_action(
            actor_id=actor_id,
            organization_id=organization_id,
            action="INVENTORY_ADJUSTED",
            resource_type="InventoryBalance",
            resource_id=balance.id,
            metadata={"item_id": str(dto.item_id), "location_id": str(dto.location_id), "delta": delta, "reason": dto.reason},
        )
        return self._to_balance_dto(balance)

    async def transfer_stock(
        self, organization_id: uuid.UUID, dto: InventoryTransferDTO, actor_id: uuid.UUID
    ) -> Tuple[InventoryBalanceResponseDTO, InventoryBalanceResponseDTO]:
        if dto.source_location_id == dto.destination_location_id:
            raise BusinessRuleViolationException(
                "Source and destination locations must be distinct.",
                rule_name="IDENTICAL_TRANSFER_LOCATIONS",
            )

        item = await self._item_repo.get_by_id(dto.item_id)
        if not item or item.organization_id != organization_id:
            raise EntityNotFoundException("Item not found in this organization.")

        src_loc = await self._loc_repo.get_by_id(dto.source_location_id)
        dest_loc = await self._loc_repo.get_by_id(dto.destination_location_id)
        if not src_loc or src_loc.organization_id != organization_id:
            raise EntityNotFoundException("Source location not found in this organization.")
        if not dest_loc or dest_loc.organization_id != organization_id:
            raise EntityNotFoundException("Destination location not found in this organization.")

        src_bal = await self._bal_repo.get_by_item_and_location(organization_id, dto.item_id, dto.source_location_id)
        if not src_bal or src_bal.available_quantity < dto.quantity:
            avail = src_bal.available_quantity if src_bal else 0.0
            raise BusinessRuleViolationException(
                f"Insufficient inventory at source location (requested {dto.quantity}, available {avail}).",
                rule_name="INSUFFICIENT_INVENTORY",
            )

        # Atomic deduction from source
        src_bal.decrease(dto.quantity)
        src_bal = await self._bal_repo.update(src_bal)

        # Atomic addition to destination
        dest_bal = await self._bal_repo.get_by_item_and_location(organization_id, dto.item_id, dto.destination_location_id)
        if not dest_bal:
            dest_bal = InventoryBalance(
                organization_id=organization_id,
                item_id=dto.item_id,
                location_id=dto.destination_location_id,
                quantity=dto.quantity,
            )
            dest_bal = await self._bal_repo.add(dest_bal)
        else:
            dest_bal.increase(dto.quantity)
            dest_bal = await self._bal_repo.update(dest_bal)

        transfer_ref_id = uuid.uuid4()
        tx_out = InventoryTransaction(
            organization_id=organization_id,
            item_id=dto.item_id,
            location_id=dto.source_location_id,
            transaction_type=TransactionType.TRANSFER_OUT.value,
            quantity=-dto.quantity,
            created_by=actor_id,
            reference_type="INVENTORY_TRANSFER",
            reference_id=transfer_ref_id,
        )
        tx_in = InventoryTransaction(
            organization_id=organization_id,
            item_id=dto.item_id,
            location_id=dto.destination_location_id,
            transaction_type=TransactionType.TRANSFER_IN.value,
            quantity=dto.quantity,
            created_by=actor_id,
            reference_type="INVENTORY_TRANSFER",
            reference_id=transfer_ref_id,
        )
        await self._tx_repo.add(tx_out)
        await self._tx_repo.add(tx_in)

        await self._emit(
            DomainEvent(
                event_type="InventoryTransferred",
                aggregate_id=str(transfer_ref_id),
                aggregate_type="InventoryTransfer",
                organization_id=str(organization_id),
                payload={
                    "item_id": str(dto.item_id),
                    "source_location_id": str(dto.source_location_id),
                    "destination_location_id": str(dto.destination_location_id),
                    "quantity": dto.quantity,
                },
            )
        )

        await audit_service.log_action(
            actor_id=actor_id,
            organization_id=organization_id,
            action="INVENTORY_TRANSFERRED",
            resource_type="InventoryBalance",
            resource_id=transfer_ref_id,
            metadata={
                "item_id": str(dto.item_id),
                "source_location_id": str(dto.source_location_id),
                "destination_location_id": str(dto.destination_location_id),
                "quantity": dto.quantity,
            },
        )
        return self._to_balance_dto(src_bal), self._to_balance_dto(dest_bal)

    async def list_balances(
        self,
        organization_id: uuid.UUID,
        item_id: Optional[uuid.UUID] = None,
        location_id: Optional[uuid.UUID] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[InventoryBalanceResponseDTO]:
        balances = await self._bal_repo.list_by_organization(
            organization_id, item_id=item_id, location_id=location_id, limit=limit, offset=offset
        )
        return [self._to_balance_dto(b) for b in balances]

    # --------------------------------------------------------------------------
    # Material Consumption Integration
    # --------------------------------------------------------------------------

    async def consume_material(
        self,
        organization_id: uuid.UUID,
        consumer_type: str,
        consumer_id: uuid.UUID,
        item_id: uuid.UUID,
        location_id: uuid.UUID,
        quantity: float,
        actor_id: uuid.UUID,
    ) -> InventoryTransaction:
        item = await self._item_repo.get_by_id(item_id)
        if not item or item.organization_id != organization_id:
            raise EntityNotFoundException("Item not found in this organization.")

        loc = await self._loc_repo.get_by_id(location_id)
        if not loc or loc.organization_id != organization_id:
            raise EntityNotFoundException("Inventory location not found in this organization.")

        balance = await self._bal_repo.get_by_item_and_location(organization_id, item_id, location_id)
        if not balance or balance.available_quantity < quantity:
            avail = balance.available_quantity if balance else 0.0
            raise BusinessRuleViolationException(
                f"Insufficient inventory to consume item '{item.sku}' (requested {quantity}, available {avail}).",
                rule_name="INSUFFICIENT_INVENTORY",
            )

        balance.decrease(quantity)
        await self._bal_repo.update(balance)

        tx = InventoryTransaction(
            organization_id=organization_id,
            item_id=item_id,
            location_id=location_id,
            transaction_type=TransactionType.ISSUE.value,
            quantity=-quantity,
            created_by=actor_id,
            reference_type=consumer_type,
            reference_id=consumer_id,
        )
        saved_tx = await self._tx_repo.add(tx)

        await self._emit(
            DomainEvent(
                event_type="InventoryIssued",
                aggregate_id=str(balance.id),
                aggregate_type="InventoryBalance",
                organization_id=str(organization_id),
                payload={
                    "item_id": str(item_id),
                    "location_id": str(location_id),
                    "quantity": quantity,
                    "consumer_type": consumer_type,
                    "consumer_id": str(consumer_id),
                },
            )
        )

        return saved_tx

    # --------------------------------------------------------------------------
    # DTO Mappings
    # --------------------------------------------------------------------------

    def _to_item_dto(self, item: Item) -> ItemResponseDTO:
        return ItemResponseDTO(
            id=item.id,
            organization_id=item.organization_id,
            sku=item.sku,
            name=item.name,
            unit_of_measure=item.unit_of_measure,
            category=item.category,
            description=item.description,
            active=item.active,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )

    def _to_loc_dto(self, loc: InventoryLocation) -> InventoryLocationResponseDTO:
        return InventoryLocationResponseDTO(
            id=loc.id,
            organization_id=loc.organization_id,
            site_id=loc.site_id,
            plant_id=loc.plant_id,
            code=loc.code,
            name=loc.name,
            active=loc.active,
            created_at=loc.created_at,
            updated_at=loc.updated_at,
        )

    def _to_balance_dto(self, bal: InventoryBalance) -> InventoryBalanceResponseDTO:
        return InventoryBalanceResponseDTO(
            id=bal.id,
            organization_id=bal.organization_id,
            item_id=bal.item_id,
            location_id=bal.location_id,
            quantity=bal.quantity,
            reserved_quantity=bal.reserved_quantity,
            available_quantity=bal.available_quantity,
            version=bal.version,
            created_at=bal.created_at,
            updated_at=bal.updated_at,
        )


# Singleton service instance
inventory_service = InventoryService()
