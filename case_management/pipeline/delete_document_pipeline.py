from case_management.pipeline.base_pipeline import BasePipeline
from case_management.services.document_service import DocumentService
from Enterprise_Legal_AI_Case_Management_Platform.logger import logger


class DeleteDocumentPipeline(BasePipeline):
    def __init__(self, request, case_id, document_id):
        self.request = request
        self.case_id = case_id
        self.document_id = document_id
        self.document_service = DocumentService()

    def process_item(self):
        try:
            return self.document_service.delete_document(self.request, self.case_id, self.document_id)
        except Exception as e:
            logger.error(f"Error in DeleteDocumentPipeline: {e}")
            return False, f"Error deleting document: {e}", None
