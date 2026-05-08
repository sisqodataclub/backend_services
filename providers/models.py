from django.db import models


class Provider(models.Model):
    user        = models.OneToOneField("core.User", on_delete=models.CASCADE, related_name="provider_profile")
    bio         = models.TextField(blank=True)
    specialties = models.ManyToManyField("services.Service", blank=True, related_name="providers")
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Provider: {self.user.full_name}"


DAYS_OF_WEEK = [
    (0, "Monday"), (1, "Tuesday"), (2, "Wednesday"),
    (3, "Thursday"), (4, "Friday"), (5, "Saturday"), (6, "Sunday"),
]


class WeeklyAvailability(models.Model):
    """Recurring weekly availability — defines when a provider generally works."""
    provider   = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name="availability")
    day_of_week= models.IntegerField(choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time   = models.TimeField()
    is_active  = models.BooleanField(default=True)

    class Meta:
        ordering = ["day_of_week", "start_time"]
        unique_together = ["provider", "day_of_week", "start_time"]

    def __str__(self):
        return f"{self.provider} — {self.get_day_of_week_display()} {self.start_time}–{self.end_time}"


class BlockedSlot(models.Model):
    """Specific dates/times when a provider is NOT available (holidays, breaks, etc.)."""
    provider   = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name="blocked_slots")
    date       = models.DateField()
    start_time = models.TimeField(null=True, blank=True, help_text="Leave blank to block the full day")
    end_time   = models.TimeField(null=True, blank=True)
    reason     = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["date", "start_time"]

    def __str__(self):
        return f"{self.provider} blocked on {self.date}"
