from auth_app.pipelines.base_pipeline import BasePipeline
from auth_app.services.authentication import AuthenticationService
from auth_app.services.otp_service import OtpService
from Enterprise_Legal_AI_Case_Management_Platform.logger import logger


class MfaVerifyPipeline(BasePipeline):
    def __init__(self):
        self.authentication_service = AuthenticationService()
        self.otp_service = OtpService()

    def process_item(self, data):
        """Returns (success, message, user) — the caller (view) is
        responsible for starting the Django session once verified."""
        try:
            otp_valid, message = self.otp_service.verify_otp(
                purpose="mfa", email=data['email'], code=data['otp']
            )
            if not otp_valid:
                return False, message, None

            user = self.authentication_service.get_user_by_email(data['email'])
            if not user:
                return False, "User not found", None
            return True, "Verified successfully", user
        except Exception as e:
            logger.error(f"Error in MfaVerifyPipeline: {e}")
            return False, f"Error in MfaVerifyPipeline: {e}", None
