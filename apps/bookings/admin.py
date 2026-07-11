from django.contrib import admin
from .models import LabBooking 

@admin.register(LabBooking)
class LabBookingAdmin(admin.ModelAdmin):
    search_fields = ['title', 'requested_by__username', 'lab_room__name']
    list_display = ['title', 'lab_room', 'start_at', 'status', 'requested_by']
    list_filter = ['status', 'booking_type']