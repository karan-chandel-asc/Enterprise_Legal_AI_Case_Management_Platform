from case_management.pipeline.base_pipeline import BasePipeline
from case_management.services.hearing_service import HearingService
from Enterprise_Legal_AI_Case_Management_Platform.logger import logger


class CreateHearingPipeline(BasePipeline):
    def __init__(self, request, schema):
        self.request = request
        self.schema = schema
        self.hearing_service = HearingService()

    def process_item(self):
        try:
            return self.hearing_service.create_hearing(self.request, self.schema)
        except Exception as e:
            logger.error(f"Error in CreateHearingPipeline: {e}")
            return False, f"Error scheduling hearing: {e}", None
