import builtins
import uuid

from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import DateTimeRangeField, RangeOperators
from django.db import models
from properties.models import Property


class Booking(models.Model):
    class Status(models.TextChoices):
        REQUESTED = "requested", "Requested"
        APPROVED = "approved", "Approved"
        DECLINED = "declined", "Declined"
        CONFIRMED = "confirmed", "Confirmed"
        CANCELED = "canceled", "Canceled"
        EXPIRED = "expired", "Expired"
        COMPLETED = "completed", "Completed"

    # List of status that locks the booking and prevent overlapping bookings
    ACTIVE = [Status.APPROVED, Status.COMPLETED, Status.CONFIRMED, Status.REQUESTED]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    property = models.ForeignKey(Property, on_delete=models.PROTECT, related_name="bookings")
    guest = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="bookings")

    stay = DateTimeRangeField(help_text="[check_in, check_out): the check-out day is not a night")
    guests = models.PositiveSmallIntegerField(default=1)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.REQUESTED)
    total = models.DecimalField(max_digits=9, decimal_places=2, default=0.00)

    approved_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status", "approved_at"])]
        constraints = [
            ExclusionConstraint(
                expressions=[("stay", RangeOperators.OVERLAPS), ("property", RangeOperators.EQUAL)],
                condition=models.Q(status__in=["approved", "requested", "completed", "confirmed"]),
                name="bookings_overlap",
            ),
            models.CheckConstraint(
                condition=models.Q(guests__gt=0), name="booking_guests_positive"
            ),
            models.CheckConstraint(
                condition=models.Q(stay__lower_inf=False)
                & models.Q(stay__upper_inf=False)
                & models.Q(stay__isempty=False),
                name="valid_booking_date",
            ),
        ]

    def __str__(self):
        return f"{self.property.title}: {self.check_in:%Y-%m-%d} to {self.check_out:%Y-%m-%d}"

    @builtins.property
    def check_in(self):
        return self.stay.lower

    @builtins.property
    def check_out(self):
        return self.stay.upper

    @builtins.property
    def nights(self):
        return (self.check_out - self.check_in).days


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    booking = models.ForeignKey(Booking, on_delete=models.PROTECT, related_name="payments")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    reference = models.JSONField(default=dict, unique=True)

    def __str__(self):
        return f"{self.booking} payments"


class Review(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.PROTECT, related_name="reviews")
    comment = models.CharField(max_length=255, blank=True)
    rating = models.PositiveSmallIntegerField()

    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(rating__gte=1) & models.Q(rating__lte=5),
                name="review_rating_1_to_5",
            )
        ]

    def __str__(self):
        return f"Review for Booking {self.booking} - Rating: {self.rating}/5"
