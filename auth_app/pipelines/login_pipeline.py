from auth_app.pipelines.base_pipeline import BasePipeline
from auth_app.services.authentication import AuthenticationService
from auth_app.services.otp_service import OtpService
from Enterprise_Legal_AI_Case_Management_Platform.logger import logger


class LoginPipeline(BasePipeline):
    def __init__(self):
        self.authentication_service = AuthenticationService()
        self.otp_service = OtpService()

    def process_item(self, data):
        """Returns (success, message, user). When MFA_LOGIN_ENABLED is False,
        the caller (view) can log the returned user in immediately. When it's
        True, an OTP has been sent instead and the user is not yet returned."""
        try:
            credentials_valid, message, user = self.authentication_service.authenticate_user(
                data['email'], data['password']
            )
            if not credentials_valid:
                return False, message, None

            # MFA when the user enabled it on Profile, or when the global
            # MFA_LOGIN_ENABLED kill-switch is forced on for everyone.
            from auth_app.feature_flags import MFA_LOGIN_ENABLED
            if MFA_LOGIN_ENABLED or getattr(user, "mfa_enabled", False):
                self.otp_service.generate_otp(purpose="mfa", email=user.email)
                return True, "OTP sent to your registered email.", None

            return True, "Login successful", user
        except Exception as e:
            logger.error(f"Error in LoginPipeline: {e}")
            return False, f"Error in LoginPipeline: {e}", None
