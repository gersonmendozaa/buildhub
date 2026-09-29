from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    Category,
    County,
    Project,
    ProjectMedia,
    ProjectVerificationEvent,
    User,
    VendorProfile,
)


@admin.register(User)
class MarketplaceUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Marketplace", {"fields": ("role",)}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("Marketplace", {"fields": ("email", "role")}),)
    list_display = ("username", "email", "role", "is_staff", "is_active")
    list_filter = ("role", "is_staff", "is_active")


@admin.register(VendorProfile)
class VendorProfileAdmin(admin.ModelAdmin):
    list_display = ("business_name", "license_number", "license_state", "score", "is_published")
    list_filter = ("license_state", "is_published", "categories", "service_counties")
    search_fields = ("business_name", "license_number")
    filter_horizontal = ("categories", "service_counties")


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "vendor", "county", "status", "completed_on", "is_public")
    list_filter = ("status", "county", "category")
    search_fields = ("title", "vendor__business_name", "homeowner_email")


@admin.register(ProjectMedia)
class ProjectMediaAdmin(admin.ModelAdmin):
    list_display = (
        "project",
        "kind",
        "review_status",
        "llm_status",
        "detected_mime",
        "created_at",
    )
    list_filter = ("kind", "review_status", "llm_status")
    readonly_fields = (
        "sha256",
        "detected_mime",
        "byte_size",
        "width",
        "height",
        "metadata_stripped",
        "llm_analysis",
    )


admin.site.register(Category)
admin.site.register(County)
admin.site.register(ProjectVerificationEvent)
