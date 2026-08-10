from case_management.pipeline.base_pipeline import BasePipeline
from case_management.services.note_service import NoteService
from Enterprise_Legal_AI_Case_Management_Platform.logger import logger


class CreateNotePipeline(BasePipeline):
    def __init__(self, request, case_id, schema):
        self.request = request
        self.case_id = case_id
        self.schema = schema
        self.note_service = NoteService()

    def process_item(self):
        try:
            return self.note_service.create_note(self.request, self.case_id, self.schema)
        except Exception as e:
            logger.error(f"Error in CreateNotePipeline: {e}")
            return False, f"Error creating note: {e}", None
