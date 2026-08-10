from django.conf import settings

from auth_app.pipelines.base_pipeline import BasePipeline
from auth_app.services.authentication import AuthenticationService
from auth_app.tasks import send_password_reset_email
from Enterprise_Legal_AI_Case_Management_Platform.logger import logger


class ForgotPasswordPipeline(BasePipeline):
    def __init__(self):
        self.authentication_service = AuthenticationService()

    def process_item(self, data):
        """`data['reset_base_url']` is the absolute URL of the reset-password
        page (built by the view from the request), so the emailed link
        works regardless of host/port."""
        try:
            user = self.authentication_service.get_user_by_email(data['email'])
            if user:
                uidb64, token = self.authentication_service.generate_password_reset_token(user)
                reset_link = f"{data['reset_base_url']}?uid={uidb64}&token={token}"
                logger.info(f"[PasswordReset] email={user.email} link={reset_link}")
                try:
                    ttl_minutes = settings.PASSWORD_RESET_TIMEOUT // 60
                    send_password_reset_email.delay(email=user.email, reset_link=reset_link, ttl_minutes=ttl_minutes)
                except Exception as e:
                    # Broker (Redis) unreachable, worker down, etc. The link is
                    # still valid and logged above — never let a delivery
                    # hiccup block the forgot-password flow itself.
                    logger.error(f"[PasswordReset email] could not queue send for email={user.email}: {e}")

            # Always respond the same way, whether or not the email exists,
            # so we don't leak which emails are registered.
            return True, "If an account with that email exists, a reset link has been sent.", None
        except Exception as e:
            logger.error(f"Error in ForgotPasswordPipeline: {e}")
            return False, f"Error in ForgotPasswordPipeline: {e}", None
