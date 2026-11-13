from contextlib import nullcontext
from datetime import timedelta
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock, patch
from uuid import uuid4

from django.test import SimpleTestCase
from django.utils import timezone

from . import services
from .models import Booking
from .ranges import stay_range


class RequestBookingTests(SimpleTestCase):
    def setUp(self):
        self.guest = SimpleNamespace(pk=uuid4())
        self.check_in = timezone.localdate() + timedelta(days=1)
        self.check_out = self.check_in + timedelta(days=3)
        self.property = SimpleNamespace(
            owner_id=uuid4(),
            owner=SimpleNamespace(),
            is_active=True,
            max_guests=4,
            price_per_night=Decimal("125.00"),
            title="Home",
        )

    def test_creates_timestamp_range_booking_with_requested_default(self):
        created_booking = object()
        with (
            patch.object(services.transaction, "atomic", return_value=nullcontext()),
            patch.object(Booking.objects, "create", return_value=created_booking) as create,
            patch.object(services, "_notify") as notify,
        ):
            result = services.request_booking(
                guest=self.guest,
                check_in=self.check_in,
                check_out=self.check_out,
                guests=2,
                property=self.property,
            )

        self.assertIs(result, created_booking)
        create.assert_called_once_with(
            guest=self.guest,
            property=self.property,
            stay=stay_range(self.check_in, self.check_out),
            guests=2,
            total=Decimal("375.00"),
        )
        self.assertEqual(Booking._meta.get_field("status").get_default(), Booking.Status.REQUESTED)
        notify.assert_called_once_with(
            self.property.owner, "booking_request", "New request for Home"
        )

    def test_stay_range_uses_utc_midnight_and_excludes_checkout(self):
        stay = stay_range(self.check_in, self.check_out)

        self.assertEqual(stay.lower.date(), self.check_in)
        self.assertEqual(stay.upper.date(), self.check_out)
        self.assertEqual(stay.lower.utcoffset(), timedelta(0))
        self.assertEqual(stay.upper.utcoffset(), timedelta(0))
        self.assertEqual(stay.bounds, "[)")

    def test_guest_cannot_book_own_property(self):
        self.property.owner_id = self.guest.pk

        with self.assertRaisesRegex(services.BookingError, "cannot book your own property"):
            services.request_booking(
                guest=self.guest,
                check_in=self.check_in,
                check_out=self.check_out,
                guests=2,
                property=self.property,
            )

    def test_rejects_non_positive_guest_count(self):
        with self.assertRaisesRegex(services.BookingError, "at least one guest"):
            services.request_booking(
                guest=self.guest,
                check_in=self.check_in,
                check_out=self.check_out,
                guests=0,
                property=self.property,
            )


class ApproveBookingTests(SimpleTestCase):
    def test_approval_moves_requested_booking_to_approved(self):
        landlord = object()
        guest = object()
        booking = SimpleNamespace(
            property=SimpleNamespace(owner=landlord, title="Home"),
            guest=guest,
            status=Booking.Status.REQUESTED,
            save=Mock(),
        )
        with (
            patch.object(services, "_locked", return_value=booking),
            patch.object(services, "_notify") as notify,
        ):
            result = services.approve.__wrapped__(uuid4(), landlord=landlord)

        self.assertIs(result, booking)
        self.assertEqual(booking.status, Booking.Status.APPROVED)
        self.assertIsNotNone(booking.approved_at)
        booking.save.assert_called_once_with(update_fields=["status", "approved_at"])
        notify.assert_called_once_with(
            guest,
            "booking_approved",
            "Your booking for Home was approved",
        )


class CancelBookingTests(SimpleTestCase):
    def test_cancel_allows_guest_to_cancel_active_booking(self):
        guest = object()
        owner = object()
        booking = SimpleNamespace(
            guest=guest,
            property=SimpleNamespace(owner=owner, title="Home"),
            status=Booking.Status.REQUESTED,
            save=Mock(),
        )
        with (
            patch.object(services, "_locked", return_value=booking),
            patch.object(services, "_notify") as notify,
        ):
            result = services.cancel.__wrapped__(uuid4(), user=guest)

        self.assertIs(result, booking)
        self.assertEqual(booking.status, Booking.Status.CANCELED)
        booking.save.assert_called_once_with(update_fields=["status"])
        notify.assert_called_once_with(
            owner,
            "booking_canceled",
            "A guest canceled their booking for Home",
        )


class ConfirmPaymentTests(SimpleTestCase):
    def test_confirm_payment_marks_booking_confirmed_when_completed_payment_exists(self):
        guest = object()
        booking = SimpleNamespace(
            guest=guest,
            property=SimpleNamespace(title="Home"),
            status=Booking.Status.APPROVED,
            payments=Mock(),
            save=Mock(),
        )
        booking.payments.filter.return_value.exists.return_value = True

        with (
            patch.object(services, "_locked", return_value=booking),
            patch.object(services, "_notify") as notify,
        ):
            result = services.confirm_payment.__wrapped__(uuid4())

        self.assertIs(result, booking)
        self.assertEqual(booking.status, Booking.Status.CONFIRMED)
        booking.payments.filter.assert_called_once_with(status=services.Payment.Status.COMPLETED)
        booking.save.assert_called_once_with(update_fields=["status"])
        notify.assert_called_once_with(
            guest,
            "payment_confirmed",
            "Payment for Home was confirmed",
        )
