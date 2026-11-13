from bookings.models import Booking
from bookings.ranges import stay_range

from .models import Property


def search_properties(
    *, guests=None, min_price=None, max_price=None, check_in=None, check_out=None, city=None
):
    qs = Property.objects.filter(is_active=True)

    if city:
        qs = qs.filter(city__iexact=city.strip())

    if guests:
        qs = qs.filter(guests__gte=guests)

    if min_price:
        qs = qs.filter(price_per_night__gte=min_price)

    if max_price:
        qs = qs.filter(price_per_night__lte=max_price)

    if check_in and check_out:
        busy = Booking.objects.filter(
            stay__overlap=stay_range(check_in, check_out), status__in=Booking.ACTIVE
        ).values("property")

        qs = qs.exclude(pk__in=busy)

    return qs
