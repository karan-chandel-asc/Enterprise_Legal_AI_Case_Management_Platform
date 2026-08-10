from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

from Enterprise_Legal_AI_Case_Management_Platform.logger import logger
from analytics.services import AnalyticsService


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def send_daily_analytics_digest(self, hours: int = 24):
    """Aggregate the last N hours of analytics events and email a digest."""
    if not getattr(settings, "ANALYTICS_DIGEST_ENABLED", True):
        logger.info("[Analytics digest] skipped — ANALYTICS_DIGEST_ENABLED is False")
        return "skipped"

    digest = AnalyticsService.build_daily_digest(hours=hours)
    recipient = digest["recipient"]
    if not recipient:
        logger.error("[Analytics digest] no recipient configured (ANALYTICS_DIGEST_EMAIL / DEFAULT_FROM_EMAIL)")
        return "no_recipient"

    subject, body = AnalyticsService.format_digest_email(digest)
    try:
        send_mail(
            subject=subject,
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            fail_silently=False,
        )
        deleted = AnalyticsService.delete_events_in_window(digest["since"], digest["until"])
        logger.info(
            f"[Analytics digest] sent to={recipient} visitors={digest['unique_visitors']} "
            f"interested={digest['interested_visitors']} events={digest['total_events']} deleted={deleted}"
        )
        return f"sent_deleted_{deleted}"
    except Exception as e:
        logger.error(f"[Analytics digest] email failed: {e}")
        raise self.retry(exc=e)
