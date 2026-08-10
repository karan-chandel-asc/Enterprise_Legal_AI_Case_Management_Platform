from django.shortcuts import render
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from Enterprise_Legal_AI_Case_Management_Platform.logger import logger
from Enterprise_Legal_AI_Case_Management_Platform.responses import error_response, success_response

from dashboard.pipeline.dashboard_overview_pipeline import DashboardOverviewPipeline
from dashboard.serializers import RecentAiChatSerializer, RecentCaseSerializer, UpcomingHearingSerializer
from django.contrib.auth.decorators import login_required

@login_required(login_url="login")
def dashboard_page(request):
    return render(request, "dashboard.html")


class DashboardApi(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            pipeline = DashboardOverviewPipeline(request)
            success, message, result = pipeline.process_item()
            if not success:
                return Response(error_response(message=message), status=status.HTTP_400_BAD_REQUEST)

            data = {
                "kpis": result["kpis"],
                "recent_cases": RecentCaseSerializer(result["recent_cases"], many=True).data,
                "upcoming_hearings": UpcomingHearingSerializer(result["upcoming_hearings"], many=True).data,
                "ai_activity": result["ai_activity"],
                "recent_ai_chats": RecentAiChatSerializer(result["recent_ai_chats"], many=True).data,
                "user": {
                    "full_name": request.user.full_name,
                },
            }
            return Response(success_response(message=message, data=data), status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error in DashboardApi: {e}")
            return Response(error_response(message=f"Error getting dashboard data: {e}"), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
