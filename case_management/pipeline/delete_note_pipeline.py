from case_management.pipeline.base_pipeline import BasePipeline
from case_management.services.note_service import NoteService
from Enterprise_Legal_AI_Case_Management_Platform.logger import logger


class DeleteNotePipeline(BasePipeline):
    def __init__(self, request, case_id, note_id):
        self.request = request
        self.case_id = case_id
        self.note_id = note_id
        self.note_service = NoteService()

    def process_item(self):
        try:
            return self.note_service.delete_note(self.request, self.case_id, self.note_id)
        except Exception as e:
            logger.error(f"Error in DeleteNotePipeline: {e}")
            return False, f"Error deleting note: {e}", None
