import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Enterprise_Legal_AI_Case_Management_Platform.settings")

app = Celery("Enterprise_Legal_AI_Case_Management_Platform")

# Read CELERY_* settings straight from Django's settings.py
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks.py in every installed app (chatbot/tasks.py, etc.)
app.autodiscover_tasks()
