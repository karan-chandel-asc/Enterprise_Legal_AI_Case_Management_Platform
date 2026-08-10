from django.conf import settings
from django.db import models


class AnalyticsEvent(models.Model):
    """Visitor / demo-interest event used to build journey emails.

    Tuned for portfolio/Upwork demos: know if someone visited, where they
    came from, and what flow they tried (login → dashboard → cases → chat).
    """

    STATUS_CHOICES = [
        ("started", "Started"),
        ("succeeded", "Succeeded"),
        ("failed", "Failed"),
        ("info", "Info"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="analytics_events",
    )
    email = models.EmailField(blank=True, default="")
    visitor_id = models.CharField(max_length=64, blank=True, default="", db_index=True)
    referrer = models.CharField(max_length=500, blank=True, default="")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    location = models.CharField(max_length=120, blank=True, default="")
    event_name = models.CharField(max_length=80, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="info", db_index=True)
    page = models.CharField(max_length=120, blank=True, default="")
    source = models.CharField(max_length=40, blank=True, default="backend")  # backend | frontend
    message = models.CharField(max_length=255, blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["event_name", "created_at"]),
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["visitor_id", "created_at"]),
        ]

    def __str__(self):
        return f"{self.event_name} ({self.status}) @ {self.created_at:%Y-%m-%d %H:%M}"
