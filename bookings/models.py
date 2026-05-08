from django.db import models


class Booking(models.Model):
    STATUS_PENDING   = "pending"
    STATUS_CONFIRMED = "confirmed"
    STATUS_CANCELLED = "cancelled"
    STATUS_COMPLETED = "completed"
    STATUS_NO_SHOW   = "no_show"
    STATUS_CHOICES   = [
        (STATUS_PENDING,   "Pending"),
        (STATUS_CONFIRMED, "Confirmed"),
        (STATUS_CANCELLED, "Cancelled"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_NO_SHOW,   "No Show"),
    ]

    client         = models.ForeignKey("core.User",    on_delete=models.PROTECT, related_name="bookings_as_client")
    provider       = models.ForeignKey("providers.Provider", on_delete=models.PROTECT, related_name="bookings")
    service        = models.ForeignKey("services.Service",   on_delete=models.PROTECT, related_name="bookings")
    start_datetime = models.DateTimeField()
    end_datetime   = models.DateTimeField()
    status         = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    price_paid     = models.DecimalField(max_digits=10, decimal_places=2)
    group_size     = models.PositiveIntegerField(default=1)
    client_notes   = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True)   # provider/admin only
    cancelled_at   = models.DateTimeField(null=True, blank=True)
    cancel_reason  = models.CharField(max_length=300, blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-start_datetime"]

    def __str__(self):
        return f"Booking #{self.pk} — {self.client.email} with {self.provider}"

    @property
    def is_cancellable(self):
        from django.utils import timezone
        from datetime import timedelta
        # Allow cancel up to 24 h before appointment
        return self.status in (self.STATUS_PENDING, self.STATUS_CONFIRMED) and \
               self.start_datetime > timezone.now() + timedelta(hours=24)
