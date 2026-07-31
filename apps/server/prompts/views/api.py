"""
SDK Read-Only Fetch API View.
Authenticated via X-PromptKit-Api-Key Header.
Strictly Read-only (GET only).
"""

from django.shortcuts import get_object_or_404
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.server.prompts.auth import PromptKitAPIKeyAuthentication
from apps.server.prompts.models import Label, Prompt
from apps.server.prompts.serializers import SDKPromptFetchResponseSerializer


class SDKPromptFetchAPIView(APIView):  # type: ignore[misc]
    """
    SDK Read-only API Endpoint to fetch prompt by slug and label.
    Supports GET method only. Disallows POST, PUT, PATCH, DELETE.
    """

    authentication_classes = [PromptKitAPIKeyAuthentication]

    def get(self, request: Request, slug: str) -> Response:
        """
        Fetch prompt template and configuration by slug and label.
        Query params: ?label=production (default: production)
        """
        label_name = request.query_params.get("label", "production")

        prompt = get_object_or_404(Prompt, slug=slug)

        label = (
            Label.objects.filter(prompt=prompt, name=label_name).select_related("version").first()
        )
        if not label:
            return Response(
                {
                    "error": "not_found",
                    "detail": f"Prompt '{slug}' with label '{label_name}' not found",
                },
                status=404,
            )

        version = label.version
        data = {
            "slug": prompt.slug,
            "name": prompt.name,
            "prompt": prompt,
            "version_number": version.version_number,
            "version": version,
            "label": label_name,
            "template_text": version.template_text,
            "created_at": version.created_at,
        }

        serializer = SDKPromptFetchResponseSerializer(data)
        return Response(serializer.data)
