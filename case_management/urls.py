from django.urls import path
from . import views

urlpatterns = [
    # Pages
    path('cases/', views.cases_list_page, name='cases_list'),
    path('cases/<int:case_id>/', views.case_detail_page, name='case_detail'),
    path('hearings/', views.hearings_page, name='hearings'),

    # Case APIs
    path('cases-list-api/', views.CaseListApi.as_view(), name='cases_list_api'),
    path('cases-create-api/', views.CreateCaseApi.as_view(), name='cases_create_api'),
    path('cases/<int:case_id>/api/', views.CaseDetailApi.as_view(), name='case_detail_api'),

    # Document APIs
    path('cases/<int:case_id>/documents-api/', views.CaseDocumentsApi.as_view(), name='case_documents_api'),
    path('cases/<int:case_id>/documents-api/<int:document_id>/', views.CaseDocumentDetailApi.as_view(), name='case_document_detail_api'),

    # Note APIs
    path('cases/<int:case_id>/notes-api/', views.CaseNotesApi.as_view(), name='case_notes_api'),
    path('cases/<int:case_id>/notes-api/<int:note_id>/', views.CaseNoteDetailApi.as_view(), name='case_note_detail_api'),

    # Activity API
    path('cases/<int:case_id>/activity-api/', views.CaseActivityApi.as_view(), name='case_activity_api'),

    # Hearing APIs
    path('hearings-api/', views.HearingsApi.as_view(), name='hearings_api'),
    path('hearings-api/<int:hearing_id>/', views.HearingDetailApi.as_view(), name='hearing_detail_api'),
]
