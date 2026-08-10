from django.shortcuts import get_object_or_404, render
from pydantic import ValidationError
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from Enterprise_Legal_AI_Case_Management_Platform.logger import logger
from Enterprise_Legal_AI_Case_Management_Platform.responses import error_response, success_response
from analytics.services import AnalyticsService

from case_management.models import Case
from case_management.pipeline.case_activity_pipeline import CaseActivityPipeline
from case_management.pipeline.case_detail_pipeline import CaseDetailPipeline
from case_management.pipeline.case_list_pipeline import CaseListPipeline
from case_management.pipeline.create_case_pipeline import CreateCasePipeline
from case_management.pipeline.create_document_pipeline import CreateDocumentPipeline
from case_management.pipeline.create_hearing_pipeline import CreateHearingPipeline
from case_management.pipeline.create_note_pipeline import CreateNotePipeline
from case_management.pipeline.delete_case_pipeline import DeleteCasePipeline
from case_management.pipeline.delete_document_pipeline import DeleteDocumentPipeline
from case_management.pipeline.delete_hearing_pipeline import DeleteHearingPipeline
from case_management.pipeline.delete_note_pipeline import DeleteNotePipeline
from case_management.pipeline.document_list_pipeline import DocumentListPipeline
from case_management.pipeline.hearing_list_pipeline import HearingListPipeline
from case_management.pipeline.note_list_pipeline import NoteListPipeline
from case_management.pipeline.update_case_pipeline import UpdateCasePipeline
from case_management.pipeline.update_hearing_pipeline import UpdateHearingPipeline
from case_management.pipeline.update_note_pipeline import UpdateNotePipeline
from django.contrib.auth.decorators import login_required
from case_management.schemas import (
    CaseListSchema,
    CreateCaseSchema,
    CreateHearingSchema,
    CreateNoteSchema,
    HearingListSchema,
    UpdateCaseSchema,
    UpdateHearingSchema,
    UpdateNoteSchema,
)
from case_management.serializers import (
    CaseDetailSerializer,
    CaseDocumentSerializer,
    CaseListSerializer,
    CaseNoteSerializer,
    HearingSerializer,
)

@login_required(login_url="login")
def cases_list_page(request):
    return render(request, "cases/list.html")


@login_required(login_url="login")
def case_detail_page(request, case_id):
    get_object_or_404(Case, id=case_id, user=request.user)
    return render(request, "cases/detail.html", {"case_id": case_id})


@login_required(login_url="login")
def hearings_page(request):
    return render(request, "hearings.html")


def _validation_error_response(exc):
    message = exc.errors()[0]["msg"].replace("Value error, ", "")
    return Response(error_response(message=message), status=status.HTTP_400_BAD_REQUEST)


class CaseListApi(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            try:
                # Query params (?search=, ?page=, etc.) come from query_params,
                # never from request.data — request.data is for request bodies
                # and is always empty on a GET request.
                schema = CaseListSchema(**request.query_params.dict())
            except ValidationError as e:
                message = e.errors()[0]["msg"].replace("Value error, ", "")
                return Response(error_response(message=message), status=status.HTTP_400_BAD_REQUEST)

            pipeline = CaseListPipeline(request, schema.model_dump())
            success, message, result = pipeline.process_item()
            if not success:
                return Response(error_response(message=message), status=status.HTTP_400_BAD_REQUEST)

            data = {
                "cases": CaseListSerializer(result["cases"], many=True).data,
                "pagination": result["pagination"],
                "counts": result["counts"],
            }
            return Response(success_response(message=message, data=data), status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error in CaseListApi: {e}")
            return Response(error_response(message=f"Error getting cases: {e}"), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CreateCaseApi(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            data = request.data.dict() if hasattr(request.data, "dict") else dict(request.data)
            try:
                schema = CreateCaseSchema(**data)
            except ValidationError as e:
                return _validation_error_response(e)

            pipeline = CreateCasePipeline(request, schema)
            success, message, case = pipeline.process_item()
            if not success:
                AnalyticsService.track(
                    "case.created",
                    request=request,
                    status="failed",
                    page="cases",
                    message=message,
                )
                return Response(error_response(message=message), status=status.HTTP_400_BAD_REQUEST)

            AnalyticsService.track(
                "case.created",
                request=request,
                status="succeeded",
                page="cases",
                metadata={"case_id": case.id if case else None},
            )
            data = CaseListSerializer(case).data
            return Response(success_response(message=message, data=data), status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error in CreateCaseApi: {e}")
            return Response(error_response(message=f"Error creating case: {e}"), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CaseDetailApi(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, case_id):
        try:
            pipeline = CaseDetailPipeline(request, case_id)
            success, message, case = pipeline.process_item()
            if not success:
                return Response(error_response(message=message), status=status.HTTP_404_NOT_FOUND)

            data = CaseDetailSerializer(case).data
            return Response(success_response(message=message, data=data), status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error in CaseDetailApi.get: {e}")
            return Response(error_response(message=f"Error getting case: {e}"), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request, case_id):
        try:
            data = request.data.dict() if hasattr(request.data, "dict") else dict(request.data)
            try:
                schema = UpdateCaseSchema(**data)
            except ValidationError as e:
                return _validation_error_response(e)

            pipeline = UpdateCasePipeline(request, case_id, schema)
            success, message, case = pipeline.process_item()
            if not success:
                status_code = status.HTTP_404_NOT_FOUND if message == "Case not found" else status.HTTP_400_BAD_REQUEST
                return Response(error_response(message=message), status=status_code)

            data = CaseDetailSerializer(case).data
            return Response(success_response(message=message, data=data), status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error in CaseDetailApi.patch: {e}")
            return Response(error_response(message=f"Error updating case: {e}"), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, case_id):
        try:
            pipeline = DeleteCasePipeline(request, case_id)
            success, message, _ = pipeline.process_item()
            if not success:
                return Response(error_response(message=message), status=status.HTTP_404_NOT_FOUND)

            return Response(success_response(message=message), status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error in CaseDetailApi.delete: {e}")
            return Response(error_response(message=f"Error deleting case: {e}"), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CaseDocumentsApi(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, case_id):
        try:
            pipeline = DocumentListPipeline(request, case_id)
            success, message, documents = pipeline.process_item()
            if not success:
                return Response(error_response(message=message), status=status.HTTP_404_NOT_FOUND)

            data = CaseDocumentSerializer(documents, many=True, context={"request": request}).data
            return Response(success_response(message=message, data=data), status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error in CaseDocumentsApi.get: {e}")
            return Response(error_response(message=f"Error getting documents: {e}"), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, case_id):
        try:
            file_obj = request.FILES.get("file")
            document_name = request.data.get("document_name")

            pipeline = CreateDocumentPipeline(request, case_id, file_obj, document_name)
            success, message, document = pipeline.process_item()
            AnalyticsService.track(
                "document.uploaded",
                request=request,
                status="succeeded" if success else "failed",
                page="case_detail",
                message=message,
                metadata={
                    "case_id": case_id,
                    "document_id": getattr(document, "id", None),
                    "file_name": getattr(file_obj, "name", "")[:120] if file_obj else "",
                },
            )
            if not success:
                status_code = status.HTTP_404_NOT_FOUND if message == "Case not found" else status.HTTP_400_BAD_REQUEST
                return Response(error_response(message=message), status=status_code)

            data = CaseDocumentSerializer(document, context={"request": request}).data
            return Response(success_response(message=message, data=data), status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error in CaseDocumentsApi.post: {e}")
            return Response(error_response(message=f"Error uploading document: {e}"), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CaseDocumentDetailApi(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, case_id, document_id):
        try:
            pipeline = DeleteDocumentPipeline(request, case_id, document_id)
            success, message, payload = pipeline.process_item()
            if not success:
                return Response(error_response(message=message), status=status.HTTP_404_NOT_FOUND)

            return Response(success_response(message=message, data=payload), status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error in CaseDocumentDetailApi.delete: {e}")
            return Response(error_response(message=f"Error deleting document: {e}"), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CaseNotesApi(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, case_id):
        try:
            pipeline = NoteListPipeline(request, case_id)
            success, message, notes = pipeline.process_item()
            if not success:
                return Response(error_response(message=message), status=status.HTTP_404_NOT_FOUND)

            data = CaseNoteSerializer(notes, many=True).data
            return Response(success_response(message=message, data=data), status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error in CaseNotesApi.get: {e}")
            return Response(error_response(message=f"Error getting notes: {e}"), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, case_id):
        try:
            data = request.data.dict() if hasattr(request.data, "dict") else dict(request.data)
            try:
                schema = CreateNoteSchema(**data)
            except ValidationError as e:
                return _validation_error_response(e)

            pipeline = CreateNotePipeline(request, case_id, schema)
            success, message, note = pipeline.process_item()
            if not success:
                status_code = status.HTTP_404_NOT_FOUND if message == "Case not found" else status.HTTP_400_BAD_REQUEST
                return Response(error_response(message=message), status=status_code)

            data = CaseNoteSerializer(note).data
            return Response(success_response(message=message, data=data), status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error in CaseNotesApi.post: {e}")
            return Response(error_response(message=f"Error creating note: {e}"), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CaseNoteDetailApi(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, case_id, note_id):
        try:
            data = request.data.dict() if hasattr(request.data, "dict") else dict(request.data)
            try:
                schema = UpdateNoteSchema(**data)
            except ValidationError as e:
                return _validation_error_response(e)

            pipeline = UpdateNotePipeline(request, case_id, note_id, schema)
            success, message, note = pipeline.process_item()
            if not success:
                status_code = status.HTTP_404_NOT_FOUND if "not found" in message else status.HTTP_400_BAD_REQUEST
                return Response(error_response(message=message), status=status_code)

            data = CaseNoteSerializer(note).data
            return Response(success_response(message=message, data=data), status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error in CaseNoteDetailApi.patch: {e}")
            return Response(error_response(message=f"Error updating note: {e}"), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, case_id, note_id):
        try:
            pipeline = DeleteNotePipeline(request, case_id, note_id)
            success, message, _ = pipeline.process_item()
            if not success:
                return Response(error_response(message=message), status=status.HTTP_404_NOT_FOUND)

            return Response(success_response(message=message), status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error in CaseNoteDetailApi.delete: {e}")
            return Response(error_response(message=f"Error deleting note: {e}"), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CaseActivityApi(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, case_id):
        try:
            pipeline = CaseActivityPipeline(request, case_id)
            success, message, activity = pipeline.process_item()
            if not success:
                return Response(error_response(message=message), status=status.HTTP_404_NOT_FOUND)

            return Response(success_response(message=message, data=activity), status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error in CaseActivityApi: {e}")
            return Response(error_response(message=f"Error getting activity: {e}"), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HearingsApi(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            try:
                schema = HearingListSchema(**request.query_params.dict())
            except ValidationError as e:
                return _validation_error_response(e)

            pipeline = HearingListPipeline(request, schema.model_dump())
            success, message, hearings = pipeline.process_item()
            if not success:
                return Response(error_response(message=message), status=status.HTTP_400_BAD_REQUEST)

            data = HearingSerializer(hearings, many=True).data
            return Response(success_response(message=message, data=data), status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error in HearingsApi.get: {e}")
            return Response(error_response(message=f"Error getting hearings: {e}"), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        try:
            data = request.data.dict() if hasattr(request.data, "dict") else dict(request.data)
            try:
                schema = CreateHearingSchema(**data)
            except ValidationError as e:
                return _validation_error_response(e)

            pipeline = CreateHearingPipeline(request, schema)
            success, message, hearing = pipeline.process_item()
            if not success:
                status_code = status.HTTP_404_NOT_FOUND if message == "Case not found" else status.HTTP_400_BAD_REQUEST
                return Response(error_response(message=message), status=status_code)

            data = HearingSerializer(hearing).data
            return Response(success_response(message=message, data=data), status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error in HearingsApi.post: {e}")
            return Response(error_response(message=f"Error scheduling hearing: {e}"), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HearingDetailApi(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, hearing_id):
        try:
            data = request.data.dict() if hasattr(request.data, "dict") else dict(request.data)
            try:
                schema = UpdateHearingSchema(**data)
            except ValidationError as e:
                return _validation_error_response(e)

            pipeline = UpdateHearingPipeline(request, hearing_id, schema)
            success, message, hearing = pipeline.process_item()
            if not success:
                status_code = status.HTTP_404_NOT_FOUND if message == "Hearing not found" else status.HTTP_400_BAD_REQUEST
                return Response(error_response(message=message), status=status_code)

            data = HearingSerializer(hearing).data
            return Response(success_response(message=message, data=data), status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error in HearingDetailApi.patch: {e}")
            return Response(error_response(message=f"Error updating hearing: {e}"), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, hearing_id):
        try:
            pipeline = DeleteHearingPipeline(request, hearing_id)
            success, message, _ = pipeline.process_item()
            if not success:
                return Response(error_response(message=message), status=status.HTTP_404_NOT_FOUND)

            return Response(success_response(message=message), status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error in HearingDetailApi.delete: {e}")
            return Response(error_response(message=f"Error deleting hearing: {e}"), status=status.HTTP_500_INTERNAL_SERVER_ERROR)