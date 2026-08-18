"""
Django Template Dashboard Views for Prompt Registry CUD operations.
Requires Django Session Authentication and Staff Permissions.
"""

import logging
from typing import Any

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import IntegrityError, models, transaction
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify
from django.views import View
from django.views.generic import ListView
from promptkit import (
    CompiledPrompt,
    InvalidVariableTypeError,
    MissingVariableError,
    PromptKitError,
    TemplateValidationError,
    UnexpectedVariableError,
)

from apps.server.prompts.forms import PlaygroundCompileForm
from apps.server.prompts.models import (
    Prompt,
    PromptCategory,
    Section,
    VariableDefinition,
    Version,
)
from apps.server.prompts.services.lifecycle import (
    StaleRevisionError,
    clear_on_live_version,
    clone_version,
    create_prompt_with_initial_draft,
    delete_draft_version,
    delete_prompt,
    publish_version,
    remove_custom_label,
    set_custom_label,
    set_on_live_version,
)
from apps.server.prompts.services.playground import (
    compile_playground_version,
    playground_version_queryset,
)
from apps.server.prompts.services.templates import (
    is_variable_referenced,
    rename_variable_in_content,
    validate_variable_default_value,
)

logger = logging.getLogger(__name__)


class DashboardStaffRequiredMixin(UserPassesTestMixin):
    """
    Mixin to ensure only authenticated staff users can access dashboard features.
    """

    request: HttpRequest

    def test_func(self) -> bool:
        user = self.request.user
        return bool(user.is_authenticated and (user.is_staff or user.is_superuser))

    def handle_no_permission(self) -> HttpResponseRedirect:
        if not self.request.user.is_authenticated:
            return redirect("dashboard-login")
        messages.error(self.request, "Access denied. Staff permission is required.")
        return redirect("dashboard-login")


# --- Auth Views ---


class DashboardLoginView(View):
    """
    Session Auth Login View for Dashboard.
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
                messages.success(request, f"Welcome back, {user.username}!")
                return redirect("dashboard-prompt-list")
            else:
                messages.error(request, "Access denied. Staff permission is required.")
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


# --- Category Dashboard Views (US4) ---


class DashboardCategoryListView(LoginRequiredMixin, DashboardStaffRequiredMixin, View):
    template_name = "prompts/category_list.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        categories = PromptCategory.objects.all().order_by("name")
        return render(request, self.template_name, {"categories": categories})

    def post(self, request: HttpRequest) -> HttpResponse:
        name = request.POST.get("name", "").strip()
        slug_val = request.POST.get("slug", "").strip() or slugify(name)
        description = request.POST.get("description", "").strip()

        if not name:
            messages.error(request, "Category name is required.")
            return redirect("dashboard-category-list")

        try:
            PromptCategory.objects.create(name=name, slug=slug_val, description=description)
            messages.success(request, f"Category '{name}' created successfully.")
        except IntegrityError:
            messages.error(
                request, f"Category with name '{name}' or slug '{slug_val}' already exists."
            )
        except Exception as e:
            messages.error(request, f"Failed to create category: {e}")

        return redirect("dashboard-category-list")


class DashboardCategoryUpdateView(LoginRequiredMixin, DashboardStaffRequiredMixin, View):
    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        category = get_object_or_404(PromptCategory, pk=pk)
        name = request.POST.get("name", "").strip()
        slug_val = request.POST.get("slug", "").strip() or slugify(name)
        description = request.POST.get("description", "").strip()

        if not name:
            messages.error(request, "Category name is required.")
            return redirect("dashboard-category-list")

        try:
            category.name = name
            category.slug = slug_val
            category.description = description
            category.save()
            messages.success(request, f"Category '{name}' updated successfully.")
        except IntegrityError:
            messages.error(request, "Category name or slug already in use.")
        except Exception as e:
            messages.error(request, f"Failed to update category: {e}")

        return redirect("dashboard-category-list")


class DashboardCategoryDeleteView(LoginRequiredMixin, DashboardStaffRequiredMixin, View):
    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        category = get_object_or_404(PromptCategory, pk=pk)
        if category.prompts.exists():
            messages.error(
                request,
                f"Cannot delete category '{category.name}' while prompts are attached to it.",
            )
            return redirect("dashboard-category-list")
        cat_name = category.name
        category.delete()
        messages.success(request, f"Category '{cat_name}' deleted successfully.")
        return redirect("dashboard-category-list")


# --- Prompt Dashboard Views ---


class DashboardPromptListView(LoginRequiredMixin, DashboardStaffRequiredMixin, ListView):  # type: ignore[type-arg]
    model = Prompt
    template_name = "prompts/prompt_list.html"
    context_object_name = "prompts"
    paginate_by = 20

    def get_queryset(self) -> Any:
        qs = Prompt.objects.select_related("category").prefetch_related("versions", "labels")
        category_slug = self.request.GET.get("category")
        if category_slug:
            qs = qs.filter(category__slug=category_slug)
        return qs.order_by("-updated_at")

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["categories"] = PromptCategory.objects.filter(is_active=True).order_by("name")
        context["selected_category"] = self.request.GET.get("category", "")
        return context


class DashboardPromptCreateView(LoginRequiredMixin, DashboardStaffRequiredMixin, View):
    template_name = "prompts/prompt_form.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        categories = PromptCategory.objects.filter(is_active=True).order_by("name")
        return render(request, self.template_name, {"categories": categories, "is_create": True})

    def post(self, request: HttpRequest) -> HttpResponse:
        name = request.POST.get("name", "").strip()
        slug_val = request.POST.get("slug", "").strip() or slugify(name)
        description = request.POST.get("description", "").strip()
        category_id = request.POST.get("category_id")

        if not name or not category_id:
            messages.error(request, "Prompt name and category are required.")
            categories = PromptCategory.objects.filter(is_active=True).order_by("name")
            return render(
                request, self.template_name, {"categories": categories, "is_create": True}
            )

        category = get_object_or_404(PromptCategory, id=category_id)

        try:
            prompt, draft = create_prompt_with_initial_draft(
                category=category,
                name=name,
                slug=slug_val,
                description=description,
            )
            messages.success(
                request,
                f"Prompt '{prompt.name}' created successfully with initial empty draft v1.",
            )
            return redirect("dashboard-prompt-detail", pk=prompt.pk)
        except IntegrityError:
            messages.error(
                request,
                f"Prompt with slug '{slug_val}' or name '{name}' in this category already exists.",
            )
            categories = PromptCategory.objects.filter(is_active=True).order_by("name")
            return render(
                request, self.template_name, {"categories": categories, "is_create": True}
            )
        except Exception as e:
            messages.error(request, f"Failed to create prompt: {e}")
            categories = PromptCategory.objects.filter(is_active=True).order_by("name")
            return render(
                request, self.template_name, {"categories": categories, "is_create": True}
            )


class DashboardPromptUpdateView(LoginRequiredMixin, DashboardStaffRequiredMixin, View):
    template_name = "prompts/prompt_form.html"

    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        prompt = get_object_or_404(Prompt, pk=pk)
        categories = PromptCategory.objects.filter(is_active=True).order_by("name")
        return render(
            request,
            self.template_name,
            {
                "prompt": prompt,
                "categories": categories,
                "is_create": False,
            },
        )

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        prompt = get_object_or_404(Prompt, pk=pk)
        name = request.POST.get("name", "").strip()
        description = request.POST.get("description", "").strip()
        category_id = request.POST.get("category_id")

        if not name or not category_id:
            messages.error(request, "Name and category are required.")
            return redirect("dashboard-prompt-update", pk=pk)

        category = get_object_or_404(PromptCategory, id=category_id)

        try:
            prompt.name = name
            prompt.description = description
            prompt.category = category
            prompt.save()
            messages.success(request, f"Prompt metadata for '{prompt.name}' updated successfully.")
            return redirect("dashboard-prompt-detail", pk=prompt.pk)
        except IntegrityError:
            messages.error(
                request, f"A prompt named '{name}' already exists in category '{category.name}'."
            )
            return redirect("dashboard-prompt-update", pk=pk)
        except Exception as e:
            messages.error(request, f"Failed to update prompt: {e}")
            return redirect("dashboard-prompt-update", pk=pk)


class DashboardPromptDeleteView(LoginRequiredMixin, DashboardStaffRequiredMixin, View):
    template_name = "prompts/prompt_confirm_delete.html"

    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        prompt = get_object_or_404(Prompt, pk=pk)
        return render(request, self.template_name, {"prompt": prompt})

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        prompt = get_object_or_404(Prompt, pk=pk)
        prompt_name = prompt.name
        try:
            delete_prompt(prompt)
            messages.success(request, f"Prompt '{prompt_name}' deleted successfully.")
            return redirect("dashboard-prompt-list")
        except ValueError as ve:
            messages.error(request, str(ve))
            return render(request, self.template_name, {"prompt": prompt})


# --- Prompt Detail & Version Editor Views (US1, US2, US3) ---


class DashboardPromptDetailView(LoginRequiredMixin, DashboardStaffRequiredMixin, View):
    template_name = "prompts/prompt_detail.html"

    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        prompt = get_object_or_404(
            Prompt.objects.select_related("category").prefetch_related("versions", "labels"),
            pk=pk,
        )
        versions = prompt.versions.all().order_by("-version_number")

        v_param = request.GET.get("version")
        if v_param and v_param.isdigit():
            selected_version = versions.filter(version_number=int(v_param)).first()
        else:
            selected_version = versions.first()

        if not selected_version and prompt.versions.exists():
            selected_version = versions.first()

        sections = []
        variables = []
        labels = []
        if selected_version:
            sections = list(selected_version.sections.all().order_by("order"))
            variables = list(selected_version.variables.all().order_by("name"))

        labels = list(prompt.labels.select_related("version").all().order_by("name"))
        on_live_version = versions.filter(is_on_live=True).first()

        return render(
            request,
            self.template_name,
            {
                "prompt": prompt,
                "versions": versions,
                "selected_version": selected_version,
                "sections": sections,
                "variables": variables,
                "labels": labels,
                "on_live_version": on_live_version,
                "role_choices": Section.Role.choices,
                "type_choices": VariableDefinition.VarType.choices,
            },
        )


class DashboardPlaygroundView(LoginRequiredMixin, DashboardStaffRequiredMixin, View):
    """Dashboard entry point for a specific prompt version's Playground."""

    template_name = "prompts/playground.html"

    def get(self, request: HttpRequest, version_id: int) -> HttpResponse:
        version = get_object_or_404(playground_version_queryset(), pk=version_id)
        form = PlaygroundCompileForm(version.variables.all())
        return self._render(request, version, form=form)

    def post(self, request: HttpRequest, version_id: int) -> HttpResponse:
        version = get_object_or_404(playground_version_queryset(), pk=version_id)
        form = PlaygroundCompileForm(version.variables.all(), data=request.POST)
        preview = None
        if form.is_valid():
            try:
                preview = compile_playground_version(version, form.compile_params)
            except PromptKitError as error:
                self._add_compile_error(form, error)
                logger.error(
                    "Playground compilation failed (slug=%s, version=%d, category=%s)",
                    version.prompt.slug,
                    version.version_number,
                    type(error).__name__,
                )
        return self._render(request, version, form=form, preview=preview)

    def _render(
        self,
        request: HttpRequest,
        version: Version,
        *,
        form: PlaygroundCompileForm,
        preview: CompiledPrompt | None = None,
    ) -> HttpResponse:
        return render(
            request,
            self.template_name,
            {
                "prompt": version.prompt,
                "version": version,
                "variables": list(version.variables.all().order_by("name")),
                "form": form,
                "preview": preview,
            },
        )

    @staticmethod
    def _add_compile_error(form: PlaygroundCompileForm, error: PromptKitError) -> None:
        field_name: str | None = None
        if isinstance(error, MissingVariableError | InvalidVariableTypeError):
            variable_name = str(error).rsplit(":", maxsplit=1)[-1].strip()
            candidate = form.field_name(variable_name)
            if candidate in form.fields:
                field_name = candidate
        if isinstance(error, MissingVariableError):
            form.add_error(field_name, "This value is required for compilation.")
        elif isinstance(error, InvalidVariableTypeError):
            form.add_error(field_name, "Enter a value matching the declared type.")
        elif isinstance(error, UnexpectedVariableError):
            form.add_error(None, "An undeclared variable was submitted.")
        elif isinstance(error, TemplateValidationError):
            form.add_error(None, "The prompt template does not match its variable declarations.")
        else:
            form.add_error(None, "The prompt could not be compiled.")


class DashboardVariableSchemaView(LoginRequiredMixin, DashboardStaffRequiredMixin, View):
    """Read-only dashboard schema endpoint for a specific prompt version."""

    def get(self, request: HttpRequest, version_id: int) -> JsonResponse:
        version = get_object_or_404(
            Version.objects.select_related("prompt").prefetch_related("variables"),
            pk=version_id,
        )
        return JsonResponse(
            {
                "prompt": {
                    "id": version.prompt.id,
                    "slug": version.prompt.slug,
                    "name": version.prompt.name,
                },
                "version": {
                    "id": version.id,
                    "number": version.version_number,
                    "status": version.status,
                },
                "variables": [
                    {
                        "name": variable.name,
                        "var_type": variable.var_type,
                        "required": variable.required,
                        "default_value": variable.default_value,
                        "description": variable.description,
                    }
                    for variable in version.variables.all().order_by("name")
                ],
            }
        )


# --- Section CUD Views (US1) ---


class DashboardSectionCreateView(LoginRequiredMixin, DashboardStaffRequiredMixin, View):
    def post(self, request: HttpRequest, version_id: int) -> HttpResponse:
        version = get_object_or_404(Version, id=version_id)
        if version.status != Version.Status.DRAFT:
            messages.error(request, "Cannot modify sections of a published version.")
            return redirect(
                f"/dashboard/prompts/{version.prompt.pk}/?version={version.version_number}"
            )

        role = request.POST.get("role", Section.Role.USER)
        content = request.POST.get("content", "").strip()
        order_val = request.POST.get("order")

        if not content:
            messages.error(request, "Section content cannot be empty.")
            return redirect(
                f"/dashboard/prompts/{version.prompt.pk}/?version={version.version_number}"
            )

        if order_val and order_val.isdigit():
            order = int(order_val)
        else:
            max_order = version.sections.aggregate(m=models.Max("order"))["m"]
            order = (max_order + 1) if max_order is not None else 0

        try:
            Section.objects.create(version=version, role=role, order=order, content=content)
            version.revision += 1
            version.save(update_fields=["revision"])
            messages.success(request, "Section added successfully.")
        except IntegrityError:
            messages.error(request, f"Section order {order} already exists.")
        except Exception as e:
            messages.error(request, f"Failed to add section: {e}")

        return redirect(f"/dashboard/prompts/{version.prompt.pk}/?version={version.version_number}")


class DashboardSectionUpdateView(LoginRequiredMixin, DashboardStaffRequiredMixin, View):
    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        section = get_object_or_404(Section.objects.select_related("version"), pk=pk)
        version = section.version

        if version.status != Version.Status.DRAFT:
            messages.error(request, "Cannot modify sections of a published version.")
            return redirect(
                f"/dashboard/prompts/{version.prompt.pk}/?version={version.version_number}"
            )

        role = request.POST.get("role", section.role)
        content = request.POST.get("content", "").strip()

        if not content:
            messages.error(request, "Section content cannot be empty.")
            return redirect(
                f"/dashboard/prompts/{version.prompt.pk}/?version={version.version_number}"
            )

        section.role = role
        section.content = content
        section.save()

        version.revision += 1
        version.save(update_fields=["revision"])
        messages.success(request, "Section updated successfully.")
        return redirect(f"/dashboard/prompts/{version.prompt.pk}/?version={version.version_number}")


class DashboardSectionDeleteView(LoginRequiredMixin, DashboardStaffRequiredMixin, View):
    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        section = get_object_or_404(Section.objects.select_related("version"), pk=pk)
        version = section.version

        if version.status != Version.Status.DRAFT:
            messages.error(request, "Cannot modify sections of a published version.")
            return redirect(
                f"/dashboard/prompts/{version.prompt.pk}/?version={version.version_number}"
            )

        section.delete()
        version.revision += 1
        version.save(update_fields=["revision"])
        messages.success(request, "Section deleted successfully.")
        return redirect(f"/dashboard/prompts/{version.prompt.pk}/?version={version.version_number}")


# --- Variable CUD Views (US1) ---


class DashboardVariableCreateView(LoginRequiredMixin, DashboardStaffRequiredMixin, View):
    def post(self, request: HttpRequest, version_id: int) -> HttpResponse:
        version = get_object_or_404(Version, id=version_id)
        if version.status != Version.Status.DRAFT:
            messages.error(request, "Cannot modify variables of a published version.")
            return redirect(
                f"/dashboard/prompts/{version.prompt.pk}/?version={version.version_number}"
            )

        name = request.POST.get("name", "").strip()
        var_type = request.POST.get("var_type", VariableDefinition.VarType.STRING)
        required = request.POST.get("required") == "on" or request.POST.get("required") == "true"
        default_value = request.POST.get("default_value", "").strip() or None
        description = request.POST.get("description", "").strip()

        if not name:
            messages.error(request, "Variable name is required.")
            return redirect(
                f"/dashboard/prompts/{version.prompt.pk}/?version={version.version_number}"
            )

        val_ok, val_err = validate_variable_default_value(var_type, default_value)
        if not val_ok:
            messages.error(request, val_err or "Invalid default value.")
            return redirect(
                f"/dashboard/prompts/{version.prompt.pk}/?version={version.version_number}"
            )

        try:
            VariableDefinition.objects.create(
                version=version,
                name=name,
                var_type=var_type,
                required=required,
                default_value=default_value,
                description=description,
            )
            version.revision += 1
            version.save(update_fields=["revision"])
            messages.success(request, f"Variable '${name}' added successfully.")
        except IntegrityError:
            messages.error(request, f"Variable '${name}' already exists in this version.")
        except Exception as e:
            messages.error(request, f"Failed to add variable: {e}")

        return redirect(f"/dashboard/prompts/{version.prompt.pk}/?version={version.version_number}")


class DashboardVariableUpdateView(LoginRequiredMixin, DashboardStaffRequiredMixin, View):
    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        var_def = get_object_or_404(VariableDefinition.objects.select_related("version"), pk=pk)
        version = var_def.version

        if version.status != Version.Status.DRAFT:
            messages.error(request, "Cannot modify variables of a published version.")
            return redirect(
                f"/dashboard/prompts/{version.prompt.pk}/?version={version.version_number}"
            )

        new_name = request.POST.get("name", "").strip()
        var_type = request.POST.get("var_type", var_def.var_type)
        required = request.POST.get("required") == "on" or request.POST.get("required") == "true"
        default_value = request.POST.get("default_value", "").strip() or None
        description = request.POST.get("description", "").strip()

        if not new_name:
            messages.error(request, "Variable name is required.")
            return redirect(
                f"/dashboard/prompts/{version.prompt.pk}/?version={version.version_number}"
            )

        val_ok, val_err = validate_variable_default_value(var_type, default_value)
        if not val_ok:
            messages.error(request, val_err or "Invalid default value.")
            return redirect(
                f"/dashboard/prompts/{version.prompt.pk}/?version={version.version_number}"
            )

        old_name = var_def.name
        try:
            with transaction.atomic():
                var_def.name = new_name
                var_def.var_type = var_type
                var_def.required = required
                var_def.default_value = default_value
                var_def.description = description
                var_def.save()

                # Atomically propagate variable rename to section references
                if old_name != new_name:
                    for sec in version.sections.all():
                        if old_name in sec.content:
                            sec.content = rename_variable_in_content(
                                sec.content, old_name, new_name
                            )
                            sec.save(update_fields=["content"])

                version.revision += 1
                version.save(update_fields=["revision"])

            messages.success(request, "Variable updated successfully.")
        except IntegrityError:
            messages.error(request, f"Variable name '${new_name}' already exists.")
        except Exception as e:
            messages.error(request, f"Failed to update variable: {e}")

        return redirect(f"/dashboard/prompts/{version.prompt.pk}/?version={version.version_number}")


class DashboardVariableDeleteView(LoginRequiredMixin, DashboardStaffRequiredMixin, View):
    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        var_def = get_object_or_404(VariableDefinition.objects.select_related("version"), pk=pk)
        version = var_def.version

        if version.status != Version.Status.DRAFT:
            messages.error(request, "Cannot modify variables of a published version.")
            return redirect(
                f"/dashboard/prompts/{version.prompt.pk}/?version={version.version_number}"
            )

        section_contents = list(version.sections.values_list("content", flat=True))
        if is_variable_referenced(section_contents, var_def.name):
            messages.error(
                request,
                f"Cannot delete variable '${var_def.name}': referenced in sections.",
            )
            return redirect(
                f"/dashboard/prompts/{version.prompt.pk}/?version={version.version_number}"
            )

        var_name = var_def.name
        var_def.delete()
        version.revision += 1
        version.save(update_fields=["revision"])
        messages.success(request, f"Variable '${var_name}' deleted successfully.")
        return redirect(f"/dashboard/prompts/{version.prompt.pk}/?version={version.version_number}")


# --- Lifecycle Actions (Publish, Clone, Delete Draft, On-Live, Labels) ---


class DashboardVersionPublishView(LoginRequiredMixin, DashboardStaffRequiredMixin, View):
    def post(self, request: HttpRequest, version_id: int) -> HttpResponse:
        version = get_object_or_404(Version.objects.select_related("prompt"), id=version_id)
        expected_revision_str = request.POST.get("expected_revision")
        expected_revision = (
            int(expected_revision_str)
            if expected_revision_str and expected_revision_str.isdigit()
            else None
        )

        try:
            pub = publish_version(version.id, expected_revision=expected_revision)
            messages.success(request, f"Version v{pub.version_number} published successfully!")
        except StaleRevisionError:
            messages.error(
                request,
                "Conflict detected: This version was modified by another request.",
            )
        except ValueError as ve:
            messages.error(request, f"Publication failed: {ve}")
        except Exception as e:
            messages.error(request, f"Unexpected error publishing version: {e}")

        return redirect(f"/dashboard/prompts/{version.prompt.pk}/?version={version.version_number}")


class DashboardVersionCloneView(LoginRequiredMixin, DashboardStaffRequiredMixin, View):
    def post(self, request: HttpRequest, version_id: int) -> HttpResponse:
        source_version = get_object_or_404(Version.objects.select_related("prompt"), id=version_id)
        try:
            cloned = clone_version(source_version.id)
            messages.success(
                request,
                f"Cloned v{source_version.version_number} into new draft v{cloned.version_number}.",
            )
            return redirect(
                f"/dashboard/prompts/{source_version.prompt.pk}/?version={cloned.version_number}"
            )
        except Exception as e:
            messages.error(request, f"Failed to clone version: {e}")
            return redirect(
                f"/dashboard/prompts/{source_version.prompt.pk}/?version={source_version.version_number}"
            )


class DashboardVersionDeleteView(LoginRequiredMixin, DashboardStaffRequiredMixin, View):
    def post(self, request: HttpRequest, version_id: int) -> HttpResponse:
        version = get_object_or_404(Version.objects.select_related("prompt"), id=version_id)
        prompt_pk = version.prompt.pk
        ver_num = version.version_number
        try:
            delete_draft_version(version.id)
            messages.success(request, f"Draft version v{ver_num} deleted successfully.")
        except ValueError as ve:
            messages.error(request, str(ve))
        except Exception as e:
            messages.error(request, f"Failed to delete draft version: {e}")

        return redirect("dashboard-prompt-detail", pk=prompt_pk)


class DashboardOnLiveSetView(LoginRequiredMixin, DashboardStaffRequiredMixin, View):
    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        prompt = get_object_or_404(Prompt, pk=pk)
        ver_num = int(request.POST.get("version_number", 0))
        try:
            set_on_live_version(prompt, ver_num)
            messages.success(request, f"Version v{ver_num} is now on-live!")
        except ValueError as ve:
            messages.error(request, str(ve))
        except Exception as e:
            messages.error(request, f"Failed to set on-live version: {e}")

        return redirect(f"/dashboard/prompts/{prompt.pk}/?version={ver_num}")


class DashboardOnLiveClearView(LoginRequiredMixin, DashboardStaffRequiredMixin, View):
    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        prompt = get_object_or_404(Prompt, pk=pk)
        clear_on_live_version(prompt)
        messages.info(request, f"On-live deployment target cleared for '{prompt.name}'.")
        return redirect("dashboard-prompt-detail", pk=prompt.pk)


class DashboardLabelSetView(LoginRequiredMixin, DashboardStaffRequiredMixin, View):
    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        prompt = get_object_or_404(Prompt, pk=pk)
        label_name = request.POST.get("name", "").strip()
        ver_num = int(request.POST.get("version_number", 0))

        if not label_name:
            messages.error(request, "Label name is required.")
            return redirect(f"/dashboard/prompts/{prompt.pk}/?version={ver_num}")

        try:
            lbl = set_custom_label(prompt, label_name, ver_num)
            messages.success(request, f"Label '{lbl.name}' set to v{ver_num}.")
        except ValueError as ve:
            messages.error(request, str(ve))
        except Exception as e:
            messages.error(request, f"Failed to set label: {e}")

        return redirect(f"/dashboard/prompts/{prompt.pk}/?version={ver_num}")


class DashboardLabelRemoveView(LoginRequiredMixin, DashboardStaffRequiredMixin, View):
    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        prompt = get_object_or_404(Prompt, pk=pk)
        label_name = request.POST.get("name", "").strip()
        try:
            remove_custom_label(prompt, label_name)
            messages.info(request, f"Label '{label_name}' removed.")
        except ValueError as ve:
            messages.error(request, str(ve))
        except Exception as e:
            messages.error(request, f"Failed to remove label: {e}")

        return redirect("dashboard-prompt-detail", pk=prompt.pk)
