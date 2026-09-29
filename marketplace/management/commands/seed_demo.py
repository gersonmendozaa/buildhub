from datetime import date

from django.core.management.base import BaseCommand
from django.utils import timezone

from marketplace.models import Category, County, Project, User, VendorProfile


class Command(BaseCommand):
    help = "Create local demo users, vendors, and projects"

    def handle(self, *args, **options):
        counties = {}
        for name in [
            "San Francisco",
            "San Mateo",
            "Santa Clara",
            "Alameda",
            "Contra Costa",
            "Marin",
        ]:
            slug = name.lower().replace(" ", "-")
            counties[name], _ = County.objects.get_or_create(name=name, defaults={"slug": slug})

        categories = {}
        for name in [
            "General contracting",
            "Kitchen remodeling",
            "Bathroom remodeling",
            "Electrical",
            "Roofing",
            "Landscaping",
        ]:
            slug = name.lower().replace(" ", "-")
            categories[name], _ = Category.objects.get_or_create(name=name, defaults={"slug": slug})

        vendor_user, created = User.objects.get_or_create(
            username="vendor_demo",
            defaults={"email": "vendor@example.com", "role": User.Role.VENDOR},
        )
        if created:
            vendor_user.set_password("demo-password-123")
            vendor_user.save()
        vendor, _ = VendorProfile.objects.get_or_create(
            user=vendor_user,
            defaults={
                "business_name": "Golden Gate Renovation",
                "description": (
                    "Residential remodeling across the Peninsula, with a focus on practical "
                    "design and clear project communication."
                ),
                "license_number": "1029384",
                "license_state": VendorProfile.LicenseState.VERIFIED,
                "license_checked_at": timezone.now(),
                "license_classifications": "B, C-10",
                "score": 82.4,
                "is_published": True,
            },
        )
        vendor.categories.set([categories["Kitchen remodeling"], categories["Bathroom remodeling"]])
        vendor.service_counties.set([counties["San Mateo"], counties["Santa Clara"]])

        homeowner, created = User.objects.get_or_create(
            username="homeowner_demo",
            defaults={"email": "homeowner@example.com", "role": User.Role.HOMEOWNER},
        )
        if created:
            homeowner.set_password("demo-password-123")
            homeowner.save()

        Project.objects.get_or_create(
            vendor=vendor,
            title="Warm modern kitchen",
            defaults={
                "category": categories["Kitchen remodeling"],
                "description": (
                    "Full cabinet, countertop, lighting, and flooring renovation for a 1960s home."
                ),
                "city": "San Mateo",
                "county": counties["San Mateo"],
                "started_on": date(2026, 2, 3),
                "completed_on": date(2026, 4, 18),
                "homeowner_email": "past-client@example.com",
                "status": Project.Status.CONFIRMED,
            },
        )
        Project.objects.get_or_create(
            vendor=vendor,
            title="Primary bathroom refresh",
            defaults={
                "category": categories["Bathroom remodeling"],
                "description": "Walk-in shower, tile, vanity, and accessibility upgrades.",
                "city": "Redwood City",
                "county": counties["San Mateo"],
                "started_on": date(2026, 6, 8),
                "completed_on": date(2026, 7, 17),
                "homeowner_email": homeowner.email,
                "status": Project.Status.PENDING,
            },
        )

        self.stdout.write(self.style.SUCCESS("Demo data ready."))
        self.stdout.write("Vendor: vendor_demo / demo-password-123")
        self.stdout.write("Homeowner: homeowner_demo / demo-password-123")
