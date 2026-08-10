from django.db import models

from case_management.models import Case


class ChatMessage(models.Model):
    """One turn in a case's AI Assistant conversation.

    Persisted so the chat panel survives page reloads and so the RAG graph
    can feed recent turns back in as conversational context.
    """
    role_choices = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
    ]
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='chat_messages')
    role = models.CharField(max_length=10, choices=role_choices)
    content = models.TextField()
    # [{"doc_name": str, "page": int, "score": float}, ...] — populated only
    # on assistant turns, straight from the retriever node's top matches.
    citations = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
