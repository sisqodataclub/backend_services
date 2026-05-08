from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Category(models.Model):
    name        = models.CharField(max_length=100, unique=True)
    slug        = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    icon        = models.CharField(max_length=50, blank=True)   # e.g. icon class name
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Service(models.Model):
    DURATION_UNIT_CHOICES = [
        ("minutes", "Minutes"),
        ("hours",   "Hours"),
        ("days",    "Days"),
    ]

    category          = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name="services")
    name              = models.CharField(max_length=200)
    slug              = models.SlugField(unique=True)
    short_description = models.CharField(max_length=300)
    description       = models.TextField()
    price             = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    duration          = models.PositiveIntegerField(help_text="Duration value")
    duration_unit     = models.CharField(max_length=10, choices=DURATION_UNIT_CHOICES, default="minutes")
    is_active         = models.BooleanField(default=True)
    is_featured       = models.BooleanField(default=False)
    max_group_size    = models.PositiveIntegerField(default=1, help_text="1 = individual, >1 = group service")
    created_at        = models.DateTimeField(auto_now_add=True)
    updated_at        = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def duration_display(self):
        return f"{self.duration} {self.duration_unit}"

    @property
    def average_rating(self):
        reviews = self.reviews.all()
        if not reviews:
            return None
        return round(sum(r.rating for r in reviews) / len(reviews), 1)


class ServiceImage(models.Model):
    service    = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="images")
    image      = models.ImageField(upload_to="services/")
    alt_text   = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    order      = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"Image for {self.service.name}"


class Review(models.Model):
    service    = models.ForeignKey(Service,  on_delete=models.CASCADE, related_name="reviews")
    user       = models.ForeignKey("core.User", on_delete=models.CASCADE, related_name="reviews")
    booking    = models.OneToOneField("bookings.Booking", on_delete=models.SET_NULL, null=True, blank=True)
    rating     = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment    = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering   = ["-created_at"]
        unique_together = ["service", "user"]   # one review per service per user

    def __str__(self):
        return f"{self.user.email} → {self.service.name} ({self.rating}★)"
