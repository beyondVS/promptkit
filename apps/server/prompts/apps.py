"""
App configuration for prompts registry app.
"""

from django.apps import AppConfig


class PromptsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.server.prompts"
    label = "prompts"
