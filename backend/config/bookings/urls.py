from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import BookingViewset

router = DefaultRouter()
router.register("bookings", BookingViewset, basename="booking")

urlpatterns = [
    path("", include(router.urls))
]