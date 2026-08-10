from auth_app.pipelines.base_pipeline import BasePipeline
from auth_app.services.authentication import AuthenticationService
from Enterprise_Legal_AI_Case_Management_Platform.logger import logger


class ResetPasswordPipeline(BasePipeline):
    def __init__(self):
        self.authentication_service = AuthenticationService()

    def process_item(self, data):
        try:
            user = self.authentication_service.validate_password_reset_token(data['uid'], data['token'])
            if not user:
                return False, "This reset link is invalid or has expired.", None

            success, message = self.authentication_service.update_password(user, data['password'])
            return success, message, None
        except Exception as e:
            logger.error(f"Error in ResetPasswordPipeline: {e}")
            return False, f"Error in ResetPasswordPipeline: {e}", None
