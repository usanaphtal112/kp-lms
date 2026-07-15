from decimal import Decimal

from django.db import transaction
from django.db.models import F, Sum
from django.utils import timezone

from .models import (
    InventoryUsage,
    InventoryUsageItem,
    InventoryUsageStatus,
    LowStockAlert,
    LowStockAlertStatus,
    StockBatch,
    StockBatchStatus,
    StockItem,
    StockMovement,
    StockMovementType,
)


def get_available_quantity(stock_item):
    result = stock_item.batches.filter(
        is_active=True,
        status=StockBatchStatus.AVAILABLE,
        quantity_remaining__gt=0,
    ).aggregate(
        total=Sum("quantity_remaining")
    )

    return result["total"] or Decimal("0.00")


def get_stock_item_balances():
    stock_items = StockItem.objects.select_related("category").filter(is_active=True)

    balances = []

    for item in stock_items:
        available_quantity = get_available_quantity(item)
        balances.append(
            {
                "stock_item": item,
                "available_quantity": available_quantity,
                "minimum_stock_level": item.minimum_stock_level,
                "reorder_level": item.reorder_level,
                "is_low_stock": available_quantity <= item.minimum_stock_level,
            }
        )

    return balances


@transaction.atomic
def receive_stock_batch(
    *,
    stock_item,
    supplier=None,
    batch_number,
    quantity_received,
    unit_cost=Decimal("0.00"),
    received_at=None,
    expiry_date=None,
    received_by=None,
    notes="",
):
    batch = StockBatch.objects.create(
        stock_item=stock_item,
        supplier=supplier,
        batch_number=batch_number,
        quantity_received=quantity_received,
        quantity_remaining=quantity_received,
        unit_cost=unit_cost,
        received_at=received_at or timezone.localdate(),
        expiry_date=expiry_date,
        notes=notes,
    )

    StockMovement.objects.create(
        stock_item=stock_item,
        stock_batch=batch,
        movement_type=StockMovementType.IN,
        quantity=quantity_received,
        performed_by=received_by,
        reason="Stock batch received.",
        reference=f"BATCH-{batch.pk}",
    )

    resolve_low_stock_if_recovered(stock_item, resolved_by=received_by)

    return batch


@transaction.atomic
def adjust_stock_batch(
    *,
    stock_batch,
    quantity,
    adjustment_type,
    adjusted_by,
    reason,
):
    if adjustment_type not in [
        StockMovementType.ADJUSTMENT_IN,
        StockMovementType.ADJUSTMENT_OUT,
        StockMovementType.DAMAGED,
        StockMovementType.EXPIRED,
    ]:
        raise ValueError("Invalid adjustment type.")

    locked_batch = StockBatch.objects.select_for_update().get(pk=stock_batch.pk)

    if adjustment_type == StockMovementType.ADJUSTMENT_IN:
        locked_batch.quantity_remaining = F("quantity_remaining") + quantity
        movement_type = StockMovementType.ADJUSTMENT_IN
    else:
        if locked_batch.quantity_remaining < quantity:
            raise ValueError("Insufficient stock in selected batch.")

        locked_batch.quantity_remaining = F("quantity_remaining") - quantity
        movement_type = adjustment_type

    locked_batch.save(update_fields=["quantity_remaining", "updated_at"])
    locked_batch.refresh_from_db()

    if locked_batch.quantity_remaining == 0:
        locked_batch.status = StockBatchStatus.EXHAUSTED
        locked_batch.save(update_fields=["status", "updated_at"])

    StockMovement.objects.create(
        stock_item=locked_batch.stock_item,
        stock_batch=locked_batch,
        movement_type=movement_type,
        quantity=quantity,
        performed_by=adjusted_by,
        reason=reason,
        reference=f"ADJUST-{locked_batch.pk}",
    )

    create_low_stock_alert_if_needed(locked_batch.stock_item)

    return locked_batch


@transaction.atomic
def submit_inventory_usage(*, usage, submitted_by):
    if usage.status != InventoryUsageStatus.DRAFT:
        raise ValueError("Only draft inventory usage can be submitted.")

    if not usage.items.exists():
        raise ValueError("Inventory usage must have at least one item.")

    usage.status = InventoryUsageStatus.SUBMITTED
    usage.submitted_by = submitted_by
    usage.submitted_at = timezone.now()
    usage.save(
        update_fields=[
            "status",
            "submitted_by",
            "submitted_at",
            "updated_at",
        ]
    )

    return usage


@transaction.atomic
def approve_inventory_usage(*, usage, approved_by):
    usage = InventoryUsage.objects.select_for_update().get(pk=usage.pk)

    if usage.status != InventoryUsageStatus.SUBMITTED:
        raise ValueError("Only submitted inventory usage can be approved.")

    usage_items = usage.items.select_related("stock_item").all()

    for item in usage_items:
        quantity_to_deduct = item.quantity_approved or item.quantity_requested

        if quantity_to_deduct <= 0:
            raise ValueError(
                f"Approved quantity for {item.stock_item} must be greater than zero."
            )

        available_quantity = get_available_quantity(item.stock_item)

        if available_quantity < quantity_to_deduct:
            raise ValueError(
                f"Insufficient stock for {item.stock_item}. "
                f"Available: {available_quantity}, required: {quantity_to_deduct}."
            )

    for item in usage_items:
        quantity_to_deduct = item.quantity_approved or item.quantity_requested

        deduct_stock_item_quantity(
            stock_item=item.stock_item,
            quantity=quantity_to_deduct,
            performed_by=approved_by,
            reason=f"Approved usage: {usage.title}",
            reference=f"USAGE-{usage.pk}",
        )

        item.quantity_approved = quantity_to_deduct
        item.save(update_fields=["quantity_approved"])

    usage.status = InventoryUsageStatus.APPROVED
    usage.approved_by = approved_by
    usage.approved_at = timezone.now()
    usage.rejection_reason = ""
    usage.save(
        update_fields=[
            "status",
            "approved_by",
            "approved_at",
            "rejection_reason",
            "updated_at",
        ]
    )

    return usage


@transaction.atomic
def reject_inventory_usage(*, usage, rejected_by, reason):
    usage = InventoryUsage.objects.select_for_update().get(pk=usage.pk)

    if usage.status != InventoryUsageStatus.SUBMITTED:
        raise ValueError("Only submitted inventory usage can be rejected.")

    usage.status = InventoryUsageStatus.REJECTED
    usage.approved_by = rejected_by
    usage.approved_at = timezone.now()
    usage.rejection_reason = reason
    usage.save(
        update_fields=[
            "status",
            "approved_by",
            "approved_at",
            "rejection_reason",
            "updated_at",
        ]
    )

    return usage


@transaction.atomic
def deduct_stock_item_quantity(*, stock_item, quantity, performed_by, reason, reference):
    remaining_to_deduct = quantity

    batches = (
        StockBatch.objects.select_for_update()
        .filter(
            stock_item=stock_item,
            is_active=True,
            status=StockBatchStatus.AVAILABLE,
            quantity_remaining__gt=0,
        )
        .order_by("expiry_date", "received_at", "pk")
    )

    for batch in batches:
        if remaining_to_deduct <= 0:
            break

        deduct_from_batch = min(batch.quantity_remaining, remaining_to_deduct)

        batch.quantity_remaining = F("quantity_remaining") - deduct_from_batch
        batch.save(update_fields=["quantity_remaining", "updated_at"])
        batch.refresh_from_db()

        if batch.quantity_remaining == 0:
            batch.status = StockBatchStatus.EXHAUSTED
            batch.save(update_fields=["status", "updated_at"])

        StockMovement.objects.create(
            stock_item=stock_item,
            stock_batch=batch,
            movement_type=StockMovementType.OUT,
            quantity=deduct_from_batch,
            performed_by=performed_by,
            reason=reason,
            reference=reference,
        )

        remaining_to_deduct -= deduct_from_batch

    if remaining_to_deduct > 0:
        raise ValueError(f"Insufficient stock for {stock_item}.")

    create_low_stock_alert_if_needed(stock_item)

    return True


def create_low_stock_alert_if_needed(stock_item):
    current_quantity = get_available_quantity(stock_item)

    if current_quantity > stock_item.minimum_stock_level:
        return None

    existing_open_alert = LowStockAlert.objects.filter(
        stock_item=stock_item,
        status=LowStockAlertStatus.OPEN,
    ).first()

    if existing_open_alert:
        existing_open_alert.current_quantity = current_quantity
        existing_open_alert.threshold = stock_item.minimum_stock_level
        existing_open_alert.save(
            update_fields=[
                "current_quantity",
                "threshold",
            ]
        )
        return existing_open_alert

    return LowStockAlert.objects.create(
        stock_item=stock_item,
        current_quantity=current_quantity,
        threshold=stock_item.minimum_stock_level,
    )


def resolve_low_stock_if_recovered(stock_item, resolved_by=None):
    current_quantity = get_available_quantity(stock_item)

    if current_quantity <= stock_item.minimum_stock_level:
        return 0

    updated_count = LowStockAlert.objects.filter(
        stock_item=stock_item,
        status=LowStockAlertStatus.OPEN,
    ).update(
        status=LowStockAlertStatus.RESOLVED,
        resolved_at=timezone.now(),
        resolved_by=resolved_by,
    )

    return updated_count