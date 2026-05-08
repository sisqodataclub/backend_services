from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Category, Service, Review
from .serializers import CategorySerializer, ServiceSerializer, ReviewSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    queryset         = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    lookup_field     = "slug"

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        return [IsAdminUser()]


class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.filter(is_active=True).select_related("category").prefetch_related("images", "reviews")
    serializer_class = ServiceSerializer
    lookup_field     = "slug"
    filter_backends  = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["category__slug", "is_featured", "max_group_size"]
    search_fields    = ["name", "short_description", "description"]
    ordering_fields  = ["price", "created_at", "name"]

    def get_permissions(self):
        if self.action in ["list", "retrieve", "reviews"]:
            return [AllowAny()]
        return [IsAdminUser()]

    @action(detail=True, methods=["get", "post"], permission_classes=[IsAuthenticated])
    def reviews(self, request, slug=None):
        service = self.get_object()
        if request.method == "GET":
            reviews = service.reviews.select_related("user")
            return Response(ReviewSerializer(reviews, many=True).data)
        # POST
        serializer = ReviewSerializer(
            data=request.data,
            context={"request": request, "service": service}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user, service=service)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"], permission_classes=[AllowAny])
    def featured(self, request):
        featured = self.get_queryset().filter(is_featured=True)
        return Response(self.get_serializer(featured, many=True).data)
