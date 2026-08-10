from dashboard.pipeline.base_pipeline import BasePipeline
from dashboard.services.dashboard_service import DashboardService
from Enterprise_Legal_AI_Case_Management_Platform.logger import logger


class DashboardOverviewPipeline(BasePipeline):
    def __init__(self, request):
        self.request = request
        self.dashboard_service = DashboardService()

    def process_item(self):
        try:
            user = self.request.user
            payload = {
                "kpis": self.dashboard_service.get_kpis(user),
                "recent_cases": self.dashboard_service.get_recent_cases(user),
                "upcoming_hearings": self.dashboard_service.get_upcoming_hearings(user),
                "ai_activity": self.dashboard_service.get_ai_activity(user),
                "recent_ai_chats": self.dashboard_service.get_recent_ai_chats(user),
            }
            return True, "Dashboard data fetched successfully", payload
        except Exception as e:
            logger.error(f"Error in DashboardOverviewPipeline: {e}")
            return False, f"Error getting dashboard data: {e}", None
