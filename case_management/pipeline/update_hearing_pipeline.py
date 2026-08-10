from case_management.pipeline.base_pipeline import BasePipeline
from case_management.services.hearing_service import HearingService
from Enterprise_Legal_AI_Case_Management_Platform.logger import logger


class UpdateHearingPipeline(BasePipeline):
    def __init__(self, request, hearing_id, schema):
        self.request = request
        self.hearing_id = hearing_id
        self.schema = schema
        self.hearing_service = HearingService()

    def process_item(self):
        try:
            return self.hearing_service.update_hearing(self.request, self.hearing_id, self.schema)
        except Exception as e:
            logger.error(f"Error in UpdateHearingPipeline: {e}")
            return False, f"Error updating hearing: {e}", None
