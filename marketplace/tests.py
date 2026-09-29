import io
import tempfile
from datetime import date

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from PIL import Image

from .models import Category, County, Project, ProjectMedia, User, VendorProfile


class MarketplaceFlowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.media_directory = tempfile.TemporaryDirectory()
        cls.settings_override = override_settings(
            MEDIA_ROOT=cls.media_directory.name, ANTHROPIC_ENABLED=False
        )
        cls.settings_override.enable()

    @classmethod
    def tearDownClass(cls):
        cls.settings_override.disable()
        cls.media_directory.cleanup()
        super().tearDownClass()

    def setUp(self):
        self.county = County.objects.create(name="San Mateo", slug="san-mateo")
        self.category = Category.objects.create(
            name="Kitchen remodeling", slug="kitchen-remodeling"
        )
        self.vendor_user = User.objects.create_user(
            username="builder",
            email="builder@example.com",
            password="strong-test-password",
            role=User.Role.VENDOR,
        )
        self.vendor = VendorProfile.objects.create(
            user=self.vendor_user,
            business_name="Peninsula Build Co.",
            license_number="1234567",
            is_published=True,
        )
        self.homeowner = User.objects.create_user(
            username="owner",
            email="owner@example.com",
            password="strong-test-password",
            role=User.Role.HOMEOWNER,
        )
        self.project = Project.objects.create(
            vendor=self.vendor,
            category=self.category,
            title="Bright kitchen renovation",
            description="Cabinet, counter, lighting, and flooring update.",
            city="San Mateo",
            county=self.county,
            started_on=date(2026, 1, 2),
            completed_on=date(2026, 3, 10),
            homeowner_email=self.homeowner.email,
            status=Project.Status.PENDING,
        )

    def test_public_list_only_shows_published_vendors(self):
        response = self.client.get(reverse("vendor-list"))
        self.assertContains(response, "Peninsula Build Co.")

    def test_matching_homeowner_can_confirm_project(self):
        self.client.force_login(self.homeowner)
        response = self.client.post(
            reverse("project-verify", args=[self.project.pk]),
            {
                "project_version": self.project.material_version,
                "decision": Project.Status.CONFIRMED,
                "note": "Looks accurate.",
            },
        )
        self.assertRedirects(response, reverse("dashboard"))
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, Project.Status.CONFIRMED)
        self.assertTrue(self.project.is_public)
        self.assertEqual(self.project.verification_events.count(), 1)

    def test_other_homeowner_cannot_view_project_verification(self):
        other = User.objects.create_user(
            username="other", email="other@example.com", password="strong-test-password"
        )
        self.client.force_login(other)
        response = self.client.get(reverse("project-verify", args=[self.project.pk]))
        self.assertEqual(response.status_code, 404)

    def test_homeowner_cannot_confirm_stale_project_version(self):
        self.client.force_login(self.homeowner)
        response = self.client.post(
            reverse("project-verify", args=[self.project.pk]),
            {
                "project_version": self.project.material_version - 1,
                "decision": Project.Status.CONFIRMED,
                "note": "This page is stale.",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "changed after the page was opened")
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, Project.Status.PENDING)

    def test_vendor_uploads_before_and_after_then_submits(self):
        self.client.force_login(self.vendor_user)
        self.project.status = Project.Status.CONFIRMED
        self.project.save()

        for kind, color in [(ProjectMedia.Kind.BEFORE, "gray"), (ProjectMedia.Kind.AFTER, "blue")]:
            response = self.client.post(
                reverse("project-media-manage", args=[self.project.pk]),
                {"kind": kind, "images": self._image_upload(f"{kind}.png", color)},
            )
            self.assertRedirects(response, reverse("project-media-manage", args=[self.project.pk]))

        self.project.refresh_from_db()
        self.assertEqual(self.project.status, Project.Status.DRAFT)
        self.assertFalse(self.project.is_public)
        self.assertEqual(self.project.material_version, 3)
        self.assertEqual(
            self.project.media.filter(review_status=ProjectMedia.ReviewStatus.READY).count(),
            2,
        )
        media = self.project.media.first()
        self.assertTrue(media.metadata_stripped)
        self.assertEqual(media.detected_mime, "image/png")
        self.assertEqual(media.llm_status, ProjectMedia.LlmStatus.DISABLED)

        response = self.client.post(reverse("project-submit-verification", args=[self.project.pk]))
        self.assertRedirects(response, reverse("dashboard"))
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, Project.Status.PENDING)

    def test_unrelated_user_cannot_read_private_processed_image(self):
        self.client.force_login(self.vendor_user)
        self.client.post(
            reverse("project-media-manage", args=[self.project.pk]),
            {
                "kind": ProjectMedia.Kind.BEFORE,
                "images": self._image_upload("private.png", "red"),
            },
        )
        media = self.project.media.get()
        outsider = User.objects.create_user(
            username="outsider",
            email="outsider@example.com",
            password="strong-test-password",
        )
        self.client.force_login(outsider)
        response = self.client.get(reverse("project-media-file", args=[media.pk]))
        self.assertEqual(response.status_code, 404)

    @staticmethod
    def _image_upload(name, color):
        output = io.BytesIO()
        Image.new("RGB", (120, 90), color=color).save(output, format="PNG")
        return SimpleUploadedFile(name, output.getvalue(), content_type="image/png")
