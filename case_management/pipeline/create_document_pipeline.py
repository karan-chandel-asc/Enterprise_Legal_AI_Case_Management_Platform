from case_management.pipeline.base_pipeline import BasePipeline
from case_management.services.document_service import DocumentService
from Enterprise_Legal_AI_Case_Management_Platform.logger import logger


class CreateDocumentPipeline(BasePipeline):
    def __init__(self, request, case_id, file_obj, document_name=None):
        self.request = request
        self.case_id = case_id
        self.file_obj = file_obj
        self.document_name = document_name
        self.document_service = DocumentService()

    def process_item(self):
        try:
            return self.document_service.create_document(
                self.request, self.case_id, self.file_obj, self.document_name
            )
        except Exception as e:
            logger.error(f"Error in CreateDocumentPipeline: {e}")
            return False, f"Error uploading document: {e}", None
