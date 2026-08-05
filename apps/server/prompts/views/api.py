"""
SDK Read-Only Fetch API View.
Authenticated via X-PromptKit-Api-Key Header.
Strictly Read-only (GET only).
"""

from django.shortcuts import get_object_or_404
from rest_framework import status as http_status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.server.prompts.auth import PromptKitAPIKeyAuthentication
from apps.server.prompts.models import Label, Prompt, Version
from apps.server.prompts.serializers import SDKPromptFetchResponseSerializer


class SDKPromptFetchAPIView(APIView):  # type: ignore[misc]
    """
    SDK Read-only API Endpoint to fetch prompt by slug and label.
    Supports GET method only. Disallows POST, PUT, PATCH, DELETE.
    """

    authentication_classes = [PromptKitAPIKeyAuthentication]

    def get(self, request: Request, slug: str) -> Response:
        """
        Fetch published prompt template and configuration by slug.
        Omitted label resolves to on-live published version.
        Explicit label resolves to the published version targeted by that label.
        'production' label is prohibited.
        """
        label_param = request.query_params.get("label")

        if label_param and label_param.strip().lower() == "production":
            return Response(
                {
                    "error": "invalid_label",
                    "detail": "'production' is not a valid label.",
                },
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        prompt = get_object_or_404(Prompt, slug=slug)

        if not label_param:
            version = prompt.versions.filter(
                is_on_live=True, status=Version.Status.PUBLISHED
            ).first()
            if not version:
                return Response(
                    {
                        "error": "no_deployable_version",
                        "detail": f"Prompt '{slug}' has no on-live published version.",
                    },
                    status=http_status.HTTP_404_NOT_FOUND,
                )
            selected_label = None
        else:
            lbl = (
                Label.objects.filter(prompt=prompt, name=label_param)
                .select_related("version")
                .first()
            )
            if not lbl or lbl.version.status != Version.Status.PUBLISHED:
                return Response(
                    {
                        "error": "label_not_found",
                        "detail": f"Prompt '{slug}' with label '{label_param}' was not found.",
                    },
                    status=http_status.HTTP_404_NOT_FOUND,
                )
            version = lbl.version
            selected_label = lbl.name

        data = {
            "slug": prompt.slug,
            "name": prompt.name,
            "description": prompt.description,
            "prompt": prompt,
            "version_number": version.version_number,
            "status": version.status,
            "is_on_live": version.is_on_live,
            "version": version,
            "label": selected_label,
            "template_text": version.template_text,
            "created_at": version.created_at,
        }

        serializer = SDKPromptFetchResponseSerializer(data)
        return Response(serializer.data)
