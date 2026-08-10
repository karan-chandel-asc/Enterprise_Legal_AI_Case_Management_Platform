from case_management.pipeline.base_pipeline import BasePipeline
from case_management.services.document_service import DocumentService
from Enterprise_Legal_AI_Case_Management_Platform.logger import logger


class DocumentListPipeline(BasePipeline):
    def __init__(self, request, case_id):
        self.request = request
        self.case_id = case_id
        self.document_service = DocumentService()

    def process_item(self):
        try:
            return self.document_service.list_documents(self.request, self.case_id)
        except Exception as e:
            logger.error(f"Error in DocumentListPipeline: {e}")
            return False, f"Error getting documents: {e}", None
