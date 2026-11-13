from django.db import connection
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification
from .serializers import HealthSerializer, NotifcationSerializer


class Health(APIView):
    serializer_class = HealthSerializer
    permission_classes = [permissions.AllowAny]

    @extend_schema(request=None, responses={200: HealthSerializer, 500: HealthSerializer})
    def get(self, request):
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            if not result or result[0] != 1:
                return Response(
                    {"detail": "could not process database connection"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            return Response(status=status.HTTP_200_OK)


# @api_view(["GET"])
# @permission_classes([permissions.AllowAny])
# @extend_schema(
#     request=None,
#     responses={
#         200: HealthSerializer,
#         500: HealthSerializer
#     }
# )
# def health(request):
#     with connection.cursor() as cursor:
#         cursor.execute("SELECT 1")
#     return Response({"status": "ok"})


@extend_schema(tags=["notification"])
class NotificationViewset(mixins.ListModelMixin, viewsets.GenericViewSet):
    """API endpoint that allows users to view their notifications"""

    serializer_class = NotifcationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Notification.objects.none()

        return Notification.objects.filter(user=self.request.user).order_by("-created_at")

    @extend_schema(request=None)
    @action(detail=False, methods=["POST"])
    def mark_all_read(self, request):
        """Mark all notification as read for the authenticated user"""
        updated_count = Notification.objects.filter(user=request.user, is_read=False).update(
            is_read=True
        )
        return Response({"detail": f"{updated_count} notification marked as read"})
