from case_management.pipeline.base_pipeline import BasePipeline
from case_management.services.hearing_service import HearingService
from Enterprise_Legal_AI_Case_Management_Platform.logger import logger


class HearingListPipeline(BasePipeline):
    def __init__(self, request, filters):
        self.request = request
        self.filters = filters
        self.hearing_service = HearingService()

    def process_item(self):
        try:
            hearings = self.hearing_service.list_hearings(self.request, self.filters)
            return True, "Hearings fetched successfully", hearings
        except Exception as e:
            logger.error(f"Error in HearingListPipeline: {e}")
            return False, f"Error getting hearings: {e}", None
