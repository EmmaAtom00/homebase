import uuid

from django.db import models


class Property(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    owner = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="properties")

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    city = models.CharField(max_length=50)
    address = models.CharField(max_length=150)

    price_per_night = models.DecimalField(decimal_places=2, max_digits=9)
    max_guests = models.PositiveSmallIntegerField(default=2)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "properties"
        indexes = [
            models.Index(fields=["city", "price_per_night"]),
            models.Index(fields=["is_active"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(price_per_night__gt=0), name="positive_property_price"
            ),
            models.CheckConstraint(
                condition=models.Q(max_guests__gte=1), name="property_has_room_for_a_guest"
            ),
        ]

    def __str__(self):
        return f"{self.title} {self.city}"


class PropertyPhoto(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="photos")
    image = models.ImageField(upload_to="properties/")
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["position", "id"]

    def __str__(self):
        return f"{self.property_id.title} photo {self.position}"
