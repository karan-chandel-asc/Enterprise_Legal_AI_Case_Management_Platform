from django.contrib import admin

from analytics.models import AnalyticsEvent


@admin.register(AnalyticsEvent)
class AnalyticsEventAdmin(admin.ModelAdmin):
    list_display = ("event_name", "status", "email", "page", "source", "created_at")
    list_filter = ("event_name", "status", "source", "created_at")
    search_fields = ("email", "event_name", "page", "message")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)
