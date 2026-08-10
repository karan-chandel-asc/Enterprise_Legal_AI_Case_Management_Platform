from auth_app.pipelines.base_pipeline import BasePipeline
from auth_app.services.otp_service import OtpService
from Enterprise_Legal_AI_Case_Management_Platform.logger import logger


class ResendOtpPipeline(BasePipeline):
    def __init__(self):
        self.otp_service = OtpService()

    def process_item(self, data):
        try:
            self.otp_service.generate_otp(purpose=data['purpose'], email=data['email'])
            return True, "A new code has been sent.", None
        except Exception as e:
            logger.error(f"Error in ResendOtpPipeline: {e}")
            return False, f"Error in ResendOtpPipeline: {e}", None
