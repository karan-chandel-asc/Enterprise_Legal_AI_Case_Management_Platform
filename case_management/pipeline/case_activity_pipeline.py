from case_management.pipeline.base_pipeline import BasePipeline
from case_management.services.activity_service import ActivityService
from Enterprise_Legal_AI_Case_Management_Platform.logger import logger


class CaseActivityPipeline(BasePipeline):
    def __init__(self, request, case_id):
        self.request = request
        self.case_id = case_id
        self.activity_service = ActivityService()

    def process_item(self):
        try:
            return self.activity_service.get_case_activity(self.request, self.case_id)
        except Exception as e:
            logger.error(f"Error in CaseActivityPipeline: {e}")
            return False, f"Error getting activity: {e}", None
