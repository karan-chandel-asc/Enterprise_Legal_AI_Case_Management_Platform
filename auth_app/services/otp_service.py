import random

from django.core.cache import cache

from auth_app.tasks import send_otp_email
from Enterprise_Legal_AI_Case_Management_Platform.logger import logger

OTP_TTL_SECONDS = 300


class OtpService:
    """Generates and verifies short-lived one-time codes for a given purpose
    (e.g. "verify_email", "mfa"), scoped per email address."""

    def _cache_key(self, purpose, email):
        return f"otp:{purpose}:{email.strip().lower()}"

    def generate_otp(self, purpose, email):
        code = f"{random.randint(0, 999999):06d}"
        cache.set(self._cache_key(purpose, email), code, timeout=OTP_TTL_SECONDS)
        logger.info(f"[OTP] purpose={purpose} email={email} code={code} (valid {OTP_TTL_SECONDS}s)")
        try:
            send_otp_email.delay(purpose=purpose, email=email, code=code, ttl_minutes=OTP_TTL_SECONDS // 60)
        except Exception as e:
            # Broker (Redis) unreachable, worker down, etc. The code is still
            # valid and logged above — never let a delivery hiccup block the
            # OTP flow itself.
            logger.error(f"[OTP email] could not queue send for purpose={purpose} email={email}: {e}")
        return code

    def verify_otp(self, purpose, email, code):
        key = self._cache_key(purpose, email)
        cached_code = cache.get(key)
        if cached_code is None:
            return False, "This code has expired. Please request a new one."
        if str(code).strip() != cached_code:
            return False, "Invalid verification code"
        cache.delete(key)
        return True, "Code verified"
