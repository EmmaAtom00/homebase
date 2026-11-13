import django_filters
from bookings.ranges import stay_range
from rest_framework.exceptions import ValidationError

from .models import Property


class PropertyFilter(django_filters.FilterSet):
    city = django_filters.CharFilter(field_name="city", lookup_expr="iexact")
    min_price = django_filters.NumberFilter(field_name="price_per_night", lookup_expr="lte")
    max_price = django_filters.NumberFilter(field_name="price_per_night", lookup_expr="gte")
    guests = django_filters.NumberFilter(field_name="max_guests", lookup_expr="gte")
    check_in = django_filters.DateFilter(
        method="filter_available",
        help_text="Check-in date in YYYY-MM-DD format. Example: 2026-12-20.",
    )
    check_out = django_filters.DateFilter(
        method="filter_available",
        help_text="Check-out date in YYYY-MM-DD format. Must be after check-in.",
    )

    def filter_available(self, queryset, name, value):
        if name == "check_in":
            check_in = self.form.cleaned_data.get("check_in")
            check_out = self.form.cleaned_data.get("check_out")

            if not check_out or check_out <= check_in:
                raise ValidationError("Check-out date must be after the Check-in date")

            busy_properties = Property.objects.filter(
                bookings__stay__overlap=stay_range(check_in, check_out)
            ).values_list("id", flat=True)

            queryset = queryset.exclude(id__in=busy_properties)

        return queryset

    class Meta:
        model = Property
        fields = ["city", "min_price", "max_price", "guests", "check_in", "check_out"]
