from case_management.pipeline.base_pipeline import BasePipeline
from case_management.services.db_mechanism import DbMechanism
from Enterprise_Legal_AI_Case_Management_Platform.logger import logger


class UpdateCasePipeline(BasePipeline):
    def __init__(self, request, case_id, schema):
        self.request = request
        self.case_id = case_id
        self.schema = schema
        self.db_mechanism = DbMechanism()

    def process_item(self):
        try:
            return self.db_mechanism.update_case(self.request, self.case_id, self.schema)
        except Exception as e:
            logger.error(f"Error in UpdateCasePipeline: {e}")
            return False, f"Error updating case: {e}", None
