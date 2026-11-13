from datetime import date
from types import SimpleNamespace
from unittest.mock import Mock, patch

from bookings.ranges import stay_range
from django.test import SimpleTestCase

from .filters import PropertyFilter


class PropertyFilterTests(SimpleTestCase):
    def test_availability_filter_uses_timestamp_range(self):
        check_in = date(2026, 12, 20)
        check_out = date(2026, 12, 29)
        queryset = Mock()
        filtered_queryset = Mock()
        queryset.exclude.return_value = filtered_queryset
        busy_properties = Mock()
        busy_properties.values_list.return_value = ["busy-property"]
        filterset = SimpleNamespace(
            form=SimpleNamespace(cleaned_data={"check_in": check_in, "check_out": check_out})
        )

        with patch(
            "properties.filters.Property.objects.filter", return_value=busy_properties
        ) as property_filter:
            result = PropertyFilter.filter_available(filterset, queryset, "check_in", check_in)

        self.assertIs(result, filtered_queryset)
        property_filter.assert_called_once_with(
            bookings__stay__overlap=stay_range(check_in, check_out)
        )
        queryset.exclude.assert_called_once_with(id__in=["busy-property"])
