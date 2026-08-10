from case_management.pipeline.base_pipeline import BasePipeline
from case_management.services.hearing_service import HearingService
from Enterprise_Legal_AI_Case_Management_Platform.logger import logger


class DeleteHearingPipeline(BasePipeline):
    def __init__(self, request, hearing_id):
        self.request = request
        self.hearing_id = hearing_id
        self.hearing_service = HearingService()

    def process_item(self):
        try:
            return self.hearing_service.delete_hearing(self.request, self.hearing_id)
        except Exception as e:
            logger.error(f"Error in DeleteHearingPipeline: {e}")
            return False, f"Error deleting hearing: {e}", None
