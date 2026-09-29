import uuid
from pathlib import Path

from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class User(AbstractUser):
    class Role(models.TextChoices):
        HOMEOWNER = "homeowner", "Homeowner"
        VENDOR = "vendor", "Vendor"
        ADMIN = "admin", "Admin"

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.HOMEOWNER)

    def save(self, *args, **kwargs):
        self.email = self.email.strip().lower()
        super().save(*args, **kwargs)


class County(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(unique=True)
    launch_enabled = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class VendorProfile(models.Model):
    class LicenseState(models.TextChoices):
        PENDING = "pending", "Pending review"
        VERIFIED = "verified", "CSLB verified"
        INELIGIBLE = "ineligible", "Not eligible"

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="vendor_profile")
    business_name = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180, unique=True, blank=True)
    description = models.TextField(blank=True)
    license_number = models.CharField(max_length=20, unique=True)
    license_state = models.CharField(
        max_length=20, choices=LicenseState.choices, default=LicenseState.PENDING
    )
    license_checked_at = models.DateTimeField(null=True, blank=True)
    license_classifications = models.CharField(
        max_length=200, blank=True, help_text="Example: B, C-10"
    )
    categories = models.ManyToManyField(Category, related_name="vendors", blank=True)
    service_counties = models.ManyToManyField(County, related_name="vendors", blank=True)
    score = models.DecimalField(
        max_digits=4, decimal_places=1, default=0, validators=[MinValueValidator(0)]
    )
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-score", "business_name"]

    def __str__(self):
        return self.business_name

    def save(self, *args, **kwargs):
        self.license_number = "".join(
            character for character in self.license_number if character.isdigit()
        )
        if not self.slug:
            base = slugify(self.business_name) or "vendor"
            candidate = base
            suffix = 2
            while VendorProfile.objects.exclude(pk=self.pk).filter(slug=candidate).exists():
                candidate = f"{base}-{suffix}"
                suffix += 1
            self.slug = candidate
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("vendor-detail", kwargs={"slug": self.slug})


class Project(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PENDING = "pending", "Awaiting homeowner"
        CONFIRMED = "confirmed", "Homeowner confirmed"
        REJECTED = "rejected", "Homeowner rejected"

    vendor = models.ForeignKey(VendorProfile, on_delete=models.CASCADE, related_name="projects")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="projects")
    title = models.CharField(max_length=160)
    description = models.TextField()
    city = models.CharField(max_length=100)
    county = models.ForeignKey(County, on_delete=models.PROTECT, related_name="projects")
    started_on = models.DateField()
    completed_on = models.DateField()
    homeowner_email = models.EmailField(help_text="Private. Used only for confirmation.")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    homeowner_decided_at = models.DateTimeField(null=True, blank=True)
    is_public = models.BooleanField(default=False)
    material_version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-completed_on", "-created_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.homeowner_email = self.homeowner_email.strip().lower()
        self.is_public = self.status == self.Status.CONFIRMED
        super().save(*args, **kwargs)

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.started_on and self.completed_on and self.started_on > self.completed_on:
            raise ValidationError({"completed_on": "Completion date must be after the start date."})


class ProjectVerificationEvent(models.Model):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="verification_events"
    )
    actor = models.ForeignKey(User, on_delete=models.PROTECT, related_name="verification_events")
    from_status = models.CharField(max_length=20, choices=Project.Status.choices)
    to_status = models.CharField(max_length=20, choices=Project.Status.choices)
    note = models.TextField(blank=True)
    project_version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.project}: {self.from_status} → {self.to_status}"


def private_project_upload_path(instance, filename):
    extension = Path(filename).suffix.lower() or ".bin"
    return f"private/projects/{instance.project_id}/{uuid.uuid4().hex}{extension}"


def processed_project_upload_path(instance, filename):
    return f"processed/projects/{instance.project_id}/{uuid.uuid4().hex}.jpg"


class ProjectMedia(models.Model):
    class Kind(models.TextChoices):
        BEFORE = "before", "Before"
        AFTER = "after", "After"

    class ReviewStatus(models.TextChoices):
        PROCESSING = "processing", "Processing"
        READY = "ready", "Ready"
        MANUAL_REVIEW = "manual_review", "Needs manual review"
        REJECTED = "rejected", "Rejected"
        FAILED = "failed", "Processing failed"

    class LlmStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        COMPLETED = "completed", "Completed"
        DISABLED = "disabled", "Disabled"
        FAILED = "failed", "Failed"

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="media")
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="project_media")
    kind = models.CharField(max_length=10, choices=Kind.choices)
    original_file = models.ImageField(upload_to=private_project_upload_path)
    processed_file = models.ImageField(upload_to=processed_project_upload_path, blank=True)
    original_name = models.CharField(max_length=255)
    detected_mime = models.CharField(max_length=80, blank=True)
    byte_size = models.PositiveIntegerField(default=0)
    width = models.PositiveIntegerField(default=0)
    height = models.PositiveIntegerField(default=0)
    sha256 = models.CharField(max_length=64, blank=True, db_index=True)
    metadata_stripped = models.BooleanField(default=False)
    review_status = models.CharField(
        max_length=20, choices=ReviewStatus.choices, default=ReviewStatus.PROCESSING
    )
    llm_status = models.CharField(
        max_length=20, choices=LlmStatus.choices, default=LlmStatus.PENDING
    )
    llm_analysis = models.JSONField(default=dict, blank=True)
    alt_text = models.CharField(max_length=300, blank=True)
    review_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["kind", "created_at"]

    def __str__(self):
        return f"{self.project}: {self.get_kind_display()} image"
