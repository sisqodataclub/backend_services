from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Booking
from .serializers import BookingSerializer, CancelBookingSerializer


class BookingViewSet(viewsets.ModelViewSet):
    serializer_class   = BookingSerializer
    permission_classes = [IsAuthenticated]
    http_method_names  = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        user = self.request.user
        if user.role == "admin":
            return Booking.objects.all().select_related("client", "provider__user", "service")
        if user.role == "provider":
            return Booking.objects.filter(provider__user=user).select_related("client", "service")
        # client
        return Booking.objects.filter(client=user).select_related("provider__user", "service")

    def perform_create(self, serializer):
        serializer.save(client=self.request.user)

    def get_permissions(self):
        return [IsAuthenticated()]

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        booking = self.get_object()
        if request.user.role not in ("provider", "admin"):
            return Response({"detail": "Only providers or admins can confirm."}, status=403)
        if booking.status != Booking.STATUS_PENDING:
            return Response({"detail": "Only pending bookings can be confirmed."}, status=400)
        booking.status = Booking.STATUS_CONFIRMED
        booking.save()
        return Response(BookingSerializer(booking).data)

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        booking = self.get_object()
        if request.user.role not in ("provider", "admin"):
            return Response({"detail": "Only providers or admins can mark as complete."}, status=403)
        if booking.status != Booking.STATUS_CONFIRMED:
            return Response({"detail": "Only confirmed bookings can be completed."}, status=400)
        booking.status = Booking.STATUS_COMPLETED
        booking.save()
        return Response(BookingSerializer(booking).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        booking = self.get_object()
        if not booking.is_cancellable:
            return Response({"detail": "This booking cannot be cancelled."}, status=400)
        serializer = CancelBookingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        booking.status       = Booking.STATUS_CANCELLED
        booking.cancelled_at = timezone.now()
        booking.cancel_reason = serializer.validated_data.get("reason", "")
        booking.save()
        return Response(BookingSerializer(booking).data)

    @action(detail=False, methods=["get"])
    def upcoming(self, request):
        qs = self.get_queryset().filter(
            start_datetime__gte=timezone.now(),
            status__in=["pending", "confirmed"],
        )
        return Response(BookingSerializer(qs, many=True).data)

    @action(detail=False, methods=["get"])
    def history(self, request):
        qs = self.get_queryset().filter(
            status__in=["completed", "cancelled", "no_show"],
        )
        return Response(BookingSerializer(qs, many=True).data)
