from accounts.permissions import IsLandLordOrReadOnly, IsOwnerOrReadOnly, IsVerified
from django.db.models import Avg, Count
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .filters import PropertyFilter
from .models import Property
from .serializers import PropertyListSerializer, PropertyViewSerializer, PropertyWriteSerializer


def with_rating(obj):
    return obj.select_related("owner").annotate(
        rating=Avg("bookings__reviews__rating"), review_count=Count("bookings__reviews")
    )


@extend_schema(tags=["property"])
class PropertyViewset(viewsets.ModelViewSet):
    permission_classes = [AllowAny]

    filterset_class = PropertyFilter
    search_field = ["city", "title", "description", "address"]
    ordering_field = ["price_per_night", "created_at", "title"]
    ordering = ["-created_at"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Property.objects.none()

        if self.action == "list":
            return with_rating(Property.objects.filter(is_active=True))
        if self.action == "retrieve":
            return with_rating(Property.objects.filter(is_active=True).prefetch_related("photos"))
        return with_rating(Property.objects.filter(owner=self.request.user))

    def get_serializer_class(self):
        if self.action == "list":
            return PropertyListSerializer
        if self.action == "retrieve":
            return PropertyViewSerializer
        return PropertyWriteSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        return [IsVerified(), IsLandLordOrReadOnly(), IsOwnerOrReadOnly()]

    def perform_create(self, serializer):
        return serializer.save(owner=self.request.user)

    @action(detail=False, methods=["get"])
    def mine(self, request):
        properties = Property.objects.filter(owner=request.user)
        serializer = self.get_serializer(properties, many=True)
        return Response(serializer.data)
