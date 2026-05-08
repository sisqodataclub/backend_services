from django.urls import path
from . import views

urlpatterns = [
    path("create-intent/",             views.create_payment_intent, name="create-payment-intent"),
    path("my/",                         views.my_payments,           name="my-payments"),
    path("<int:payment_id>/refund/",    views.issue_refund,          name="issue-refund"),
    path("webhook/",                    views.stripe_webhook,        name="stripe-webhook"),
]
