from Enterprise_Legal_AI_Case_Management_Platform.logger import logger
from case_management.models import Case, CaseNotes


class NoteService:
    def __init__(self):
        self.note_model = CaseNotes
        self.case_model = Case

    def _get_owned_case(self, request, case_id):
        return self.case_model.objects.filter(user=request.user, id=case_id).first()

    def list_notes(self, request, case_id):
        try:
            case = self._get_owned_case(request, case_id)
            if not case:
                return False, "Case not found", None
            notes = case.notes.order_by('-note_updated_at')
            return True, "Notes fetched successfully", notes
        except Exception as e:
            logger.error(f"Error listing notes: {e}")
            raise

    def create_note(self, request, case_id, schema):
        try:
            case = self._get_owned_case(request, case_id)
            if not case:
                return False, "Case not found", None
            note = self.note_model.objects.create(
                case=case,
                note_title=schema.note_title,
                note_content=schema.note_content,
            )
            return True, "Note created successfully", note
        except Exception as e:
            logger.error(f"Error creating note: {e}")
            return False, f"Error creating note: {e}", None

    def update_note(self, request, case_id, note_id, schema):
        try:
            case = self._get_owned_case(request, case_id)
            if not case:
                return False, "Case not found", None
            note = case.notes.filter(id=note_id).first()
            if not note:
                return False, "Note not found", None
            updates = schema.model_dump(exclude_none=True)
            for field, value in updates.items():
                setattr(note, field, value)
            note.save()
            return True, "Note updated successfully", note
        except Exception as e:
            logger.error(f"Error updating note: {e}")
            return False, f"Error updating note: {e}", None

    def delete_note(self, request, case_id, note_id):
        try:
            case = self._get_owned_case(request, case_id)
            if not case:
                return False, "Case not found", None
            note = case.notes.filter(id=note_id).first()
            if not note:
                return False, "Note not found", None
            note.delete()
            return True, "Note deleted successfully", None
        except Exception as e:
            logger.error(f"Error deleting note: {e}")
            return False, f"Error deleting note: {e}", None
