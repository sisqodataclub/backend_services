from django.db import models


class Payment(models.Model):
    STATUS_PENDING   = "pending"
    STATUS_SUCCEEDED = "succeeded"
    STATUS_FAILED    = "failed"
    STATUS_REFUNDED  = "refunded"
    STATUS_CHOICES   = [
        (STATUS_PENDING,   "Pending"),
        (STATUS_SUCCEEDED, "Succeeded"),
        (STATUS_FAILED,    "Failed"),
        (STATUS_REFUNDED,  "Refunded"),
    ]

    booking             = models.OneToOneField("bookings.Booking", on_delete=models.PROTECT, related_name="payment")
    user                = models.ForeignKey("core.User", on_delete=models.PROTECT, related_name="payments")
    amount              = models.DecimalField(max_digits=10, decimal_places=2)
    currency            = models.CharField(max_length=3, default="gbp")
    status              = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    stripe_payment_intent = models.CharField(max_length=200, unique=True)
    stripe_client_secret  = models.CharField(max_length=500, blank=True)
    created_at          = models.DateTimeField(auto_now_add=True)
    updated_at          = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Payment #{self.pk} — {self.user.email} — {self.status}"


class Refund(models.Model):
    payment    = models.ForeignKey(Payment, on_delete=models.PROTECT, related_name="refunds")
    amount     = models.DecimalField(max_digits=10, decimal_places=2)
    reason     = models.CharField(max_length=300, blank=True)
    stripe_refund_id = models.CharField(max_length=200, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Refund {self.stripe_refund_id} for Payment #{self.payment_id}"
