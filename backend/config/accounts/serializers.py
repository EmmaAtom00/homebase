from rest_framework import serializers

from .models import Notification


class HealthSerializer(serializers.Serializer):
    status = serializers.CharField()
    message = serializers.CharField()


class NotifcationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "kind", "message", "is_read", "created_at"]
        read_only_fields = fields
