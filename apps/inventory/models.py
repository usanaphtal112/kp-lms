from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone


class InventoryBaseModel(models.Model):
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class InventoryCategory(InventoryBaseModel):
    name = models.CharField(max_length=120, unique=True)
    code = models.CharField(max_length=40, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "inventory categories"

    def __str__(self):
        return self.name


class Supplier(InventoryBaseModel):
    name = models.CharField(max_length=180, unique=True)
    contact_person = models.CharField(max_length=120, blank=True)
    phone_number = models.CharField(max_length=40, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class StockUnit(models.TextChoices):
    PIECE = "PIECE", "Piece"
    BOX = "BOX", "Box"
    PACK = "PACK", "Pack"
    PAIR = "PAIR", "Pair"
    BOTTLE = "BOTTLE", "Bottle"
    LITER = "LITER", "Liter"
    MILLILITER = "MILLILITER", "Milliliter"
    GRAM = "GRAM", "Gram"
    KILOGRAM = "KILOGRAM", "Kilogram"
    SET = "SET", "Set"


class StockItemType(models.TextChoices):
    CONSUMABLE = "CONSUMABLE", "Consumable"
    EQUIPMENT = "EQUIPMENT", "Equipment"
    MODEL = "MODEL", "Model / Mannequin"
    PPE = "PPE", "PPE"
    OTHER = "OTHER", "Other"


class StockItem(InventoryBaseModel):
    category = models.ForeignKey(
        InventoryCategory,
        on_delete=models.PROTECT,
        related_name="stock_items",
    )
    name = models.CharField(max_length=180)
    code = models.CharField(max_length=60, unique=True)
    item_type = models.CharField(
        max_length=40,
        choices=StockItemType.choices,
        default=StockItemType.CONSUMABLE,
    )
    unit = models.CharField(
        max_length=40,
        choices=StockUnit.choices,
        default=StockUnit.PIECE,
    )
    minimum_stock_level = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    reorder_level = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["item_type"]),
            models.Index(fields=["is_active"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(minimum_stock_level__gte=0),
                name="stock_item_minimum_level_gte_zero",
            ),
            models.CheckConstraint(
                condition=Q(reorder_level__gte=0),
                name="stock_item_reorder_level_gte_zero",
            ),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"


class StockBatchStatus(models.TextChoices):
    AVAILABLE = "AVAILABLE", "Available"
    EXHAUSTED = "EXHAUSTED", "Exhausted"
    EXPIRED = "EXPIRED", "Expired"
    QUARANTINED = "QUARANTINED", "Quarantined"


class StockBatch(InventoryBaseModel):
    stock_item = models.ForeignKey(
        StockItem,
        on_delete=models.PROTECT,
        related_name="batches",
    )
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.SET_NULL,
        related_name="stock_batches",
        null=True,
        blank=True,
    )
    batch_number = models.CharField(max_length=80)
    quantity_received = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    quantity_remaining = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    unit_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    received_at = models.DateField(default=timezone.localdate)
    expiry_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=40,
        choices=StockBatchStatus.choices,
        default=StockBatchStatus.AVAILABLE,
        db_index=True,
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["expiry_date", "received_at", "batch_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["stock_item", "batch_number"],
                name="unique_batch_number_per_stock_item",
            ),
            models.CheckConstraint(
                condition=Q(quantity_received__gte=0),
                name="stock_batch_quantity_received_gte_zero",
            ),
            models.CheckConstraint(
                condition=Q(quantity_remaining__gte=0),
                name="stock_batch_quantity_remaining_gte_zero",
            ),
            models.CheckConstraint(
                condition=Q(unit_cost__gte=0),
                name="stock_batch_unit_cost_gte_zero",
            ),
        ]

    def clean(self):
        super().clean()

        if self.quantity_remaining and self.quantity_received:
            if self.quantity_remaining > self.quantity_received:
                raise ValidationError(
                    "Quantity remaining cannot be greater than quantity received."
                )

    def __str__(self):
        return f"{self.stock_item.code} - {self.batch_number}"


class StockMovementType(models.TextChoices):
    IN = "IN", "Stock In"
    OUT = "OUT", "Stock Out"
    ADJUSTMENT_IN = "ADJUSTMENT_IN", "Adjustment In"
    ADJUSTMENT_OUT = "ADJUSTMENT_OUT", "Adjustment Out"
    DAMAGED = "DAMAGED", "Damaged"
    EXPIRED = "EXPIRED", "Expired"
    RETURNED = "RETURNED", "Returned"


class StockMovement(models.Model):
    stock_item = models.ForeignKey(
        StockItem,
        on_delete=models.PROTECT,
        related_name="movements",
    )
    stock_batch = models.ForeignKey(
        StockBatch,
        on_delete=models.PROTECT,
        related_name="movements",
        null=True,
        blank=True,
    )
    movement_type = models.CharField(
        max_length=40,
        choices=StockMovementType.choices,
        db_index=True,
    )
    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="stock_movements_performed",
        null=True,
        blank=True,
    )
    performed_at = models.DateTimeField(default=timezone.now)
    reason = models.TextField(blank=True)
    reference = models.CharField(max_length=120, blank=True)

    class Meta:
        ordering = ["-performed_at"]
        indexes = [
            models.Index(fields=["movement_type"]),
            models.Index(fields=["performed_at"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(quantity__gt=0),
                name="stock_movement_quantity_gt_zero",
            ),
        ]

    def __str__(self):
        return f"{self.stock_item} - {self.movement_type} - {self.quantity}"


class InventoryUsageStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    SUBMITTED = "SUBMITTED", "Submitted"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"
    CANCELLED = "CANCELLED", "Cancelled"


class InventoryUsageContext(models.TextChoices):
    DEMONSTRATION = "DEMONSTRATION", "Demonstration"
    SELF_PRACTICE = "SELF_PRACTICE", "Self-practice"
    OSCE = "OSCE", "OSCE"
    GENERAL = "GENERAL", "General"


class InventoryUsage(models.Model):
    usage_context = models.CharField(
        max_length=40,
        choices=InventoryUsageContext.choices,
        default=InventoryUsageContext.GENERAL,
    )
    demonstration_session = models.ForeignKey(
        "labs.DemonstrationSession",
        on_delete=models.SET_NULL,
        related_name="inventory_usages",
        null=True,
        blank=True,
    )
    self_practice_session = models.ForeignKey(
        "labs.SelfPracticeSession",
        on_delete=models.SET_NULL,
        related_name="inventory_usages",
        null=True,
        blank=True,
    )
    osce_exam = models.ForeignKey(
        "assessments.OSCEExam",
        on_delete=models.SET_NULL,
        related_name="inventory_usages",
        null=True,
        blank=True,
    )

    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="submitted_inventory_usages",
        null=True,
        blank=True,
    )
    submitted_at = models.DateTimeField(null=True, blank=True)

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="approved_inventory_usages",
        null=True,
        blank=True,
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    status = models.CharField(
        max_length=40,
        choices=InventoryUsageStatus.choices,
        default=InventoryUsageStatus.DRAFT,
        db_index=True,
    )
    title = models.CharField(max_length=180)
    notes = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["usage_context"]),
            models.Index(fields=["submitted_at"]),
        ]

    def clean(self):
        super().clean()

        selected_contexts = [
            self.demonstration_session_id,
            self.self_practice_session_id,
            self.osce_exam_id,
        ]

        if sum(1 for value in selected_contexts if value) > 1:
            raise ValidationError(
                "Inventory usage can only be linked to one session or exam."
            )

        if self.usage_context == InventoryUsageContext.DEMONSTRATION:
            if not self.demonstration_session_id:
                raise ValidationError(
                    "Demonstration usage must be linked to a demonstration session."
                )

        if self.usage_context == InventoryUsageContext.SELF_PRACTICE:
            if not self.self_practice_session_id:
                raise ValidationError(
                    "Self-practice usage must be linked to a self-practice session."
                )

        if self.usage_context == InventoryUsageContext.OSCE:
            if not self.osce_exam_id:
                raise ValidationError("OSCE usage must be linked to an OSCE exam.")

    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"


class InventoryUsageItem(models.Model):
    usage = models.ForeignKey(
        InventoryUsage,
        on_delete=models.CASCADE,
        related_name="items",
    )
    stock_item = models.ForeignKey(
        StockItem,
        on_delete=models.PROTECT,
        related_name="usage_items",
    )
    quantity_requested = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    quantity_approved = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    remarks = models.TextField(blank=True)

    class Meta:
        ordering = ["stock_item__name"]
        constraints = [
            models.UniqueConstraint(
                fields=["usage", "stock_item"],
                name="unique_stock_item_per_inventory_usage",
            ),
            models.CheckConstraint(
                condition=Q(quantity_requested__gt=0),
                name="usage_item_quantity_requested_gt_zero",
            ),
            models.CheckConstraint(
                condition=Q(quantity_approved__gte=0),
                name="usage_item_quantity_approved_gte_zero",
            ),
        ]

    def clean(self):
        super().clean()

        if self.quantity_approved > self.quantity_requested:
            raise ValidationError(
                "Approved quantity cannot be greater than requested quantity."
            )

    def __str__(self):
        return f"{self.usage} - {self.stock_item} - {self.quantity_requested}"


class LowStockAlertStatus(models.TextChoices):
    OPEN = "OPEN", "Open"
    RESOLVED = "RESOLVED", "Resolved"
    IGNORED = "IGNORED", "Ignored"


class LowStockAlert(models.Model):
    stock_item = models.ForeignKey(
        StockItem,
        on_delete=models.CASCADE,
        related_name="low_stock_alerts",
    )
    current_quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    threshold = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    status = models.CharField(
        max_length=30,
        choices=LowStockAlertStatus.choices,
        default=LowStockAlertStatus.OPEN,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="resolved_low_stock_alerts",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.stock_item} low stock: {self.current_quantity}"