from rest_framework import serializers
from .models import Provider, WeeklyAvailability, BlockedSlot
from core.serializers import UserSerializer
from services.serializers import ServiceSerializer


class WeeklyAvailabilitySerializer(serializers.ModelSerializer):
    day_label = serializers.CharField(source="get_day_of_week_display", read_only=True)

    class Meta:
        model  = WeeklyAvailability
        fields = ["id", "day_of_week", "day_label", "start_time", "end_time", "is_active"]


class BlockedSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model  = BlockedSlot
        fields = ["id", "date", "start_time", "end_time", "reason"]


class ProviderSerializer(serializers.ModelSerializer):
    user        = UserSerializer(read_only=True)
    specialties = ServiceSerializer(many=True, read_only=True)
    specialty_ids = serializers.PrimaryKeyRelatedField(
        many=True, write_only=True, source="specialties",
        queryset=__import__("services.models", fromlist=["Service"]).Service.objects.all()
    )
    availability = WeeklyAvailabilitySerializer(many=True, read_only=True)

    class Meta:
        model  = Provider
        fields = ["id", "user", "bio", "specialties", "specialty_ids", "availability", "is_active", "created_at"]
        read_only_fields = ["id", "created_at"]
