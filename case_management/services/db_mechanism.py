from Enterprise_Legal_AI_Case_Management_Platform.logger import logger
from case_management.models import Case, Hearing


class DbMechanism:
    def __init__(self):
        self.case_model = Case

    def get_cases(self, request):
        try:
            cases = self.case_model.objects.prefetch_related('documents', 'notes').filter(user=request.user)
            return cases
        except Exception as e:
            logger.error(f"Error getting cases: {e}")
            raise
    
    def create_case(self, request, schema):
        try:
            if self.case_model.objects.filter(case_id=schema.case_id).exists():
                return False, f"A case with number '{schema.case_id}' already exists", None

            case = self.case_model.objects.create(
                case_id=schema.case_id,
                case_title=schema.case_title,
                case_type=schema.case_type,
                case_status=schema.case_status,
                client_name=schema.client_name,
                opposing_party_name=schema.opposing_party_name,
                court_name=schema.court_name,
                hearing_date=schema.hearing_date,
                case_description=schema.case_description,
                user=request.user,
            )
            self._sync_case_hearing(case)
            return True, "Case created successfully", case
        except Exception as e:
            logger.error(f"Error creating case: {e}")
            return False, f"Error creating case: {e}", None

    def get_case(self, request, case_id):
        try:
            case = self.case_model.objects.prefetch_related('documents', 'notes').filter(
                user=request.user, id=case_id
            ).first()
            if not case:
                return False, "Case not found", None
            return True, "Case fetched successfully", case
        except Exception as e:
            logger.error(f"Error getting case: {e}")
            raise

    def update_case(self, request, case_id, schema):
        try:
            case = self.case_model.objects.filter(user=request.user, id=case_id).first()
            if not case:
                return False, "Case not found", None

            updates = schema.model_dump(exclude_none=True)
            if "case_id" in updates and updates["case_id"] != case.case_id:
                if self.case_model.objects.filter(case_id=updates["case_id"]).exclude(id=case.id).exists():
                    return False, f"A case with number '{updates['case_id']}' already exists", None

            for field, value in updates.items():
                setattr(case, field, value)
            case.save()
            if "hearing_date" in updates:
                self._sync_case_hearing(case)
            return True, "Case updated successfully", case
        except Exception as e:
            logger.error(f"Error updating case: {e}")
            return False, f"Error updating case: {e}", None

    def _sync_case_hearing(self, case):
        """Keeps the case's `hearing_date` field mirrored into the Hearing
        model so it automatically shows up on the Hearings calendar. Reuses
        the case's earliest scheduled hearing if one already exists,
        otherwise creates a new one — never touches other, unrelated
        hearings tied to the same case."""
        try:
            hearing = Hearing.objects.filter(case=case).order_by('hearing_date', 'hearing_time').first()
            if hearing:
                if hearing.hearing_date != case.hearing_date:
                    hearing.hearing_date = case.hearing_date
                    hearing.save(update_fields=['hearing_date', 'hearing_updated_at'])
            else:
                Hearing.objects.create(
                    case=case,
                    hearing_date=case.hearing_date,
                    court_name=case.court_name,
                    status='confirmed',
                )
        except Exception as e:
            logger.error(f"Error syncing hearing for case {case.id}: {e}")

    def delete_case(self, request, case_id):
        try:
            case = self.case_model.objects.filter(user=request.user, id=case_id).first()
            if not case:
                return False, "Case not found", None
            case.delete()
            return True, "Case deleted successfully", None
        except Exception as e:
            logger.error(f"Error deleting case: {e}")
            return False, f"Error deleting case: {e}", None
