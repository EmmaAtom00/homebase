from rest_framework import serializers

from .models import Property, PropertyPhoto


class PropertyPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyPhoto
        fields = ["id", "image", "position"]


class PropertyListSerializer(serializers.ModelSerializer):
    host = serializers.CharField(source="owner.first_name", read_only=True)
    rating = serializers.FloatField(read_only=True, allow_null=True)
    reviews_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Property
        fields = [
            "id",
            "host",
            "title",
            "description",
            "city",
            "address",
            "price_per_night",
            "max_guests",
            "rating",
            "reviews_count",
        ]


class PropertyViewSerializer(PropertyListSerializer):
    images = PropertyPhotoSerializer(source="photos", many=True, read_only=True)

    class Meta:
        model = Property
        fields = PropertyListSerializer.Meta.fields + [
            "images",
        ]


class PropertyWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Property
        fields = ["id", "title", "description", "address", "city", "max_guests", "created_at"]
        read_only_fields = ["id", "created_at"]
