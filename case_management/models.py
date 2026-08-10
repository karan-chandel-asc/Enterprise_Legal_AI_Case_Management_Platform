from django.db import models
from auth_app.models import User

# Create your models here.

class Case(models.Model):
  case_type_choices = [
    ('civil', 'Civil'),
    ('criminal', 'Criminal'),
    ('family', 'Family'),
    ('corporate', 'Corporate'),
  ]
  # "Hearing" used to be a case-level status, but a case can have several
  # hearings over its lifetime (see the Hearing model below), so tracking
  # it here didn't make sense. Whether a case has an upcoming hearing is
  # now derived from its related Hearing rows instead.
  case_status_choices = [
    ('active', 'Active'),
    ('closed', 'Closed'),
  ]
  user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cases')
  case_type = models.CharField(max_length=255, choices=case_type_choices)
  case_id = models.CharField(max_length=255, unique=True)
  case_title = models.CharField(max_length=255)
  case_status=models.CharField(max_length=255, choices=case_status_choices)
  client_name = models.CharField(max_length=255)
  opposing_party_name = models.CharField(max_length=255)
  court_name = models.CharField(max_length=255)
  hearing_date = models.DateField()
  case_description = models.TextField()
  case_created_at = models.DateTimeField(auto_now_add=True)
  case_updated_at = models.DateTimeField(auto_now=True)

class CaseDocuments(models.Model):
  embedding_status_choices = [
    ('pending', 'Pending'),
    ('processing', 'Processing'),
    ('completed', 'Completed'),
    ('failed', 'Failed'),
  ]
  case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='documents')
  document_name = models.CharField(max_length=255)
  document_file = models.FileField(upload_to='case_documents/%Y/%m/', blank=True, null=True)
  file_size = models.PositiveIntegerField(default=0)
  uploaded_at = models.DateTimeField(auto_now_add=True)

  # AI knowledge-base indexing status (chatbot app chunks + embeds + upserts
  # this document into Pinecone via a Celery background task)
  embedding_status = models.CharField(max_length=20, choices=embedding_status_choices, default='pending')
  embedding_error = models.TextField(blank=True)
  chunk_count = models.PositiveIntegerField(default=0)
  embedded_at = models.DateTimeField(null=True, blank=True)

class CaseNotes(models.Model):
  case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='notes')
  note_title = models.CharField(max_length=255)
  note_content = models.TextField()
  note_created_at = models.DateTimeField(auto_now_add=True)
  note_updated_at = models.DateTimeField(auto_now=True)

class Hearing(models.Model):
  status_choices = [
    ('confirmed', 'Confirmed'),
    ('urgent', 'Urgent'),
    ('completed', 'Completed'),
    ('cancelled', 'Cancelled'),
  ]
  case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='hearings')
  hearing_date = models.DateField()
  hearing_time = models.TimeField(null=True, blank=True)
  court_name = models.CharField(max_length=255, blank=True)
  judge_name = models.CharField(max_length=255, blank=True)
  status = models.CharField(max_length=20, choices=status_choices, default='confirmed')
  notes = models.TextField(blank=True)
  hearing_created_at = models.DateTimeField(auto_now_add=True)
  hearing_updated_at = models.DateTimeField(auto_now=True)

  class Meta:
    ordering = ['hearing_date', 'hearing_time']
