from io import BytesIO

from django.http import FileResponse
from openpyxl import Workbook
from openpyxl.styles import Font

from .services import get_available_quantity


def export_inventory_balances_workbook(stock_items):
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Inventory Balances"

    headers = [
        "Item Code",
        "Item Name",
        "Category",
        "Type",
        "Unit",
        "Available Quantity",
        "Minimum Stock Level",
        "Reorder Level",
        "Low Stock",
    ]

    worksheet.append(headers)

    for cell in worksheet[1]:
        cell.font = Font(bold=True)

    for item in stock_items:
        available_quantity = get_available_quantity(item)

        worksheet.append(
            [
                item.code,
                item.name,
                item.category.name,
                item.get_item_type_display(),
                item.get_unit_display(),
                available_quantity,
                item.minimum_stock_level,
                item.reorder_level,
                "Yes" if available_quantity <= item.minimum_stock_level else "No",
            ]
        )

    for column_cells in worksheet.columns:
        max_length = 0
        column_letter = column_cells[0].column_letter

        for cell in column_cells:
            max_length = max(max_length, len(str(cell.value or "")))

        worksheet.column_dimensions[column_letter].width = min(max_length + 2, 40)

    output = BytesIO()
    workbook.save(output)
    output.seek(0)

    return FileResponse(
        output,
        as_attachment=True,
        filename="inventory-balances.xlsx",
    )


def export_stock_movements_workbook(movements):
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Stock Movements"

    headers = [
        "Date",
        "Item Code",
        "Item Name",
        "Batch",
        "Movement Type",
        "Quantity",
        "Performed By",
        "Reference",
        "Reason",
    ]

    worksheet.append(headers)

    for cell in worksheet[1]:
        cell.font = Font(bold=True)

    for movement in movements:
        worksheet.append(
            [
                movement.performed_at.strftime("%Y-%m-%d %H:%M"),
                movement.stock_item.code,
                movement.stock_item.name,
                movement.stock_batch.batch_number if movement.stock_batch else "",
                movement.get_movement_type_display(),
                movement.quantity,
                str(movement.performed_by or ""),
                movement.reference,
                movement.reason,
            ]
        )

    for column_cells in worksheet.columns:
        max_length = 0
        column_letter = column_cells[0].column_letter

        for cell in column_cells:
            max_length = max(max_length, len(str(cell.value or "")))

        worksheet.column_dimensions[column_letter].width = min(max_length + 2, 45)

    output = BytesIO()
    workbook.save(output)
    output.seek(0)

    return FileResponse(
        output,
        as_attachment=True,
        filename="stock-movements.xlsx",
    )