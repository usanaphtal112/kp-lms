from decimal import Decimal

import pytest

from apps.inventory.services import approve_inventory_usage, get_available_quantity


@pytest.mark.django_db
def test_approved_usage_deducts_stock(stock_item, stock_batch_factory, inventory_usage, inventory_usage_item_factory, admin_user):
    stock_batch_factory(
        stock_item=stock_item,
        quantity_received=Decimal("100.00"),
        quantity_remaining=Decimal("100.00"),
    )

    inventory_usage_item_factory(
        usage=inventory_usage,
        stock_item=stock_item,
        quantity_requested=Decimal("25.00"),
    )

    inventory_usage.status = "SUBMITTED"
    inventory_usage.save()

    approve_inventory_usage(
        usage=inventory_usage,
        approved_by=admin_user,
    )

    assert get_available_quantity(stock_item) == Decimal("75.00")