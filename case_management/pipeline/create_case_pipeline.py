from case_management.pipeline.base_pipeline import BasePipeline
from case_management.services.db_mechanism import DbMechanism
from Enterprise_Legal_AI_Case_Management_Platform.logger import logger


class CreateCasePipeline(BasePipeline):
    def __init__(self, request, schema):
        self.request = request
        self.schema = schema
        self.db_mechanism = DbMechanism()

    def process_item(self):
        try:
            success, message, result = self.db_mechanism.create_case(self.request, self.schema)
            return success, message, result
        except Exception as e:
            logger.error(f"Error in CreateCasePipeline: {e}")
            return False, f"Error creating case: {e}", None
