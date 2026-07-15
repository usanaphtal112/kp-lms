from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import (
    CreateView,
    DetailView,
    FormView,
    ListView,
    TemplateView,
    UpdateView,
)

from .exports import (
    export_inventory_balances_workbook,
    export_stock_movements_workbook,
)
from .forms import (
    InventoryCategoryForm,
    InventoryUsageForm,
    InventoryUsageItemForm,
    InventoryUsageRejectForm,
    InventoryUsageSubmitForm,
    StockAdjustmentForm,
    StockBatchReceiveForm,
    StockItemForm,
    SupplierForm,
)
from .mixins import (
    InventoryApproverRequiredMixin,
    InventoryManagerRequiredMixin,
    InventorySubmitterRequiredMixin,
    InventoryViewerRequiredMixin,
)
from .models import (
    InventoryCategory,
    InventoryUsage,
    InventoryUsageItem,
    InventoryUsageStatus,
    LowStockAlert,
    StockBatch,
    StockItem,
    StockMovement,
    Supplier,
)
from .services import (
    adjust_stock_batch,
    approve_inventory_usage,
    get_available_quantity,
    get_stock_item_balances,
    receive_stock_batch,
    reject_inventory_usage,
    submit_inventory_usage,
)


class InventoryDashboardView(InventoryViewerRequiredMixin, TemplateView):
    template_name = "inventory/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["stock_item_count"] = StockItem.objects.count()
        context["batch_count"] = StockBatch.objects.count()
        context["submitted_usage_count"] = InventoryUsage.objects.filter(
            status=InventoryUsageStatus.SUBMITTED
        ).count()
        context["low_stock_count"] = LowStockAlert.objects.filter(
            status="OPEN"
        ).count()
        context["balances"] = get_stock_item_balances()[:10]

        return context


class InventoryCategoryListView(InventoryManagerRequiredMixin, ListView):
    model = InventoryCategory
    template_name = "inventory/category_list.html"
    context_object_name = "categories"
    paginate_by = 20


class InventoryCategoryCreateView(InventoryManagerRequiredMixin, CreateView):
    model = InventoryCategory
    form_class = InventoryCategoryForm
    template_name = "inventory/object_form.html"
    success_url = reverse_lazy("inventory:category_list")


class InventoryCategoryUpdateView(InventoryManagerRequiredMixin, UpdateView):
    model = InventoryCategory
    form_class = InventoryCategoryForm
    template_name = "inventory/object_form.html"
    success_url = reverse_lazy("inventory:category_list")


class SupplierListView(InventoryManagerRequiredMixin, ListView):
    model = Supplier
    template_name = "inventory/supplier_list.html"
    context_object_name = "suppliers"
    paginate_by = 20


class SupplierCreateView(InventoryManagerRequiredMixin, CreateView):
    model = Supplier
    form_class = SupplierForm
    template_name = "inventory/object_form.html"
    success_url = reverse_lazy("inventory:supplier_list")


class SupplierUpdateView(InventoryManagerRequiredMixin, UpdateView):
    model = Supplier
    form_class = SupplierForm
    template_name = "inventory/object_form.html"
    success_url = reverse_lazy("inventory:supplier_list")


class StockItemListView(InventoryViewerRequiredMixin, ListView):
    model = StockItem
    template_name = "inventory/stockitem_list.html"
    context_object_name = "stock_items"
    paginate_by = 30

    def get_queryset(self):
        queryset = StockItem.objects.select_related("category").order_by("name")

        q = self.request.GET.get("q")

        if q:
            queryset = queryset.filter(
                Q(code__icontains=q)
                | Q(name__icontains=q)
                | Q(category__name__icontains=q)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["stock_rows"] = [
            {
                "stock_item": item,
                "available_quantity": get_available_quantity(item),
            }
            for item in context["stock_items"]
        ]

        return context


class StockItemCreateView(InventoryManagerRequiredMixin, CreateView):
    model = StockItem
    form_class = StockItemForm
    template_name = "inventory/object_form.html"
    success_url = reverse_lazy("inventory:stockitem_list")


class StockItemUpdateView(InventoryManagerRequiredMixin, UpdateView):
    model = StockItem
    form_class = StockItemForm
    template_name = "inventory/object_form.html"
    success_url = reverse_lazy("inventory:stockitem_list")


class StockItemDetailView(InventoryViewerRequiredMixin, DetailView):
    model = StockItem
    template_name = "inventory/stockitem_detail.html"
    context_object_name = "stock_item"

    def get_queryset(self):
        return StockItem.objects.select_related("category").prefetch_related(
            "batches",
            "movements",
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["available_quantity"] = get_available_quantity(self.object)
        context["batches"] = self.object.batches.select_related("supplier")
        context["movements"] = self.object.movements.select_related(
            "stock_batch",
            "performed_by",
        )[:20]
        return context


class StockBatchListView(InventoryViewerRequiredMixin, ListView):
    model = StockBatch
    template_name = "inventory/stockbatch_list.html"
    context_object_name = "batches"
    paginate_by = 30

    def get_queryset(self):
        return StockBatch.objects.select_related(
            "stock_item",
            "supplier",
        ).order_by("expiry_date", "received_at")


class StockBatchReceiveView(InventoryManagerRequiredMixin, FormView):
    template_name = "inventory/batch_receive_form.html"
    form_class = StockBatchReceiveForm

    def form_valid(self, form):
        receive_stock_batch(
            stock_item=form.cleaned_data["stock_item"],
            supplier=form.cleaned_data["supplier"],
            batch_number=form.cleaned_data["batch_number"],
            quantity_received=form.cleaned_data["quantity_received"],
            unit_cost=form.cleaned_data["unit_cost"],
            received_at=form.cleaned_data["received_at"],
            expiry_date=form.cleaned_data["expiry_date"],
            received_by=self.request.user,
            notes=form.cleaned_data["notes"],
        )

        messages.success(self.request, "Stock batch received successfully.")

        return redirect("inventory:stockbatch_list")


class StockBatchAdjustmentView(InventoryManagerRequiredMixin, FormView):
    template_name = "inventory/batch_adjust_form.html"
    form_class = StockAdjustmentForm

    def dispatch(self, request, *args, **kwargs):
        self.batch = get_object_or_404(StockBatch, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        try:
            adjust_stock_batch(
                stock_batch=self.batch,
                quantity=form.cleaned_data["quantity"],
                adjustment_type=form.cleaned_data["adjustment_type"],
                adjusted_by=self.request.user,
                reason=form.cleaned_data["reason"],
            )
        except Exception as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)

        messages.success(self.request, "Stock adjustment saved successfully.")

        return redirect("inventory:stockbatch_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["batch"] = self.batch
        return context


class StockMovementListView(InventoryViewerRequiredMixin, ListView):
    model = StockMovement
    template_name = "inventory/movement_list.html"
    context_object_name = "movements"
    paginate_by = 40

    def get_queryset(self):
        return StockMovement.objects.select_related(
            "stock_item",
            "stock_batch",
            "performed_by",
        ).order_by("-performed_at")


class InventoryUsageListView(InventorySubmitterRequiredMixin, ListView):
    model = InventoryUsage
    template_name = "inventory/usage_list.html"
    context_object_name = "usages"
    paginate_by = 30

    def get_queryset(self):
        queryset = InventoryUsage.objects.select_related(
            "submitted_by",
            "approved_by",
            "demonstration_session",
            "self_practice_session",
            "osce_exam",
        )

        role = getattr(self.request.user, "role", None)

        if role == "LECTURER":
            queryset = queryset.filter(submitted_by=self.request.user)

        return queryset.order_by("-created_at")


class InventoryUsageCreateView(InventorySubmitterRequiredMixin, CreateView):
    model = InventoryUsage
    form_class = InventoryUsageForm
    template_name = "inventory/usage_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.submitted_by = self.request.user
        messages.success(
            self.request,
            "Inventory usage created. Add usage items before submitting.",
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("inventory:usage_detail", kwargs={"pk": self.object.pk})


class InventoryUsageDetailView(InventorySubmitterRequiredMixin, DetailView):
    model = InventoryUsage
    template_name = "inventory/usage_detail.html"
    context_object_name = "usage"

    def get_queryset(self):
        queryset = InventoryUsage.objects.select_related(
            "submitted_by",
            "approved_by",
            "demonstration_session",
            "self_practice_session",
            "osce_exam",
        ).prefetch_related("items__stock_item")

        role = getattr(self.request.user, "role", None)

        if role == "LECTURER":
            queryset = queryset.filter(submitted_by=self.request.user)

        return queryset


class InventoryUsageItemCreateView(InventorySubmitterRequiredMixin, CreateView):
    model = InventoryUsageItem
    form_class = InventoryUsageItemForm
    template_name = "inventory/usage_item_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.usage = get_object_or_404(InventoryUsage, pk=kwargs["usage_pk"])

        if self.usage.status != InventoryUsageStatus.DRAFT:
            messages.error(request, "Items can only be added to draft usage records.")
            return redirect("inventory:usage_detail", pk=self.usage.pk)

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.usage = self.usage
        messages.success(self.request, "Usage item added successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("inventory:usage_detail", kwargs={"pk": self.usage.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["usage"] = self.usage
        return context


class InventoryUsageSubmitView(InventorySubmitterRequiredMixin, FormView):
    template_name = "inventory/usage_submit_form.html"
    form_class = InventoryUsageSubmitForm

    def dispatch(self, request, *args, **kwargs):
        self.usage = get_object_or_404(InventoryUsage, pk=kwargs["pk"])

        if self.usage.submitted_by_id != request.user.id and getattr(request.user, "role", None) == "LECTURER":
            messages.error(request, "You can only submit your own inventory usage.")
            return redirect("inventory:usage_list")

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        try:
            submit_inventory_usage(
                usage=self.usage,
                submitted_by=self.request.user,
            )
        except Exception as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)

        messages.success(self.request, "Inventory usage submitted for approval.")

        return redirect("inventory:usage_detail", pk=self.usage.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["usage"] = self.usage
        return context


class InventoryUsageApproveView(InventoryApproverRequiredMixin, View):
    def post(self, request, pk):
        usage = get_object_or_404(InventoryUsage, pk=pk)

        try:
            approve_inventory_usage(
                usage=usage,
                approved_by=request.user,
            )
        except Exception as exc:
            messages.error(request, str(exc))
            return redirect("inventory:usage_detail", pk=usage.pk)

        messages.success(request, "Inventory usage approved and stock deducted.")

        return redirect("inventory:usage_detail", pk=usage.pk)


class InventoryUsageRejectView(InventoryApproverRequiredMixin, FormView):
    template_name = "inventory/usage_reject_form.html"
    form_class = InventoryUsageRejectForm

    def dispatch(self, request, *args, **kwargs):
        self.usage = get_object_or_404(InventoryUsage, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        try:
            reject_inventory_usage(
                usage=self.usage,
                rejected_by=self.request.user,
                reason=form.cleaned_data["reason"],
            )
        except Exception as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)

        messages.success(self.request, "Inventory usage rejected.")

        return redirect("inventory:usage_detail", pk=self.usage.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["usage"] = self.usage
        return context


class LowStockAlertListView(InventoryManagerRequiredMixin, ListView):
    model = LowStockAlert
    template_name = "inventory/low_stock_list.html"
    context_object_name = "alerts"
    paginate_by = 30

    def get_queryset(self):
        return LowStockAlert.objects.select_related(
            "stock_item",
            "resolved_by",
        ).order_by("-created_at")


class InventoryBalanceExportView(InventoryViewerRequiredMixin, View):
    def get(self, request):
        stock_items = StockItem.objects.select_related("category").filter(
            is_active=True
        ).order_by("name")

        return export_inventory_balances_workbook(stock_items)


class StockMovementExportView(InventoryViewerRequiredMixin, View):
    def get(self, request):
        movements = StockMovement.objects.select_related(
            "stock_item",
            "stock_batch",
            "performed_by",
        ).order_by("-performed_at")

        return export_stock_movements_workbook(movements)