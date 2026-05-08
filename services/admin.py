from django.contrib import admin
from .models import Category, Service, ServiceImage, Review

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "is_active"]
    prepopulated_fields = {"slug": ("name",)}

class ServiceImageInline(admin.TabularInline):
    model = ServiceImage
    extra = 1

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "price", "duration_display", "is_active", "is_featured"]
    list_filter = ["category", "is_active", "is_featured"]
    search_fields = ["name", "description"]
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ServiceImageInline]

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ["service", "user", "rating", "created_at"]
    list_filter = ["rating"]
