from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import NotificationViewset

router = DefaultRouter()
router.register("notifications", NotificationViewset, basename="notification")

urlpatterns = [
    path("", include(router.urls)),
]
