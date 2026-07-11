from django.contrib import admin
from .models import LabRoom, DemonstrationSession, DemonstrationProcedure


@admin.register(LabRoom)
class LabRoomAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "location", "capacity", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["code", "name", "location"]


@admin.register(DemonstrationSession)
class DemonstrationSessionAdmin(admin.ModelAdmin):
    list_display = ["topic", "module_offering", "lecturer", "status", "booking"]
    list_filter = ["status", "module_offering__academic_year", "module_offering__semester"]

    search_fields = [
        "topic", 
        "description", 
        "module_offering__module__title", 
        "module_offering__module__code"
    ]


@admin.register(DemonstrationProcedure)
class DemonstrationProcedureAdmin(admin.ModelAdmin):
    list_display = ["demonstration_session", "procedure"]
    search_fields = [
        "demonstration_session__topic", 
        "procedure__title", 
        "procedure__code"
    ]