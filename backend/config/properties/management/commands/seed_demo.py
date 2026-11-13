from decimal import Decimal

from accounts.models import User
from django.core.management import BaseCommand

from properties.models import Property

PASSWORD = "lagos_sunset_2026"
HOMES = [
    {
        "owner_email": "ada@homebase.test",
        "title": "Bright Apartment near the Beach",
        "description": "A calm, sunlit apartment with an easy trip to the beach.",
        "city": "Lagos",
        "address": "12 Admiralty Way, Lekki Phase 1",
        "price_per_night": Decimal("125.00"),
        "max_guests": 3,
    },
    {
        "owner_email": "ada@homebase.test",
        "title": "Cozy Ikoyi Garden Flat",
        "description": "A comfortable garden-level flat in a quiet Ikoyi neighborhood.",
        "city": "Lagos",
        "address": "8 Alexander Road, Ikoyi",
        "price_per_night": Decimal("180.00"),
        "max_guests": 2,
    },
    {
        "owner_email": "kemi@homebase.test",
        "title": "Family Home in Ikeja",
        "description": "A spacious home with room for the whole family.",
        "city": "Lagos",
        "address": "24 Allen Avenue, Ikeja",
        "price_per_night": Decimal("150.00"),
        "max_guests": 6,
    },
    {
        "owner_email": "kemi@homebase.test",
        "title": "Modern Lekki Studio",
        "description": "A well-equipped studio suited to short city stays.",
        "city": "Lagos",
        "address": "5 Freedom Way, Lekki Phase 1",
        "price_per_night": Decimal("95.00"),
        "max_guests": 2,
    },
]


class Command(BaseCommand):
    def handle(self, *args, **options):
        self.person("ada@homebase.test", User.Role.LANDLORD, "ada", "lovelace")
        self.person("john@homebase.test", User.Role.GUEST, "john", "doe")
        self.person("kemi@homebase.test", User.Role.LANDLORD, "kemi", "adeniyi")

        owners = {
            user.email: user
            for user in User.objects.filter(email__in={home["owner_email"] for home in HOMES})
        }
        created_count = 0
        for home in HOMES:
            owner = owners[home["owner_email"]]
            property_data = {key: value for key, value in home.items() if key != "owner_email"}
            _, created = Property.objects.get_or_create(
                owner=owner,
                title=property_data["title"],
                address=property_data["address"],
                defaults=property_data,
            )
            created_count += created

        self.stdout.write(
            self.style.SUCCESS(
                f"Demo data ready: {len(HOMES)} homes available; {created_count} newly created."
            )
        )

    def person(self, email, role, first_name, last_name):
        normalize_email = email.lower()
        user, created = User.objects.get_or_create(
            email=normalize_email,
            defaults={
                "first_name": first_name,
                "last_name": last_name,
                "role": role,
                "is_verified": True,
            },
        )
        user.first_name = first_name
        user.last_name = last_name
        user.role = role
        user.is_verified = True

        if created:
            user.set_password(PASSWORD)
        user.save()
        return user
