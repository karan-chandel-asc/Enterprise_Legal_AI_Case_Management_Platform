from auth_app.feature_flags import EMAIL_VERIFICATION_ENABLED
from auth_app.pipelines.base_pipeline import BasePipeline
from auth_app.services.authentication import AuthenticationService
from auth_app.services.otp_service import OtpService
from Enterprise_Legal_AI_Case_Management_Platform.logger import logger


class RegisterUserPipeline(BasePipeline):
    def __init__(self):
        self.authentication_service = AuthenticationService()
        self.otp_service = OtpService()

    def process_item(self, data):
        """Returns (success, message, payload). payload["requires_verification"]
        tells the caller (view) whether to route the user to the OTP page or
        straight to login, based on EMAIL_VERIFICATION_ENABLED."""
        try:
            email_exists, message = self.authentication_service.check_email_already_exists(data['email'])
            if email_exists:
                return False, message, None

            user_registered, message = self.authentication_service.register_user(data)
            if not user_registered:
                return False, message, None

            if not EMAIL_VERIFICATION_ENABLED:
                self.authentication_service.mark_email_verified(data['email'])
                return True, "Account created successfully. You can now log in.", {"requires_verification": False}

            self.otp_service.generate_otp(purpose="verify_email", email=data['email'])
            return True, "Account created. Check your email for the verification code.", {"requires_verification": True}
        except Exception as e:
            logger.error(f"Error in RegisterUserPipeline: {e}")
            return False, f"Error in RegisterUserPipeline: {e}", None
