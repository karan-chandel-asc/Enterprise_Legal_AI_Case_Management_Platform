from auth_app.pipelines.base_pipeline import BasePipeline
from auth_app.services.authentication import AuthenticationService
from auth_app.services.otp_service import OtpService
from Enterprise_Legal_AI_Case_Management_Platform.logger import logger


class VerifyEmailPipeline(BasePipeline):
    def __init__(self):
        self.authentication_service = AuthenticationService()
        self.otp_service = OtpService()

    def process_item(self, data):
        try:
            otp_valid, message = self.otp_service.verify_otp(
                purpose="verify_email", email=data['email'], code=data['otp']
            )
            if not otp_valid:
                return False, message, None

            success, message = self.authentication_service.mark_email_verified(data['email'])
            return success, message, None
        except Exception as e:
            logger.error(f"Error in VerifyEmailPipeline: {e}")
            return False, f"Error in VerifyEmailPipeline: {e}", None
