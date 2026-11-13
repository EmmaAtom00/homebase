from django.db.models import Q
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.exceptions import APIException, PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from . import services
from .models import Booking
from .serializers import BookingCreateSerializer, BookingSerializer, ReviewSerializer


class Conflict(APIException):
    status_code = 409
    default_detail = "This change conflicts with the booking's current state."
    default_code = "conflict"


def as_http_error(exec: services.BookingError):
    body = {"detail": exec.message, "code": exec.code}
    if isinstance(exec, services.NotAllowed):
        return PermissionDenied(body)
    if isinstance(exec, (services.DateUnavailable, services.InvalidTransition)):
        return Conflict(body)
    return ValidationError(body)


@extend_schema(tags=["booking"])
class BookingViewset(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, GenericViewSet
):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Booking.objects.none()

        return Booking.objects.select_related("property", "guest").filter(
            Q(guest=self.request.user) | Q(owner=self.request.user)
        )

    def get_serializer_class(self):
        if self.action == "create":
            return BookingCreateSerializer
        return BookingSerializer

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            booking = services.request_booking(**serializer.validated_data, guest=request.user)
        except services.BookingError as e:
            raise as_http_error(e) from e

        return Response(BookingSerializer(booking).data, status=status.HTTP_201_CREATED)

    def _run(self, fn, **who):
        booking = self.get_object()

        try:
            booking = fn(booking.pk, **who)
        except services.BookingError as e:
            raise as_http_error(e) from e
        return Response(BookingSerializer(booking).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["POST"])
    def approve(self, request, pk=None):
        return self._run(services.approve, landlord=request.user)

    @action(detail=True, methods=["POST"])
    def cancel(self, request, pk=None):
        return self._run(services.cancel, guest=request.user)

    @action(detail=True, methods=["POST"])
    def confirm_payment(self, request, pk=None):
        return self._run(services.confirm_payment, landlord=request.user)

    @action(detail=True, methods=["POST"])
    def review(self, request, pk=None):
        booking = self.get_object()

        if booking.guest != request.user:
            raise PermissionDenied("You do not have access to review this property")

        if booking.status != Booking.Status.COMPLETED:
            raise Conflict("only completed bookings can be reviewed")

        if booking.review.exists():
            raise Conflict("this booking has already been reviewed")

        serializer = ReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save(
            booking=booking,
            rating=serializer.validated_data["validate_rating"],
            **serializer.validated_data,
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)
