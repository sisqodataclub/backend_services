from datetime import date, datetime, timedelta
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.response import Response
from .models import Provider, WeeklyAvailability, BlockedSlot
from .serializers import ProviderSerializer, WeeklyAvailabilitySerializer, BlockedSlotSerializer
from bookings.models import Booking


class ProviderViewSet(viewsets.ModelViewSet):
    queryset         = Provider.objects.filter(is_active=True).select_related("user").prefetch_related("specialties", "availability")
    serializer_class = ProviderSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve", "available_slots"]:
            return [AllowAny()]
        return [IsAdminUser()]

    @action(detail=True, methods=["get"], permission_classes=[AllowAny])
    def available_slots(self, request, pk=None):
        """
        Return available 30-min slots for a provider on a given date.
        Query params: ?date=YYYY-MM-DD&duration=60  (duration in minutes)
        """
        provider = self.get_object()
        target_date_str = request.query_params.get("date")
        duration = int(request.query_params.get("duration", 60))

        if not target_date_str:
            return Response({"detail": "?date=YYYY-MM-DD is required."}, status=400)

        try:
            target_date = date.fromisoformat(target_date_str)
        except ValueError:
            return Response({"detail": "Invalid date format."}, status=400)

        day_of_week = target_date.weekday()

        # Get provider's working windows for that day
        windows = provider.availability.filter(day_of_week=day_of_week, is_active=True)
        if not windows.exists():
            return Response({"date": target_date_str, "slots": []})

        # Existing bookings on that day
        booked = Booking.objects.filter(
            provider=provider,
            start_datetime__date=target_date,
            status__in=["pending", "confirmed"],
        ).values_list("start_datetime", "end_datetime")

        # Full-day blocked slots
        blocked_full = provider.blocked_slots.filter(date=target_date, start_time__isnull=True)
        if blocked_full.exists():
            return Response({"date": target_date_str, "slots": []})

        # Partial blocked slots
        blocked_partial = list(provider.blocked_slots.filter(date=target_date, start_time__isnull=False))

        slots = []
        slot_delta = timedelta(minutes=duration)

        for window in windows:
            cursor = datetime.combine(target_date, window.start_time)
            end_window = datetime.combine(target_date, window.end_time)

            while cursor + slot_delta <= end_window:
                slot_end = cursor + slot_delta
                # Check against bookings
                overlap = any(
                    not (slot_end <= b_start or cursor >= b_end)
                    for b_start, b_end in booked
                )
                # Check against blocked partials
                blocked = any(
                    not (slot_end <= datetime.combine(target_date, bl.start_time) or
                         cursor >= datetime.combine(target_date, bl.end_time))
                    for bl in blocked_partial
                )
                if not overlap and not blocked:
                    slots.append({
                        "start": cursor.strftime("%H:%M"),
                        "end":   slot_end.strftime("%H:%M"),
                    })
                cursor += timedelta(minutes=30)   # move in 30-min increments

        return Response({"date": target_date_str, "slots": slots})


class WeeklyAvailabilityViewSet(viewsets.ModelViewSet):
    serializer_class = WeeklyAvailabilitySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return WeeklyAvailability.objects.filter(provider__user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(provider=self.request.user.provider_profile)


class BlockedSlotViewSet(viewsets.ModelViewSet):
    serializer_class = BlockedSlotSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return BlockedSlot.objects.filter(provider__user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(provider=self.request.user.provider_profile)
