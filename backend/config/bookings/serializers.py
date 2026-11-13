from properties.models import Property
from rest_framework import serializers

from .models import Booking, Review


class BookingSerializer(serializers.ModelSerializer):
    property_title = serializers.CharField(read_only=True, source="property.title")
    check_in = serializers.DateField(read_only=True, format="%Y-%m-%d")
    check_out = serializers.DateField(read_only=True, format="%Y-%m-%d")
    nights = serializers.IntegerField(read_only=True)

    class Meta:
        model = Booking
        fields = [
            "id",
            "property",
            "property_title",
            "guests",
            "status",
            "check_in",
            "check_out",
            "nights",
            "total",
            "approved_at",
            "created_at",
        ]
        read_only_fields = fields


class BookingCreateSerializer(serializers.Serializer):
    property = serializers.PrimaryKeyRelatedField(queryset=Property.objects.filter(is_active=True))
    check_in = serializers.DateField(format="%Y-%m-%d")
    check_out = serializers.DateField(format="%Y-%m-%d")
    guests = serializers.IntegerField(min_value=1, default=1)


class ReviewSerializer(serializers.ModelSerializer):
    validate_rating = serializers.IntegerField(min_value=1, max_value=5)

    class Meta:
        model = Review
        fields = ["id", "booking", "comment", "validate_rating", "created_at"]
        read_only_fields = ["id", "created_at"]
