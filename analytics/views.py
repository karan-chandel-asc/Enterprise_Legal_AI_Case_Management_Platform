from pydantic import ValidationError
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from Enterprise_Legal_AI_Case_Management_Platform.logger import logger
from Enterprise_Legal_AI_Case_Management_Platform.responses import error_response, success_response
from analytics.schemas import TrackEventSchema
from analytics.services import AnalyticsService


class TrackEventApi(APIView):
    """Ingest selective frontend analytics (page views + CTA clicks).

    Authenticated when a session exists; anonymous events are still accepted
    so auth pages can be measured before login.
    """

    authentication_classes = [SessionAuthentication]
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            data = request.data.dict() if hasattr(request.data, "dict") else dict(request.data)
            if isinstance(data.get("metadata"), str):
                data["metadata"] = {}

            try:
                schema = TrackEventSchema(**data)
            except ValidationError as e:
                message = e.errors()[0]["msg"].replace("Value error, ", "")
                return Response(error_response(message=message), status=status.HTTP_400_BAD_REQUEST)

            metadata = dict(schema.metadata or {})
            for key in list(metadata.keys()):
                if any(token in key.lower() for token in ("password", "otp", "token", "secret")):
                    metadata.pop(key, None)

            AnalyticsService.track(
                schema.event_name,
                request=request,
                status=schema.status,
                page=schema.page,
                source="frontend",
                message=schema.message,
                metadata=metadata,
                visitor_id=schema.visitor_id,
                referrer=schema.referrer,
            )
            return Response(success_response(message="Event recorded"), status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error in TrackEventApi: {e}")
            return Response(
                error_response(message="Could not record event"),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
