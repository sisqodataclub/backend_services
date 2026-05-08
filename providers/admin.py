from django.contrib import admin
from .models import Provider, WeeklyAvailability, BlockedSlot

class AvailabilityInline(admin.TabularInline):
    model = WeeklyAvailability
    extra = 1

class BlockedSlotInline(admin.TabularInline):
    model = BlockedSlot
    extra = 0

@admin.register(Provider)
class ProviderAdmin(admin.ModelAdmin):
    list_display = ["user", "is_active", "created_at"]
    inlines = [AvailabilityInline, BlockedSlotInline]
