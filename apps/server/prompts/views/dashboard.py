"""
Django Template Dashboard Views for Prompt Registry CUD operations.
Requires Django Session Authentication.
"""

from typing import Any

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import transaction
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import ListView

from apps.server.prompts.models import Label, Prompt, PromptCategory, Version


class DashboardStaffRequiredMixin(UserPassesTestMixin):
    """
    Mixin to ensure only staff/admin users can access the dashboard.
    """

    request: HttpRequest

    def test_func(self) -> bool:
        user = self.request.user
        return bool(user.is_authenticated and (user.is_staff or user.is_superuser))

    def handle_no_permission(self) -> HttpResponseRedirect:
        if not self.request.user.is_authenticated:
            return redirect("dashboard-login")
        messages.error(self.request, "Access denied. Dashboard requires staff permissions.")
        return redirect("dashboard-login")


class DashboardLoginView(View):
    """
    Session Auth Login View for Dashboard Admins.
    """

    template_name = "prompts/login.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
            return redirect("dashboard-prompt-list")
        form = AuthenticationForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request: HttpRequest) -> HttpResponse:
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user and (user.is_staff or user.is_superuser):
                login(request, user)
                messages.success(request, f"Welcome, {user.username}!")
                return redirect("dashboard-prompt-list")
            else:
                messages.error(
                    request, "Access denied. Only staff members can access the dashboard."
                )
        else:
            messages.error(request, "Invalid username or password.")
        return render(request, self.template_name, {"form": form})


class DashboardLogoutView(View):
    """
    Session Auth Logout View.
    """

    def post(self, request: HttpRequest) -> HttpResponse:
        logout(request)
        messages.info(request, "Logged out successfully.")
        return redirect("dashboard-login")

    def get(self, request: HttpRequest) -> HttpResponse:
        return self.post(request)


class DashboardPromptListView(LoginRequiredMixin, DashboardStaffRequiredMixin, ListView):  # type: ignore[type-arg]
    """
    List all prompts in the registry for dashboard management.
    """

    model = Prompt
    template_name = "prompts/prompt_list.html"
    context_object_name = "prompts"
    paginate_by = 20

    def get_queryset(self) -> Any:
        return (
            Prompt.objects.select_related("category")
            .prefetch_related("versions", "labels")
            .order_by("-updated_at")
        )

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["categories"] = PromptCategory.objects.all()
        return context


class DashboardPromptCreateView(LoginRequiredMixin, DashboardStaffRequiredMixin, View):
    """
    Create a new prompt asset and initial version.
    """

    template_name = "prompts/prompt_form.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        categories = PromptCategory.objects.filter(is_active=True)
        return render(request, self.template_name, {"categories": categories, "is_create": True})

    def post(self, request: HttpRequest) -> HttpResponse:
        name = request.POST.get("name", "").strip()
        slug = request.POST.get("slug", "").strip()
        description = request.POST.get("description", "").strip()
        category_id = request.POST.get("category_id")
        template_text = request.POST.get("template_text", "").strip()

        if not name or not slug or not category_id:
            messages.error(request, "Name, slug, and category are required.")
            categories = PromptCategory.objects.filter(is_active=True)
            return render(
                request, self.template_name, {"categories": categories, "is_create": True}
            )

        category = get_object_or_404(PromptCategory, id=category_id)

        try:
            with transaction.atomic():
                prompt = Prompt.objects.create(
                    name=name,
                    slug=slug,
                    description=description,
                    category=category,
                )
                version = Version.objects.create(
                    prompt=prompt,
                    version_number=1,
                    template_text=template_text,
                    changelog="Initial version created via dashboard",
                )
                Label.objects.create(
                    prompt=prompt,
                    version=version,
                    name="production",
                )
            messages.success(
                request, f"Prompt '{prompt.name}' created successfully with production version v1."
            )
            return redirect("dashboard-prompt-list")
        except Exception as e:
            messages.error(request, f"Failed to create prompt: {e}")
            categories = PromptCategory.objects.filter(is_active=True)
            return render(
                request, self.template_name, {"categories": categories, "is_create": True}
            )


class DashboardPromptUpdateView(LoginRequiredMixin, DashboardStaffRequiredMixin, View):
    """
    Update prompt details or add a new version.
    """

    template_name = "prompts/prompt_form.html"

    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        prompt = get_object_or_404(Prompt, pk=pk)
        categories = PromptCategory.objects.filter(is_active=True)
        latest_version = prompt.versions.order_by("-version_number").first()
        return render(
            request,
            self.template_name,
            {
                "prompt": prompt,
                "categories": categories,
                "latest_version": latest_version,
                "is_create": False,
            },
        )

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        prompt = get_object_or_404(Prompt, pk=pk)
        name = request.POST.get("name", "").strip()
        description = request.POST.get("description", "").strip()
        category_id = request.POST.get("category_id")
        template_text = request.POST.get("template_text", "").strip()
        create_new_version = request.POST.get("create_new_version") == "true"

        if not name or not category_id:
            messages.error(request, "Name and category are required.")
            return redirect("dashboard-prompt-update", pk=pk)

        category = get_object_or_404(PromptCategory, id=category_id)

        try:
            with transaction.atomic():
                prompt.name = name
                prompt.description = description
                prompt.category = category
                prompt.save()

                if create_new_version:
                    latest_v = prompt.versions.order_by("-version_number").first()
                    next_ver = (latest_v.version_number + 1) if latest_v else 1
                    new_version = Version.objects.create(
                        prompt=prompt,
                        version_number=next_ver,
                        template_text=template_text,
                        changelog=f"Dashboard update to v{next_ver}",
                    )
                    # Update production label to point to latest version
                    Label.objects.update_or_create(
                        prompt=prompt,
                        name="production",
                        defaults={"version": new_version},
                    )
                    messages.success(
                        request, f"Prompt '{prompt.name}' updated with new version v{next_ver}."
                    )
                else:
                    latest_v = prompt.versions.order_by("-version_number").first()
                    if latest_v:
                        latest_v.template_text = template_text
                        latest_v.save()
                    messages.success(request, f"Prompt '{prompt.name}' updated successfully.")

            return redirect("dashboard-prompt-list")
        except Exception as e:
            messages.error(request, f"Failed to update prompt: {e}")
            return redirect("dashboard-prompt-update", pk=pk)


class DashboardPromptDeleteView(LoginRequiredMixin, DashboardStaffRequiredMixin, View):
    """
    Delete a prompt asset.
    """

    template_name = "prompts/prompt_confirm_delete.html"

    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        prompt = get_object_or_404(Prompt, pk=pk)
        return render(request, self.template_name, {"prompt": prompt})

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        prompt = get_object_or_404(Prompt, pk=pk)
        prompt_name = prompt.name
        prompt.delete()
        messages.success(request, f"Prompt '{prompt_name}' deleted successfully.")
        return redirect("dashboard-prompt-list")
