import csv
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from marketplace.models import Category, County, Project, User, VendorProfile

REQUIRED_COLUMNS = {
    "vendor_username",
    "vendor_email",
    "business_name",
    "license_number",
    "license_state",
    "license_classifications",
    "categories",
    "service_counties",
    "score",
    "is_published",
    "project_title",
    "project_category",
    "project_description",
    "city",
    "county",
    "started_on",
    "completed_on",
    "homeowner_username",
    "homeowner_email",
    "project_status",
}


class Command(BaseCommand):
    help = "Import synthetic marketplace test records from the BuildHub CSV format"

    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=Path)
        parser.add_argument(
            "--test-password",
            default="csv-test-password-123",
            help="Password assigned only to newly created synthetic accounts.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        path = options["csv_path"]
        if not path.is_file():
            raise CommandError(f"CSV file not found: {path}")

        with path.open(encoding="utf-8", newline="") as csv_file:
            reader = csv.DictReader(csv_file)
            missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
            if missing:
                raise CommandError(f"Missing required columns: {', '.join(sorted(missing))}")
            rows = list(reader)

        vendor_ids = set()
        homeowner_ids = set()
        project_ids = set()
        for row_number, row in enumerate(rows, start=2):
            try:
                vendor, homeowner, project = self._import_row(row, options["test_password"])
            except (ValueError, InvalidOperation) as error:
                raise CommandError(f"Invalid data on CSV row {row_number}: {error}") from error
            vendor_ids.add(vendor.pk)
            homeowner_ids.add(homeowner.pk)
            project_ids.add(project.pk)

        self.stdout.write(
            self.style.SUCCESS(
                f"Imported {len(project_ids)} projects for {len(vendor_ids)} vendors "
                f"and {len(homeowner_ids)} homeowners."
            )
        )
        self.stdout.write("New synthetic accounts use the password supplied by --test-password.")

    def _import_row(self, row, test_password):
        license_states = {choice for choice, _ in VendorProfile.LicenseState.choices}
        project_statuses = {choice for choice, _ in Project.Status.choices}
        if row["license_state"] not in license_states:
            raise ValueError(f"unknown license_state {row['license_state']!r}")
        if row["project_status"] not in project_statuses:
            raise ValueError(f"unknown project_status {row['project_status']!r}")
        if row["is_published"].lower() not in {"true", "false"}:
            raise ValueError("is_published must be true or false")

        vendor_user, created = User.objects.get_or_create(
            username=row["vendor_username"],
            defaults={"email": row["vendor_email"], "role": User.Role.VENDOR},
        )
        if created:
            vendor_user.set_password(test_password)
            vendor_user.save()

        vendor, _ = VendorProfile.objects.update_or_create(
            user=vendor_user,
            defaults={
                "business_name": row["business_name"],
                "license_number": row["license_number"],
                "license_state": row["license_state"],
                "license_classifications": row["license_classifications"],
                "score": Decimal(row["score"]),
                "is_published": row["is_published"].lower() == "true",
            },
        )

        categories = [
            Category.objects.get_or_create(name=name, defaults={"slug": self._slug(name)})[0]
            for name in self._split(row["categories"])
        ]
        service_counties = [
            County.objects.get_or_create(
                name=name, defaults={"slug": self._slug(name), "launch_enabled": True}
            )[0]
            for name in self._split(row["service_counties"])
        ]
        vendor.categories.set(categories)
        vendor.service_counties.set(service_counties)

        homeowner, created = User.objects.get_or_create(
            username=row["homeowner_username"],
            defaults={"email": row["homeowner_email"], "role": User.Role.HOMEOWNER},
        )
        if created:
            homeowner.set_password(test_password)
            homeowner.save()

        project_category, _ = Category.objects.get_or_create(
            name=row["project_category"],
            defaults={"slug": self._slug(row["project_category"])},
        )
        project_county, _ = County.objects.get_or_create(
            name=row["county"],
            defaults={"slug": self._slug(row["county"]), "launch_enabled": True},
        )
        project, _ = Project.objects.update_or_create(
            vendor=vendor,
            title=row["project_title"],
            defaults={
                "category": project_category,
                "description": row["project_description"],
                "city": row["city"],
                "county": project_county,
                "started_on": date.fromisoformat(row["started_on"]),
                "completed_on": date.fromisoformat(row["completed_on"]),
                "homeowner_email": homeowner.email,
                "status": row["project_status"],
            },
        )
        return vendor, homeowner, project

    @staticmethod
    def _split(value):
        return [part.strip() for part in value.split("|") if part.strip()]

    @staticmethod
    def _slug(value):
        return value.lower().replace(" ", "-")
