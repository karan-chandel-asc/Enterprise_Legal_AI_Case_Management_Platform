from django.contrib import admin
from .models import Case, CaseDocuments, CaseNotes


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ['case_title', 'case_type', 'case_status', 'client_name', 'opposing_party_name', 'court_name', 'hearing_date']


admin.site.register(CaseDocuments)
admin.site.register(CaseNotes)
