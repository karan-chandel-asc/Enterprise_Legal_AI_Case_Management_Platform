from django.utils import timezone
from django.utils.timesince import timesince
from rest_framework import serializers

from case_management.models import Case, Hearing
from chatbot.models import ChatMessage


class RecentCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Case
        fields = ['id', 'case_id', 'case_title', 'case_type', 'case_status', 'court_name', 'hearing_date']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['hearing_date'] = instance.hearing_date.strftime("%b %d, %Y") if instance.hearing_date else None
        return data


class UpcomingHearingSerializer(serializers.ModelSerializer):
    case_id = serializers.IntegerField(source='case.id')
    case_title = serializers.CharField(source='case.case_title')

    class Meta:
        model = Hearing
        fields = ['id', 'case_id', 'case_title', 'hearing_date', 'hearing_time', 'court_name', 'status']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['hearing_date'] = instance.hearing_date.strftime("%Y-%m-%d")
        data['hearing_time'] = instance.hearing_time.strftime("%I:%M %p") if instance.hearing_time else "Time TBD"
        return data


class RecentAiChatSerializer(serializers.ModelSerializer):
    case_id = serializers.IntegerField(source="case.id")
    case_title = serializers.CharField(source="case.case_title")

    class Meta:
        model = ChatMessage
        fields = ["id", "case_id", "case_title", "content", "created_at"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        query = (instance.content or "").strip()
        if len(query) > 90:
            query = query[:87].rstrip() + "..."
        data["query"] = query
        data["time"] = f"{timesince(instance.created_at, timezone.now()).split(',')[0]} ago"
        data["created_at"] = instance.created_at.isoformat()
        data.pop("content", None)
        return data
