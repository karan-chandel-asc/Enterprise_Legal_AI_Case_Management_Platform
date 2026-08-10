from rest_framework import serializers
from .models import Case, CaseDocuments, CaseNotes, Hearing

class CaseListSerializer(serializers.ModelSerializer):
    document_count = serializers.SerializerMethodField()

    class Meta:
        model = Case
        fields = [
            'id',
            'case_id',
            'case_title',
            'case_type',
            'case_status',
            'client_name',
            'opposing_party_name',
            'court_name',
            'hearing_date',
            'case_description',
            'document_count',
        ]

    def get_document_count(self, obj):
        return obj.documents.count()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.hearing_date:
            data['hearing_date'] = instance.hearing_date.strftime("%b %d, %Y")
        else:
            data['hearing_date'] = None
        return data


class CaseDetailSerializer(serializers.ModelSerializer):
    document_count = serializers.SerializerMethodField()
    note_count = serializers.SerializerMethodField()

    class Meta:
        model = Case
        fields = [
            'id',
            'case_id',
            'case_title',
            'case_type',
            'case_status',
            'client_name',
            'opposing_party_name',
            'court_name',
            'hearing_date',
            'case_description',
            'document_count',
            'note_count',
            'case_created_at',
            'case_updated_at',
        ]

    def get_document_count(self, obj):
        return obj.documents.count()

    def get_note_count(self, obj):
        return obj.notes.count()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['hearing_date'] = instance.hearing_date.strftime("%b %d, %Y") if instance.hearing_date else None
        data['case_created_at'] = instance.case_created_at.strftime("%b %d, %Y")
        data['case_updated_at'] = instance.case_updated_at.strftime("%b %d, %Y \u00b7 %I:%M %p")
        return data


class CaseDocumentSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    file_type = serializers.SerializerMethodField()

    class Meta:
        model = CaseDocuments
        fields = [
            'id', 'document_name', 'file_url', 'file_type', 'file_size', 'uploaded_at',
            'embedding_status', 'chunk_count',
        ]

    def get_file_url(self, obj):
        if not obj.document_file:
            return None
        request = self.context.get('request')
        url = obj.document_file.url
        return request.build_absolute_uri(url) if request else url

    def get_file_type(self, obj):
        name = obj.document_name or ""
        ext = name.rsplit('.', 1)[-1].lower() if '.' in name else ""
        if ext in ('jpg', 'jpeg', 'png', 'gif', 'webp'):
            return 'img'
        if ext in ('doc', 'docx'):
            return 'docx'
        if ext == 'pdf':
            return 'pdf'
        return ext or 'file'

    def to_representation(self, instance):
        data = super().to_representation(instance)
        size = instance.file_size or 0
        if size >= 1024 * 1024:
            data['file_size'] = f"{size / (1024 * 1024):.1f} MB"
        elif size:
            data['file_size'] = f"{size / 1024:.0f} KB"
        else:
            data['file_size'] = "—"
        data['uploaded_at'] = instance.uploaded_at.strftime("%b %d, %Y")
        return data


class CaseNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseNotes
        fields = ['id', 'note_title', 'note_content', 'note_created_at', 'note_updated_at']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['note_created_at'] = instance.note_created_at.strftime("%b %d, %Y \u00b7 %I:%M %p")
        data['note_updated_at'] = instance.note_updated_at.strftime("%b %d, %Y \u00b7 %I:%M %p")
        data['ai'] = False
        return data


class HearingSerializer(serializers.ModelSerializer):
    case_id = serializers.IntegerField(source='case.id')
    case_title = serializers.CharField(source='case.case_title')
    case_number = serializers.CharField(source='case.case_id')

    class Meta:
        model = Hearing
        fields = [
            'id', 'case_id', 'case_title', 'case_number', 'hearing_date', 'hearing_time',
            'court_name', 'judge_name', 'status', 'notes',
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['hearing_date'] = instance.hearing_date.strftime("%Y-%m-%d")
        data['hearing_time'] = instance.hearing_time.strftime("%I:%M %p") if instance.hearing_time else None
        return data