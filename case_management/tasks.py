from celery import shared_task

from Enterprise_Legal_AI_Case_Management_Platform.logger import logger


@shared_task(bind=True, max_retries=2, default_retry_delay=15)
def delete_case_document(self, document_id: int, user_id: int):
    """Delete a case document in the background: vector index + file + DB row.

    Request path only validates ownership and queues this task so the API
    can return immediately ("deletion started in the background").
    """
    try:
        from case_management.models import CaseDocuments

        document = (
            CaseDocuments.objects.select_related("case")
            .filter(id=document_id, case__user_id=user_id)
            .first()
        )
        if not document:
            logger.info(f"[DocDelete] document {document_id} already gone or not owned by user {user_id}")
            return "missing"

        # Pinecone cleanup — imported lazily so Django request workers never
        # pull langchain/langsmith just to queue a delete.
        try:
            from chatbot.services.vector_storage import PineconeService
            PineconeService().delete_document(str(document_id))
        except Exception as e:
            logger.error(f"[DocDelete] Pinecone cleanup failed for {document_id}: {e}")

        if document.document_file:
            document.document_file.delete(save=False)

        document.delete()
        logger.info(f"[DocDelete] document {document_id} deleted for user {user_id}")
        return "deleted"
    except Exception as e:
        logger.error(f"[DocDelete] failed for document {document_id}: {e}")
        raise self.retry(exc=e)
