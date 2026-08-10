from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

from Enterprise_Legal_AI_Case_Management_Platform.logger import logger

OTP_EMAIL_SUBJECTS = {
    "verify_email": "Verify your Lexora account",
    "mfa": "Your Lexora sign-in code",
}


@shared_task(bind=True, max_retries=3, default_retry_delay=15)
def send_otp_email(self, purpose: str, email: str, code: str, ttl_minutes: int = 5):
    """Delivers a one-time code by email in the background so the request
    that triggered it (register/login/resend) never waits on SMTP."""
    subject = OTP_EMAIL_SUBJECTS.get(purpose, "Your Lexora verification code")
    message = (
        f"Your verification code is: {code}\n\n"
        f"This code expires in {ttl_minutes} minutes. "
        f"If you didn't request this, you can safely ignore this email."
    )
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        logger.info(f"[OTP email] purpose={purpose} sent to={email}")
    except Exception as e:
        logger.error(f"[OTP email] purpose={purpose} to={email} failed: {e}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=15)
def send_password_reset_email(self, email: str, reset_link: str, ttl_minutes: int = 30):
    """Delivers the password-reset link by email in the background."""
    subject = "Reset your Lexora password"
    message = (
        f"We received a request to reset your Lexora password.\n\n"
        f"Reset it here: {reset_link}\n\n"
        f"This link expires in {ttl_minutes} minutes. "
        f"If you didn't request this, you can safely ignore this email."
    )
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        logger.info(f"[PasswordReset email] sent to={email}")
    except Exception as e:
        logger.error(f"[PasswordReset email] to={email} failed: {e}")
        raise self.retry(exc=e)
