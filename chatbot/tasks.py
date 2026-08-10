from celery import shared_task
from django.utils import timezone

from Enterprise_Legal_AI_Case_Management_Platform.logger import logger
from case_management.models import CaseDocuments


def _mark_failed(document: CaseDocuments, error_message: str) -> None:
    document.embedding_status = "failed"
    document.embedding_error = (error_message or "")[:500]
    document.save(update_fields=["embedding_status", "embedding_error"])


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def process_document_embedding(self, document_id: int):
    """Background knowledge-base indexing pipeline for one uploaded case document.

    load file -> split into chunks -> embed -> upsert to Pinecone.

    Heavy langchain imports stay inside this function so Django's request
    path can queue the task with `.delay()` without loading langsmith.
    """
    # Lazy imports — only the Celery worker pays this cost.
    from chatbot.services.chunking import ChunkingService
    from chatbot.services.loaders import LoaderService
    from chatbot.services.vector_storage import PineconeService

    try:
        document = CaseDocuments.objects.select_related("case").get(id=document_id)
    except CaseDocuments.DoesNotExist:
        logger.error(f"[Embedding] Document {document_id} not found, skipping")
        return

    if not document.document_file:
        _mark_failed(document, "No file attached to this document")
        return

    document.embedding_status = "processing"
    document.save(update_fields=["embedding_status"])

    try:
        loaded, message, pages = LoaderService().load_document(document.document_file.path)
        if not loaded:
            _mark_failed(document, message)
            return

        chunks_meta = []
        for page_number, page in enumerate(pages, start=1):
            page_text = getattr(page, "page_content", "") or ""
            if not page_text.strip():
                continue
            metadata = getattr(page, "metadata", None) or {}
            chunks, _ = ChunkingService(page_text).chunk_text()
            for chunk in chunks:
                chunks_meta.append({"text": chunk, "page": metadata.get("page", page_number)})

        if not chunks_meta:
            _mark_failed(document, "No extractable text found in this document")
            return

        vector_count = PineconeService().index_document(
            doc_id=str(document.id),
            doc_name=document.document_name,
            chunks_meta=chunks_meta,
        )

        document.embedding_status = "completed"
        document.chunk_count = vector_count
        document.embedding_error = ""
        document.embedded_at = timezone.now()
        document.save(update_fields=["embedding_status", "chunk_count", "embedding_error", "embedded_at"])
        logger.info(f"[Embedding] Document {document_id} indexed with {vector_count} vectors")
        try:
            from analytics.services import AnalyticsService
            owner = getattr(document.case, "user", None)
            AnalyticsService.track(
                "embedding.completed",
                user=owner,
                status="succeeded",
                page="embedding",
                metadata={"document_id": document_id, "vector_count": vector_count},
            )
        except Exception:
            pass

    except Exception as e:
        logger.error(f"[Embedding] Failed processing document {document_id}: {e}")
        _mark_failed(document, str(e))
        try:
            from analytics.services import AnalyticsService
            owner = getattr(document.case, "user", None)
            AnalyticsService.track(
                "embedding.failed",
                user=owner,
                status="failed",
                page="embedding",
                message=str(e)[:255],
                metadata={"document_id": document_id},
            )
        except Exception:
            pass
        raise self.retry(exc=e)
