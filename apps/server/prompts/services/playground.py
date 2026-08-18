"""Map dashboard ORM snapshots to the public PromptKit compile contract."""

from collections.abc import Mapping

from django.db.models import Prefetch, QuerySet
from promptkit import (
    CompiledPrompt,
    PromptSection,
    PromptVariable,
    RetrievedPrompt,
)
from promptkit import (
    PromptCategory as SDKPromptCategory,
)

from apps.server.prompts.models import Section, VariableDefinition, Version


def playground_version_queryset() -> QuerySet[Version]:
    """Return versions with every relation needed for one compile request."""
    return Version.objects.select_related("prompt__category").prefetch_related(
        Prefetch("variables", queryset=VariableDefinition.objects.order_by("name")),
        Prefetch("sections", queryset=Section.objects.order_by("order")),
    )


def to_retrieved_prompt(version: Version) -> RetrievedPrompt:
    """Create a transient public SDK model from an explicitly selected version."""
    prompt = version.prompt
    return RetrievedPrompt(
        slug=prompt.slug,
        name=prompt.name,
        description=prompt.description,
        category=SDKPromptCategory(name=prompt.category.name, slug=prompt.category.slug),
        version=version.version_number,
        version_status=version.status,
        is_on_live=version.is_on_live,
        label=None,
        template_text=version.template_text,
        variables=[
            PromptVariable(
                name=variable.name,
                var_type=variable.var_type,
                required=variable.required,
                default_value=variable.default_value,
                description=variable.description,
            )
            for variable in version.variables.all()
        ],
        sections=[
            PromptSection(role=section.role, order=section.order, content=section.content)
            for section in version.sections.all()
        ],
        created_at=version.created_at,
    )


def compile_playground_version(
    version: Version,
    params: Mapping[str, object],
) -> CompiledPrompt:
    """Compile one selected ORM snapshot exactly once through the public SDK."""
    return to_retrieved_prompt(version).compile(params)
