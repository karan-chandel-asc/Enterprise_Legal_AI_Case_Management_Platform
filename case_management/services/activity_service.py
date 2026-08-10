from Enterprise_Legal_AI_Case_Management_Platform.logger import logger
from case_management.models import Case

TIME_FORMAT = "%b %d, %Y \u00b7 %I:%M %p"


class ActivityService:
    def get_case_activity(self, request, case_id):
        try:
            case = Case.objects.prefetch_related('documents', 'notes', 'hearings').filter(
                user=request.user, id=case_id
            ).first()
            if not case:
                return False, "Case not found", None

            events = [{
                "type": "case",
                "text": f"Case \"{case.case_title}\" created",
                "time": case.case_created_at,
            }]

            for doc in case.documents.all():
                events.append({
                    "type": "upload",
                    "text": f"Document uploaded: {doc.document_name}",
                    "time": doc.uploaded_at,
                })

            for note in case.notes.all():
                events.append({
                    "type": "note",
                    "text": f"Note added: {note.note_title}",
                    "time": note.note_created_at,
                })

            for hearing in case.hearings.all():
                events.append({
                    "type": "hearing",
                    "text": f"Hearing scheduled for {hearing.hearing_date.strftime('%b %d, %Y')}",
                    "time": hearing.hearing_created_at,
                })

            events.sort(key=lambda e: e["time"], reverse=True)
            for event in events:
                event["time"] = event["time"].strftime(TIME_FORMAT)

            return True, "Activity fetched successfully", events
        except Exception as e:
            logger.error(f"Error fetching case activity: {e}")
            return False, f"Error fetching case activity: {e}", None
