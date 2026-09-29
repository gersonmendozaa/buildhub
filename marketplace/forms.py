from django import forms
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm

from .models import Project, ProjectMedia, User, VendorProfile


class RegistrationForm(UserCreationForm):
    email = forms.EmailField()
    role = forms.ChoiceField(
        choices=[
            (User.Role.HOMEOWNER, "I am a homeowner"),
            (User.Role.VENDOR, "I represent a construction company"),
        ]
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "role")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account already uses this email.")
        return email


class VendorProfileForm(forms.ModelForm):
    class Meta:
        model = VendorProfile
        fields = (
            "business_name",
            "description",
            "license_number",
            "license_classifications",
            "categories",
            "service_counties",
            "is_published",
        )
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
            "categories": forms.CheckboxSelectMultiple,
            "service_counties": forms.CheckboxSelectMultiple,
        }


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = (
            "title",
            "category",
            "description",
            "city",
            "county",
            "started_on",
            "completed_on",
            "homeowner_email",
        )
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
            "started_on": forms.DateInput(attrs={"type": "date"}),
            "completed_on": forms.DateInput(attrs={"type": "date"}),
        }


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleImageField(forms.FileField):
    widget = MultipleFileInput

    def clean(self, data, initial=None):
        files = data if isinstance(data, (list, tuple)) else [data]
        if not files or files == [None]:
            raise forms.ValidationError("Select at least one image.")
        if len(files) > 10:
            raise forms.ValidationError("Upload no more than 10 images at a time.")
        cleaned = []
        for uploaded_file in files:
            if uploaded_file.size > settings.PROJECT_IMAGE_MAX_BYTES:
                raise forms.ValidationError(f"{uploaded_file.name} exceeds the 15 MB upload limit.")
            cleaned.append(super().clean(uploaded_file, initial))
        return cleaned


class ProjectMediaUploadForm(forms.Form):
    kind = forms.ChoiceField(choices=ProjectMedia.Kind.choices)
    images = MultipleImageField(help_text="JPEG, PNG, or WebP. Up to 10 images and 15 MB each.")


class VerificationDecisionForm(forms.Form):
    project_version = forms.IntegerField(widget=forms.HiddenInput)
    decision = forms.ChoiceField(
        choices=[
            (Project.Status.CONFIRMED, "Confirm this work"),
            (Project.Status.REJECTED, "This is not accurate"),
        ],
        widget=forms.RadioSelect,
    )
    note = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))

    def __init__(self, *args, project, **kwargs):
        super().__init__(*args, **kwargs)
        self.project = project
        self.fields["project_version"].initial = project.material_version

    def clean_project_version(self):
        version = self.cleaned_data["project_version"]
        if version != self.project.material_version:
            raise forms.ValidationError(
                "This project changed after the page was opened. Review it again before deciding."
            )
        return version
