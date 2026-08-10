from Enterprise_Legal_AI_Case_Management_Platform.logger import logger
from case_management.models import Case
from chatbot.models import ChatMessage
from chatbot.services.rag_graph import run_rag_chat

HISTORY_TURNS = 10


class ChatService:
    def _get_owned_case(self, user, case_id):
        return Case.objects.filter(user=user, id=case_id).first()

    def get_history(self, user, case_id):
        try:
            case = self._get_owned_case(user, case_id)
            if not case:
                return False, "Case not found", None

            messages = case.chat_messages.order_by("created_at")
            return True, "Chat history fetched successfully", messages
        except Exception as e:
            logger.error(f"Error in ChatService.get_history: {e}")
            return False, f"Error fetching chat history: {e}", None

    def send_message(self, user, case_id, question):
        try:
            case = self._get_owned_case(user, case_id)
            if not case:
                return False, "Case not found", None

            question = (question or "").strip()
            if not question:
                return False, "Message cannot be empty", None

            doc_ids = [str(pk) for pk in case.documents.values_list("id", flat=True)]

            # Oldest-first, capped so the prompt doesn't grow unbounded turn after turn.
            recent = list(
                case.chat_messages.order_by("-created_at").values("role", "content")[:HISTORY_TURNS]
            )
            history = list(reversed(recent))

            ChatMessage.objects.create(case=case, role="user", content=question)

            if not doc_ids:
                answer = (
                    "This case doesn't have any documents indexed yet. Upload a document first, "
                    "then ask me anything about it."
                )
                citations = []
            else:
                result = run_rag_chat(question, doc_ids, history)
                answer, citations = result["answer"], result["citations"]

            assistant_message = ChatMessage.objects.create(
                case=case, role="assistant", content=answer, citations=citations
            )
            try:
                from analytics.services import AnalyticsService
                AnalyticsService.track(
                    "chat.message_sent",
                    user=user,
                    status="succeeded",
                    page="case_detail",
                    metadata={"case_id": case_id, "citations": len(citations or [])},
                )
            except Exception:
                pass
            return True, "Message sent successfully", assistant_message
        except Exception as e:
            logger.error(f"Error in ChatService.send_message: {e}")
            try:
                from analytics.services import AnalyticsService
                AnalyticsService.track(
                    "chat.message_failed",
                    user=user,
                    status="failed",
                    page="case_detail",
                    message=str(e)[:255],
                    metadata={"case_id": case_id},
                )
            except Exception:
                pass
            return False, f"Error processing message: {e}", None
