from django.contrib import admin
from .models import Payment, Refund

class RefundInline(admin.TabularInline):
    model = Refund
    extra = 0

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "booking", "amount", "currency", "status", "created_at"]
    list_filter = ["status", "currency"]
    inlines = [RefundInline]
