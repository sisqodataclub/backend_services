from rest_framework import serializers
from .models import Category, Service, ServiceImage, Review
from core.serializers import UserSerializer


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model  = Category
        fields = ["id", "name", "slug", "description", "icon", "is_active"]


class ServiceImageSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ServiceImage
        fields = ["id", "image", "alt_text", "is_primary", "order"]


class ReviewSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model  = Review
        fields = ["id", "user", "rating", "comment", "created_at"]
        read_only_fields = ["id", "user", "created_at"]

    def validate(self, data):
        request = self.context.get("request")
        service = self.context.get("service")
        if service and Review.objects.filter(service=service, user=request.user).exists():
            raise serializers.ValidationError("You have already reviewed this service.")
        return data


class ServiceSerializer(serializers.ModelSerializer):
    category       = CategorySerializer(read_only=True)
    category_id    = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source="category", write_only=True
    )
    images         = ServiceImageSerializer(many=True, read_only=True)
    average_rating = serializers.ReadOnlyField()
    review_count   = serializers.SerializerMethodField()
    duration_display = serializers.ReadOnlyField()

    class Meta:
        model  = Service
        fields = [
            "id", "category", "category_id", "name", "slug",
            "short_description", "description", "price",
            "duration", "duration_unit", "duration_display",
            "is_active", "is_featured", "max_group_size",
            "images", "average_rating", "review_count",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_review_count(self, obj):
        return obj.reviews.count()
