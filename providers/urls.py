from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register("availability", views.WeeklyAvailabilityViewSet, basename="availability")
router.register("blocked",      views.BlockedSlotViewSet,        basename="blocked")
router.register("",             views.ProviderViewSet,           basename="provider")

urlpatterns = [path("", include(router.urls))]
