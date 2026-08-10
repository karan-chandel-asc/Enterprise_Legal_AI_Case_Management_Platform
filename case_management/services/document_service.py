from pathlib import Path

from Enterprise_Legal_AI_Case_Management_Platform.logger import logger
from case_management.models import Case, CaseDocuments

ALLOWED_DOCUMENT_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt", ".csv"}
MAX_UPLOAD_BYTES = 25 * 1024 * 1024  # 25 MB


class DocumentService:
    def __init__(self):
        self.document_model = CaseDocuments
        self.case_model = Case

    def _get_owned_case(self, request, case_id):
        return self.case_model.objects.filter(user=request.user, id=case_id).first()

    def list_documents(self, request, case_id):
        try:
            case = self._get_owned_case(request, case_id)
            if not case:
                return False, "Case not found", None
            documents = case.documents.order_by('-uploaded_at')
            return True, "Documents fetched successfully", documents
        except Exception as e:
            logger.error(f"Error listing documents: {e}")
            raise

    def create_document(self, request, case_id, file_obj, document_name=None):
        """Save the file quickly, then queue indexing on Celery.

        The HTTP response returns immediately after the DB/file write — OCR /
        embeddings never block the upload request.
        """
        try:
            case = self._get_owned_case(request, case_id)
            if not case:
                return False, "Case not found", None
            if not file_obj:
                return False, "No file was uploaded", None

            extension = Path(file_obj.name).suffix.lower()
            if extension not in ALLOWED_DOCUMENT_EXTENSIONS:
                allowed = ', '.join(sorted(ALLOWED_DOCUMENT_EXTENSIONS))
                return False, f"Unsupported file type '{extension or 'unknown'}'. Allowed: {allowed}", None
            if file_obj.size > MAX_UPLOAD_BYTES:
                return False, "File exceeds the 25 MB upload limit", None

            document = self.document_model.objects.create(
                case=case,
                document_name=(document_name or file_obj.name).strip() or file_obj.name,
                document_file=file_obj,
                file_size=file_obj.size,
                embedding_status="pending",
            )
            self._enqueue_embedding(document.id)
            return True, "Document uploaded — indexing is running in the background", document
        except Exception as e:
            logger.error(f"Error uploading document: {e}")
            return False, f"Error uploading document: {e}", None

    def _enqueue_embedding(self, document_id):
        try:
            # Prefer send_task so we don't even need to import the task module
            # in the request worker (avoids accidental heavy imports).
            from Enterprise_Legal_AI_Case_Management_Platform.celery import app
            app.send_task("chatbot.tasks.process_document_embedding", args=[document_id])
        except Exception as e:
            logger.error(f"Error queueing embedding task for document {document_id}: {e}")

    def delete_document(self, request, case_id, document_id):
        """Validate ownership and queue deletion — return immediately."""
        try:
            case = self._get_owned_case(request, case_id)
            if not case:
                return False, "Case not found", None
            document = case.documents.filter(id=document_id).first()
            if not document:
                return False, "Document not found", None

            from case_management.tasks import delete_case_document
            delete_case_document.delay(document.id, request.user.id)
            return True, "Document deletion started in the background", {"id": document.id, "deleting": True}
        except Exception as e:
            logger.error(f"Error queueing document delete: {e}")
            return False, f"Error deleting document: {e}", None
