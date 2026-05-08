from rest_framework import serializers
from django.utils import timezone
from .models import Booking
from core.serializers import UserSerializer
from services.serializers import ServiceSerializer
from providers.serializers import ProviderSerializer


class BookingSerializer(serializers.ModelSerializer):
    client   = UserSerializer(read_only=True)
    service  = ServiceSerializer(read_only=True)
    provider = ProviderSerializer(read_only=True)

    service_id  = serializers.PrimaryKeyRelatedField(
        queryset=__import__("services.models", fromlist=["Service"]).Service.objects.filter(is_active=True),
        source="service", write_only=True
    )
    provider_id = serializers.PrimaryKeyRelatedField(
        queryset=__import__("providers.models", fromlist=["Provider"]).Provider.objects.filter(is_active=True),
        source="provider", write_only=True
    )

    is_cancellable = serializers.ReadOnlyField()

    class Meta:
        model  = Booking
        fields = [
            "id", "client", "service", "service_id", "provider", "provider_id",
            "start_datetime", "end_datetime", "status",
            "price_paid", "group_size", "client_notes",
            "is_cancellable", "cancelled_at", "cancel_reason",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "client", "status", "price_paid", "cancelled_at", "created_at", "updated_at"]

    def validate(self, data):
        start = data.get("start_datetime")
        end   = data.get("end_datetime")
        if start and end and start >= end:
            raise serializers.ValidationError("end_datetime must be after start_datetime.")
        if start and start < timezone.now():
            raise serializers.ValidationError("Cannot book a slot in the past.")
        # Overlap check
        provider = data.get("provider")
        if provider and start and end:
            overlap = Booking.objects.filter(
                provider=provider,
                status__in=["pending", "confirmed"],
                start_datetime__lt=end,
                end_datetime__gt=start,
            )
            if self.instance:
                overlap = overlap.exclude(pk=self.instance.pk)
            if overlap.exists():
                raise serializers.ValidationError("This time slot is already booked for the provider.")
        return data

    def create(self, validated_data):
        service = validated_data["service"]
        validated_data["price_paid"] = service.price
        return super().create(validated_data)


class CancelBookingSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=300, required=False, default="")
