import stripe
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import serializers as drf_serializers

from bookings.models import Booking
from .models import Payment, Refund

stripe.api_key = settings.STRIPE_SECRET_KEY


# ---- Serializers (inline for brevity) ----

class PaymentSerializer(drf_serializers.ModelSerializer):
    class Meta:
        model  = Payment
        fields = ["id", "booking", "amount", "currency", "status",
                  "stripe_payment_intent", "stripe_client_secret", "created_at"]
        read_only_fields = fields


class CreatePaymentIntentSerializer(drf_serializers.Serializer):
    booking_id = drf_serializers.IntegerField()


# ---- Views ----

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_payment_intent(request):
    """Create a Stripe PaymentIntent for a booking."""
    serializer = CreatePaymentIntentSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    try:
        booking = Booking.objects.get(
            pk=serializer.validated_data["booking_id"],
            client=request.user,
            status__in=["pending", "confirmed"],
        )
    except Booking.DoesNotExist:
        return Response({"detail": "Booking not found or not yours."}, status=404)

    if hasattr(booking, "payment") and booking.payment.status == Payment.STATUS_SUCCEEDED:
        return Response({"detail": "Booking already paid."}, status=400)

    amount_pence = int(booking.price_paid * 100)  # Stripe uses smallest currency unit

    intent = stripe.PaymentIntent.create(
        amount=amount_pence,
        currency="gbp",
        metadata={"booking_id": booking.id, "user_id": request.user.id},
    )

    payment, _ = Payment.objects.update_or_create(
        booking=booking,
        defaults={
            "user": request.user,
            "amount": booking.price_paid,
            "stripe_payment_intent": intent.id,
            "stripe_client_secret": intent.client_secret,
            "status": Payment.STATUS_PENDING,
        },
    )

    return Response({
        "client_secret": intent.client_secret,
        "payment_id": payment.id,
        "amount": booking.price_paid,
    }, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_payments(request):
    payments = Payment.objects.filter(user=request.user).select_related("booking")
    return Response(PaymentSerializer(payments, many=True).data)


@api_view(["POST"])
@permission_classes([IsAdminUser])
def issue_refund(request, payment_id):
    try:
        payment = Payment.objects.get(pk=payment_id, status=Payment.STATUS_SUCCEEDED)
    except Payment.DoesNotExist:
        return Response({"detail": "Payment not found or not eligible for refund."}, status=404)

    amount_pence = int(payment.amount * 100)

    stripe_refund = stripe.Refund.create(
        payment_intent=payment.stripe_payment_intent,
        amount=amount_pence,
    )

    Refund.objects.create(
        payment=payment,
        amount=payment.amount,
        reason=request.data.get("reason", ""),
        stripe_refund_id=stripe_refund.id,
    )

    payment.status = Payment.STATUS_REFUNDED
    payment.save()

    return Response({"detail": "Refund issued.", "stripe_refund_id": stripe_refund.id})


@csrf_exempt
def stripe_webhook(request):
    """Handle Stripe webhook events to keep payment status in sync."""
    payload    = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    except (ValueError, stripe.error.SignatureVerificationError):
        return HttpResponse(status=400)

    if event["type"] == "payment_intent.succeeded":
        intent = event["data"]["object"]
        try:
            payment = Payment.objects.get(stripe_payment_intent=intent["id"])
            payment.status = Payment.STATUS_SUCCEEDED
            payment.save()
            # Auto-confirm booking
            booking = payment.booking
            if booking.status == Booking.STATUS_PENDING:
                booking.status = Booking.STATUS_CONFIRMED
                booking.save()
        except Payment.DoesNotExist:
            pass

    elif event["type"] == "payment_intent.payment_failed":
        intent = event["data"]["object"]
        try:
            payment = Payment.objects.get(stripe_payment_intent=intent["id"])
            payment.status = Payment.STATUS_FAILED
            payment.save()
        except Payment.DoesNotExist:
            pass

    return HttpResponse(status=200)
