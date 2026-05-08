from django.contrib import admin
from .models import Booking

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ["id", "client", "service", "provider", "start_datetime", "status", "price_paid"]
    list_filter = ["status"]
    search_fields = ["client__email", "service__name"]
    date_hierarchy = "start_datetime"
