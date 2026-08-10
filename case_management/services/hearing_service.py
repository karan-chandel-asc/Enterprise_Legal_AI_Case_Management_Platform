from django.db.models import Q

from Enterprise_Legal_AI_Case_Management_Platform.logger import logger
from case_management.models import Case, Hearing


class HearingService:
    def __init__(self):
        self.hearing_model = Hearing
        self.case_model = Case

    def list_hearings(self, request, filters):
        try:
            hearings = self.hearing_model.objects.select_related('case').filter(case__user=request.user)

            if filters.get('month') and filters.get('year'):
                hearings = hearings.filter(
                    hearing_date__year=filters['year'],
                    hearing_date__month=filters['month'],
                )
            if filters.get('status'):
                hearings = hearings.filter(status=filters['status'])
            if filters.get('case_id'):
                hearings = hearings.filter(case_id=filters['case_id'])
            if filters.get('search'):
                search = filters['search']
                hearings = hearings.filter(
                    Q(case__case_title__icontains=search) | Q(court_name__icontains=search)
                )
            return hearings
        except Exception as e:
            logger.error(f"Error listing hearings: {e}")
            raise

    def get_hearing(self, request, hearing_id):
        return self.hearing_model.objects.select_related('case').filter(
            case__user=request.user, id=hearing_id
        ).first()

    def create_hearing(self, request, schema):
        try:
            case = self.case_model.objects.filter(user=request.user, id=schema.case_id).first()
            if not case:
                return False, "Case not found", None

            # If the case already has a hearing date, replace it with the new one
            if case.hearing_date or case.hearing_time:
                case.hearing_date = schema.hearing_date
                case.hearing_time = schema.hearing_time
                case.save()

            hearing = self.hearing_model.objects.create(
                case=case,
                hearing_date=schema.hearing_date,
                hearing_time=schema.hearing_time,
                court_name=schema.court_name or case.court_name,
                judge_name=schema.judge_name or "",
                status=schema.status or "confirmed",
                notes=schema.notes or "",
            )
            return True, "Hearing scheduled successfully", hearing
        except Exception as e:
            logger.error(f"Error creating hearing: {e}")
            return False, f"Error scheduling hearing: {e}", None

    def update_hearing(self, request, hearing_id, schema):
        try:
            hearing = self.get_hearing(request, hearing_id)
            if not hearing:
                return False, "Hearing not found", None
            updates = schema.model_dump(exclude_none=True)
            for field, value in updates.items():
                setattr(hearing, field, value)
            hearing.save()
            return True, "Hearing updated successfully", hearing
        except Exception as e:
            logger.error(f"Error updating hearing: {e}")
            return False, f"Error updating hearing: {e}", None

    def delete_hearing(self, request, hearing_id):
        try:
            hearing = self.get_hearing(request, hearing_id)
            if not hearing:
                return False, "Hearing not found", None
            hearing.delete()
            return True, "Hearing deleted successfully", None
        except Exception as e:
            logger.error(f"Error deleting hearing: {e}")
            return False, f"Error deleting hearing: {e}", None
