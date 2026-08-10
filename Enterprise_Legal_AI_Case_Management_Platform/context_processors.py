from django.conf import settings


def chatbot_settings(request):
    """Expose chatbot API base URL to templates (local :8001 or /ai via nginx)."""
    return {
        "CHATBOT_API_BASE_URL": getattr(
            settings, "CHATBOT_API_BASE_URL", "http://127.0.0.1:8001"
        ).rstrip("/"),
    }
