from collections.abc import Collection
from datetime import date, timedelta

from accounts.models import Notification
from django.db import IntegrityError, transaction
from django.utils import timezone

from .models import Booking, Payment
from .ranges import stay_range

PAYMENT_WINDOW = timedelta(hours=24)


class BookingError(Exception):
    """a rule was broken. the `code` is for the frontend and message is for the users"""

    code = "booking_error"

    def __init__(self, message, code=None):
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code


class DateUnavailable(BookingError):
    code = "date_unavailable"


class NotAllowed(BookingError):
    code = "not_allowed"


class InvalidTransition(BookingError):
    code = "invalid_transition"


def _notify(user, kind, message):
    Notification.objects.create(user=user, kind=kind, message=message)


def _locked(booking_id) -> Booking:
    return Booking.objects.select_for_update().select_related("property").get(id=booking_id)


def _move(booking: Booking, allowed_from: Collection[str], to_status: str):
    if booking.status not in allowed_from:
        raise InvalidTransition(f"{booking.status} cannot be changed to {to_status}")
    booking.status = to_status
    return booking


def request_booking(*, guest, check_in: date, check_out: date, guests, property):
    if check_in >= check_out:
        raise BookingError("check in must be before check out", "bad_date")
    if check_in < timezone.localdate():
        raise BookingError("check in cannot be in the past", "bad_date")
    if not property.is_active:
        raise BookingError("the home isn't taking bookings now")
    if property.owner_id == guest.pk:
        raise BookingError("you cannot book your own property")
    if guests < 1:
        raise BookingError("a booking must include at least one guest", "bad_guests")
    if property.max_guests < guests:
        raise BookingError(f"home can only accomodate {property.max_guests}")

    nights = (check_out - check_in).days

    try:
        with transaction.atomic():
            booking = Booking.objects.create(
                guest=guest,
                property=property,
                stay=stay_range(check_in, check_out),
                guests=guests,
                total=nights * property.price_per_night,
            )
    except IntegrityError as exec:
        if "bookings_overlap" in str(exec):
            raise DateUnavailable("those dates were just taken. try another one") from exec
        raise
    _notify(property.owner, "booking_request", f"New request for {property.title}")
    return booking


@transaction.atomic
def approve(booking_id, *, landlord):
    booking = _locked(booking_id)
    if booking.property.owner != landlord:
        raise NotAllowed("only landlord can approve property")
    _move(booking, {Booking.Status.REQUESTED}, Booking.Status.APPROVED)
    booking.approved_at = timezone.now()
    booking.save(update_fields=["status", "approved_at"])
    _notify(
        booking.guest, "booking_approved", f"Your booking for {booking.property.title} was approved"
    )
    return booking


@transaction.atomic
def decline(booking_id, *, landlord):
    booking = _locked(booking_id)
    if booking.property.owner != landlord:
        raise NotAllowed("only landlord can decline")
    _move(
        booking,
        (Booking.Status.APPROVED, Booking.Status.CONFIRMED, Booking.Status.REQUESTED),
        Booking.Status.DECLINED,
    )
    booking.save(update_fields=["status"])
    _notify(
        booking.guest, "booking_declined", f"Your booking for {booking.property.title} was declined"
    )
    return booking


@transaction.atomic
def cancel(booking_id, *, guest):
    booking = _locked(booking_id)
    if booking.guest != guest:
        raise NotAllowed("you can only cancel your own booking")
    _move(
        booking,
        (Booking.Status.REQUESTED, Booking.Status.APPROVED, Booking.Status.CONFIRMED),
        Booking.Status.CANCELED,
    )
    booking.save(update_fields=["status"])
    _notify(
        booking.property.owner,
        "booking_canceled",
        f"A guest canceled their booking for {booking.property.title}",
    )
    return booking


@transaction.atomic
def confirm_payment(booking_id):
    booking = _locked(booking_id)
    if booking.payments.filter(status=Payment.Status.COMPLETED).exists():
        _move(booking, (Booking.Status.APPROVED), Booking.Status.CONFIRMED)
        booking.save(update_fields=["status"])
        _notify(
            booking.guest,
            "payment_confirmed",
            f"Payment for {booking.property.title} was confirmed",
        )
        return booking


@transaction.atomic
def expire(booking_id):
    """System changes booking status when approved to expired after 24 hours without payment"""
    current_time = timezone.now()
    booking = _locked(booking_id)
    expired = (
        booking.approved_at is not None and current_time >= booking.approved_at + PAYMENT_WINDOW
    )

    if expired:
        _move(booking, (Booking.Status.APPROVED), Booking.Status.EXPIRED)
        booking.save(update_fields=["status"])
        _notify(
            booking.guest,
            "booking_expired",
            f"Your booking for {booking.property.title} expired before payment",
        )
        return booking
