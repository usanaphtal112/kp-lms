from django.urls import path

from .views import (
    InventoryBalanceExportView,
    InventoryCategoryCreateView,
    InventoryCategoryListView,
    InventoryCategoryUpdateView,
    InventoryDashboardView,
    InventoryUsageApproveView,
    InventoryUsageCreateView,
    InventoryUsageDetailView,
    InventoryUsageItemCreateView,
    InventoryUsageListView,
    InventoryUsageRejectView,
    InventoryUsageSubmitView,
    LowStockAlertListView,
    StockBatchAdjustmentView,
    StockBatchListView,
    StockBatchReceiveView,
    StockItemCreateView,
    StockItemDetailView,
    StockItemListView,
    StockItemUpdateView,
    StockMovementExportView,
    StockMovementListView,
    SupplierCreateView,
    SupplierListView,
    SupplierUpdateView,
)


app_name = "inventory"

urlpatterns = [
    path("", InventoryDashboardView.as_view(), name="dashboard"),

    path("categories/", InventoryCategoryListView.as_view(), name="category_list"),
    path("categories/create/", InventoryCategoryCreateView.as_view(), name="category_create"),
    path("categories/<int:pk>/update/", InventoryCategoryUpdateView.as_view(), name="category_update"),

    path("suppliers/", SupplierListView.as_view(), name="supplier_list"),
    path("suppliers/create/", SupplierCreateView.as_view(), name="supplier_create"),
    path("suppliers/<int:pk>/update/", SupplierUpdateView.as_view(), name="supplier_update"),

    path("items/", StockItemListView.as_view(), name="stockitem_list"),
    path("items/create/", StockItemCreateView.as_view(), name="stockitem_create"),
    path("items/<int:pk>/", StockItemDetailView.as_view(), name="stockitem_detail"),
    path("items/<int:pk>/update/", StockItemUpdateView.as_view(), name="stockitem_update"),

    path("batches/", StockBatchListView.as_view(), name="stockbatch_list"),
    path("batches/receive/", StockBatchReceiveView.as_view(), name="stockbatch_receive"),
    path("batches/<int:pk>/adjust/", StockBatchAdjustmentView.as_view(), name="stockbatch_adjust"),

    path("movements/", StockMovementListView.as_view(), name="movement_list"),

    path("usages/", InventoryUsageListView.as_view(), name="usage_list"),
    path("usages/create/", InventoryUsageCreateView.as_view(), name="usage_create"),
    path("usages/<int:pk>/", InventoryUsageDetailView.as_view(), name="usage_detail"),
    path("usages/<int:usage_pk>/items/add/", InventoryUsageItemCreateView.as_view(), name="usage_item_add"),
    path("usages/<int:pk>/submit/", InventoryUsageSubmitView.as_view(), name="usage_submit"),
    path("usages/<int:pk>/approve/", InventoryUsageApproveView.as_view(), name="usage_approve"),
    path("usages/<int:pk>/reject/", InventoryUsageRejectView.as_view(), name="usage_reject"),

    path("low-stock/", LowStockAlertListView.as_view(), name="low_stock_list"),

    path("exports/balances/", InventoryBalanceExportView.as_view(), name="export_balances"),
    path("exports/movements/", StockMovementExportView.as_view(), name="export_movements"),
]