from django.contrib import admin

from .models import (
    InventoryCategory,
    InventoryUsage,
    InventoryUsageItem,
    LowStockAlert,
    StockBatch,
    StockItem,
    StockMovement,
    Supplier,
)


@admin.register(InventoryCategory)
class InventoryCategoryAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "is_active"]
    search_fields = ["code", "name"]
    list_filter = ["is_active"]


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ["name", "contact_person", "phone_number", "email", "is_active"]
    search_fields = ["name", "contact_person", "phone_number", "email"]
    list_filter = ["is_active"]


@admin.register(StockItem)
class StockItemAdmin(admin.ModelAdmin):
    list_display = [
        "code",
        "name",
        "category",
        "item_type",
        "unit",
        "minimum_stock_level",
        "reorder_level",
        "is_active",
    ]
    search_fields = ["code", "name", "category__name"]
    list_filter = ["category", "item_type", "unit", "is_active"]


@admin.register(StockBatch)
class StockBatchAdmin(admin.ModelAdmin):
    list_display = [
        "stock_item",
        "batch_number",
        "quantity_received",
        "quantity_remaining",
        "received_at",
        "expiry_date",
        "status",
    ]
    search_fields = ["stock_item__code", "stock_item__name", "batch_number"]
    list_filter = ["status", "received_at", "expiry_date"]
    autocomplete_fields = ["stock_item", "supplier"]


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = [
        "stock_item",
        "stock_batch",
        "movement_type",
        "quantity",
        "performed_by",
        "performed_at",
        "reference",
    ]
    search_fields = ["stock_item__code", "stock_item__name", "reference", "reason"]
    list_filter = ["movement_type", "performed_at"]
    autocomplete_fields = ["stock_item", "stock_batch", "performed_by"]
    readonly_fields = [
        "stock_item",
        "stock_batch",
        "movement_type",
        "quantity",
        "performed_by",
        "performed_at",
        "reason",
        "reference",
    ]

    def has_add_permission(self, request):
        return False


class InventoryUsageItemInline(admin.TabularInline):
    model = InventoryUsageItem
    extra = 1


@admin.register(InventoryUsage)
class InventoryUsageAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "usage_context",
        "status",
        "submitted_by",
        "submitted_at",
        "approved_by",
        "approved_at",
    ]
    search_fields = ["title", "submitted_by__username", "notes"]
    list_filter = ["usage_context", "status", "submitted_at", "approved_at"]
    autocomplete_fields = [
        "submitted_by",
        "approved_by",
        "demonstration_session",
        "self_practice_session",
        "osce_exam",
    ]
    inlines = [InventoryUsageItemInline]


@admin.register(InventoryUsageItem)
class InventoryUsageItemAdmin(admin.ModelAdmin):
    list_display = [
        "usage",
        "stock_item",
        "quantity_requested",
        "quantity_approved",
    ]
    search_fields = ["usage__title", "stock_item__code", "stock_item__name"]
    autocomplete_fields = ["usage", "stock_item"]


@admin.register(LowStockAlert)
class LowStockAlertAdmin(admin.ModelAdmin):
    list_display = [
        "stock_item",
        "current_quantity",
        "threshold",
        "status",
        "created_at",
        "resolved_at",
    ]
    search_fields = ["stock_item__code", "stock_item__name"]
    list_filter = ["status", "created_at"]
    autocomplete_fields = ["stock_item", "resolved_by"]