from case_management.pipeline.base_pipeline import BasePipeline
from case_management.services.note_service import NoteService
from Enterprise_Legal_AI_Case_Management_Platform.logger import logger


class NoteListPipeline(BasePipeline):
    def __init__(self, request, case_id):
        self.request = request
        self.case_id = case_id
        self.note_service = NoteService()

    def process_item(self):
        try:
            return self.note_service.list_notes(self.request, self.case_id)
        except Exception as e:
            logger.error(f"Error in NoteListPipeline: {e}")
            return False, f"Error getting notes: {e}", None
