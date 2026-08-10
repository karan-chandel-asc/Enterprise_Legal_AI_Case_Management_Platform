from django.urls import path

from analytics.views import TrackEventApi

urlpatterns = [
    path("api/analytics/events/", TrackEventApi.as_view(), name="analytics_track_event_api"),
]
