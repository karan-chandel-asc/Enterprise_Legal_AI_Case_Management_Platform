from django.core.management.base import BaseCommand

from analytics.tasks import send_daily_analytics_digest


class Command(BaseCommand):
    help = "Send the analytics digest email now (last N hours)."

    def add_arguments(self, parser):
        parser.add_argument("--hours", type=int, default=24)
        parser.add_argument(
            "--async",
            action="store_true",
            dest="run_async",
            help="Queue via Celery instead of running inline.",
        )

    def handle(self, *args, **options):
        hours = options["hours"]
        if options["run_async"]:
            result = send_daily_analytics_digest.delay(hours=hours)
            self.stdout.write(self.style.SUCCESS(f"Queued digest task id={result.id}"))
            return

        status = send_daily_analytics_digest(hours=hours)
        self.stdout.write(self.style.SUCCESS(f"Digest finished: {status}"))
