from django.urls import path

from . import views

urlpatterns = [
    path("", views.vendor_list, name="vendor-list"),
    path("vendors/<slug:slug>/", views.vendor_detail, name="vendor-detail"),
    path("register/", views.register, name="register"),
    path("login/", views.MarketplaceLoginView.as_view(), name="login"),
    path("logout/", views.MarketplaceLogoutView.as_view(), name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("dashboard/vendor-profile/", views.vendor_profile_edit, name="vendor-profile-edit"),
    path("dashboard/projects/new/", views.project_create, name="project-create"),
    path(
        "dashboard/projects/<int:project_id>/media/",
        views.project_media_manage,
        name="project-media-manage",
    ),
    path(
        "dashboard/projects/<int:project_id>/media/<int:media_id>/delete/",
        views.project_media_delete,
        name="project-media-delete",
    ),
    path(
        "dashboard/projects/<int:project_id>/submit/",
        views.project_submit_verification,
        name="project-submit-verification",
    ),
    path(
        "dashboard/projects/<int:project_id>/verify/", views.project_verify, name="project-verify"
    ),
    path("project-media/<int:media_id>/", views.project_media_file, name="project-media-file"),
]
