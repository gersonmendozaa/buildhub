from functools import wraps

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.db import transaction
from django.db.models import Count, Prefetch, Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import (
    ProjectForm,
    ProjectMediaUploadForm,
    RegistrationForm,
    VendorProfileForm,
    VerificationDecisionForm,
)
from .models import (
    Category,
    County,
    Project,
    ProjectMedia,
    ProjectVerificationEvent,
    User,
    VendorProfile,
)
from .services.media_processing import process_project_media


def vendor_required(view):
    @wraps(view)
    @login_required
    def wrapped(request, *args, **kwargs):
        if request.user.role != User.Role.VENDOR:
            messages.error(request, "This area is for vendor accounts.")
            return redirect("dashboard")
        return view(request, *args, **kwargs)

    return wrapped


def vendor_list(request):
    showcase_projects = (
        Project.objects.filter(status=Project.Status.CONFIRMED, is_public=True)
        .select_related("category", "county")
        .prefetch_related(
            Prefetch(
                "media",
                queryset=ProjectMedia.objects.filter(
                    review_status=ProjectMedia.ReviewStatus.READY
                ).order_by("kind", "created_at"),
                to_attr="showcase_media",
            )
        )
        .order_by("-completed_on")
    )
    vendors = (
        VendorProfile.objects.filter(is_published=True)
        .prefetch_related(
            "categories",
            "service_counties",
            Prefetch("projects", queryset=showcase_projects, to_attr="showcase_projects"),
        )
        .annotate(
            verified_project_count=Count(
                "projects", filter=Q(projects__status=Project.Status.CONFIRMED)
            )
        )
    )
    query = request.GET.get("q", "").strip()
    category = request.GET.get("category", "")
    county = request.GET.get("county", "")
    verified_only = request.GET.get("verified") == "1"
    if query:
        vendors = vendors.filter(
            Q(business_name__icontains=query)
            | Q(description__icontains=query)
            | Q(license_classifications__icontains=query)
        )
    if category:
        vendors = vendors.filter(categories__slug=category)
    if county:
        vendors = vendors.filter(service_counties__slug=county)
    if verified_only:
        vendors = vendors.filter(license_state=VendorProfile.LicenseState.VERIFIED)
    context = {
        "vendors": vendors.distinct(),
        "categories": Category.objects.all(),
        "counties": County.objects.filter(launch_enabled=True),
        "filters": {"q": query, "category": category, "county": county, "verified": verified_only},
    }
    return render(request, "marketplace/vendor_list.html", context)


def vendor_detail(request, slug):
    vendor = get_object_or_404(
        VendorProfile.objects.prefetch_related("categories", "service_counties"),
        slug=slug,
        is_published=True,
    )
    projects = (
        vendor.projects.filter(status=Project.Status.CONFIRMED, is_public=True)
        .select_related("category", "county")
        .prefetch_related("media")
    )
    return render(
        request, "marketplace/vendor_detail.html", {"vendor": vendor, "projects": projects}
    )


def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Your account is ready.")
        return redirect("dashboard")
    return render(request, "registration/register.html", {"form": form})


class MarketplaceLoginView(LoginView):
    template_name = "registration/login.html"


class MarketplaceLogoutView(LogoutView):
    pass


@login_required
def dashboard(request):
    if request.user.role == User.Role.VENDOR:
        profile = VendorProfile.objects.filter(user=request.user).first()
        projects = profile.projects.all() if profile else Project.objects.none()
        return render(
            request,
            "marketplace/vendor_dashboard.html",
            {"profile": profile, "projects": projects},
        )
    pending = Project.objects.filter(
        homeowner_email__iexact=request.user.email, status=Project.Status.PENDING
    ).select_related("vendor", "category", "county")
    completed = Project.objects.filter(
        homeowner_email__iexact=request.user.email,
        status__in=[Project.Status.CONFIRMED, Project.Status.REJECTED],
    ).select_related("vendor")
    return render(
        request,
        "marketplace/homeowner_dashboard.html",
        {"pending_projects": pending, "completed_projects": completed},
    )


@vendor_required
def vendor_profile_edit(request):
    profile = VendorProfile.objects.filter(user=request.user).first()
    form = VendorProfileForm(request.POST or None, instance=profile)
    if request.method == "POST" and form.is_valid():
        profile = form.save(commit=False)
        profile.user = request.user
        profile.save()
        form.save_m2m()
        messages.success(request, "Vendor profile saved.")
        return redirect("dashboard")
    return render(request, "marketplace/form_page.html", {"form": form, "title": "Vendor profile"})


@vendor_required
def project_create(request):
    profile = VendorProfile.objects.filter(user=request.user).first()
    if not profile:
        messages.info(request, "Create your vendor profile before adding work.")
        return redirect("vendor-profile-edit")
    form = ProjectForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        project = form.save(commit=False)
        project.vendor = profile
        project.status = Project.Status.DRAFT
        project.save()
        messages.success(request, "Project saved. Add before and after images next.")
        return redirect("project-media-manage", project_id=project.pk)
    return render(
        request, "marketplace/form_page.html", {"form": form, "title": "Add completed work"}
    )


@login_required
@transaction.atomic
def project_verify(request, project_id):
    if request.user.role != User.Role.HOMEOWNER:
        raise Http404
    project_queryset = Project.objects.select_related("vendor", "category", "county")
    if request.method == "POST":
        project_queryset = project_queryset.select_for_update()
    project = get_object_or_404(
        project_queryset,
        pk=project_id,
        homeowner_email__iexact=request.user.email,
        status=Project.Status.PENDING,
    )
    form = VerificationDecisionForm(request.POST or None, project=project)
    if request.method == "POST" and form.is_valid():
        previous = project.status
        project.status = form.cleaned_data["decision"]
        project.homeowner_decided_at = timezone.now()
        project.save()
        ProjectVerificationEvent.objects.create(
            project=project,
            actor=request.user,
            from_status=previous,
            to_status=project.status,
            note=form.cleaned_data["note"],
            project_version=project.material_version,
        )
        messages.success(request, "Your decision was recorded.")
        return redirect("dashboard")
    return render(request, "marketplace/project_verify.html", {"project": project, "form": form})


@vendor_required
def project_media_manage(request, project_id):
    profile = get_object_or_404(VendorProfile, user=request.user)
    project = get_object_or_404(
        Project.objects.prefetch_related("media"), pk=project_id, vendor=profile
    )
    form = ProjectMediaUploadForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        if project.media.count() + len(form.cleaned_data["images"]) > 20:
            form.add_error("images", "A project can contain at most 20 images.")
        else:
            for uploaded_file in form.cleaned_data["images"]:
                media = ProjectMedia.objects.create(
                    project=project,
                    created_by=request.user,
                    kind=form.cleaned_data["kind"],
                    original_file=uploaded_file,
                    original_name=uploaded_file.name[:255],
                )
                process_project_media(media)
            _invalidate_project_confirmation(project)
            messages.success(request, "Images uploaded and processed.")
            return redirect("project-media-manage", project_id=project.pk)
    return render(
        request,
        "marketplace/project_media_manage.html",
        {"project": project, "form": form},
    )


@vendor_required
def project_media_delete(request, project_id, media_id):
    if request.method != "POST":
        raise Http404
    profile = get_object_or_404(VendorProfile, user=request.user)
    project = get_object_or_404(Project, pk=project_id, vendor=profile)
    media = get_object_or_404(ProjectMedia, pk=media_id, project=project)
    media.original_file.delete(save=False)
    if media.processed_file:
        media.processed_file.delete(save=False)
    media.delete()
    _invalidate_project_confirmation(project)
    messages.success(request, "Image removed.")
    return redirect("project-media-manage", project_id=project.pk)


@vendor_required
def project_submit_verification(request, project_id):
    if request.method != "POST":
        raise Http404
    profile = get_object_or_404(VendorProfile, user=request.user)
    project = get_object_or_404(Project, pk=project_id, vendor=profile)
    ready_media = project.media.filter(review_status=ProjectMedia.ReviewStatus.READY)
    has_before = ready_media.filter(kind=ProjectMedia.Kind.BEFORE).exists()
    has_after = ready_media.filter(kind=ProjectMedia.Kind.AFTER).exists()
    if not has_before or not has_after:
        messages.error(
            request,
            "At least one approved before image and one approved after image are required.",
        )
    elif project.media.exclude(review_status=ProjectMedia.ReviewStatus.READY).exists():
        messages.error(request, "Resolve images requiring review before submission.")
    else:
        project.status = Project.Status.PENDING
        project.save(update_fields=["status", "is_public", "updated_at"])
        messages.success(request, "Project submitted for homeowner confirmation.")
        return redirect("dashboard")
    return redirect("project-media-manage", project_id=project.pk)


def project_media_file(request, media_id):
    media = get_object_or_404(
        ProjectMedia.objects.select_related("project__vendor__user"), pk=media_id
    )
    project = media.project
    is_vendor_owner = request.user.is_authenticated and project.vendor.user_id == request.user.id
    is_invited_homeowner = (
        request.user.is_authenticated
        and getattr(request.user, "role", None) == User.Role.HOMEOWNER
        and project.homeowner_email.lower() == request.user.email.lower()
    )
    is_public = (
        project.is_public
        and project.status == Project.Status.CONFIRMED
        and media.review_status == ProjectMedia.ReviewStatus.READY
    )
    if not (is_vendor_owner or is_invited_homeowner or is_public):
        raise Http404
    if not media.processed_file:
        raise Http404
    media.processed_file.open("rb")
    response = FileResponse(media.processed_file, content_type="image/jpeg")
    response["Content-Disposition"] = f'inline; filename="project-{media.pk}.jpg"'
    response["Cache-Control"] = "private, max-age=300"
    return response


def _invalidate_project_confirmation(project):
    project.material_version += 1
    project.status = Project.Status.DRAFT
    project.is_public = False
    project.save(update_fields=["material_version", "status", "is_public", "updated_at"])
