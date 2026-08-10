from case_management.pipeline.base_pipeline import BasePipeline
from case_management.services.note_service import NoteService
from Enterprise_Legal_AI_Case_Management_Platform.logger import logger


class UpdateNotePipeline(BasePipeline):
    def __init__(self, request, case_id, note_id, schema):
        self.request = request
        self.case_id = case_id
        self.note_id = note_id
        self.schema = schema
        self.note_service = NoteService()

    def process_item(self):
        try:
            return self.note_service.update_note(self.request, self.case_id, self.note_id, self.schema)
        except Exception as e:
            logger.error(f"Error in UpdateNotePipeline: {e}")
            return False, f"Error updating note: {e}", None
