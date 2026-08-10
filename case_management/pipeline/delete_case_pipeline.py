from case_management.pipeline.base_pipeline import BasePipeline
from case_management.services.db_mechanism import DbMechanism
from Enterprise_Legal_AI_Case_Management_Platform.logger import logger


class DeleteCasePipeline(BasePipeline):
    def __init__(self, request, case_id):
        self.request = request
        self.case_id = case_id
        self.db_mechanism = DbMechanism()

    def process_item(self):
        try:
            return self.db_mechanism.delete_case(self.request, self.case_id)
        except Exception as e:
            logger.error(f"Error in DeleteCasePipeline: {e}")
            return False, f"Error deleting case: {e}", None
