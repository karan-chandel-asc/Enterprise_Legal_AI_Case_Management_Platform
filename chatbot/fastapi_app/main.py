"""Standalone FastAPI micro-service for the chatbot's REST API — semantic
search and per-case AI Assistant chat, backed by the LangGraph RAG pipeline
in chatbot/services/rag_graph.py.

Document uploads are handled by Django/DRF instead (see
case_management.views.CaseDocumentsApi.post) so all case CRUD stays on one
consistent REST surface. This service stays dedicated to chatbot queries,
which benefit from running independently of the main Django process.

Why a separate service for chat/search: FastAPI's async-friendly request
handling keeps this traffic decoupled from the rest of the Django app, while
still reusing the exact same service layer and database - `django.setup()`
below boots just enough of Django to use its ORM and existing business logic.

Run with (from the project root, with the venv active):
    uvicorn chatbot.fastapi_app.main:app --host 127.0.0.1 --port 8001 --reload
"""

import os
from typing import Optional

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Enterprise_Legal_AI_Case_Management_Platform.settings")
django.setup()

from fastapi import Depends, FastAPI, HTTPException, status  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from pydantic import BaseModel  # noqa: E402

from chatbot.fastapi_app.auth import get_current_user, verify_csrf  # noqa: E402
from chatbot.services.chat_service import ChatService  # noqa: E402
from chatbot.services.search_service import SemanticSearchService  # noqa: E402
from Enterprise_Legal_AI_Case_Management_Platform.logger import logger  # noqa: E402

app = FastAPI(title="Legal AI - Chatbot Service")

# Local: browser hits Django :8000 and FastAPI :8001 (cross-origin).
# Docker/nginx: browser hits same origin via /ai/ proxy (CORS unused).
_default_origins = ["http://127.0.0.1:8000", "http://localhost:8000"]
_extra_origins = [
    o.strip()
    for o in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")
    if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_default_origins + _extra_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Chatbot REST API — semantic search + per-case AI Assistant chat
# ---------------------------------------------------------------------------

chat_service = ChatService()
search_service = SemanticSearchService()


class SearchRequest(BaseModel):
    query: str
    case_id: Optional[int] = None


class ChatMessageRequest(BaseModel):
    message: str


def _serialize_message(msg) -> dict:
    return {
        "id": msg.id,
        "role": msg.role,
        "content": msg.content,
        "citations": msg.citations,
        "created_at": msg.created_at.isoformat(),
    }


@app.post("/api/search/")
def semantic_search(
    payload: SearchRequest,
    user=Depends(get_current_user),
    _csrf=Depends(verify_csrf),
):
    success, message, results = search_service.search(user, payload.query, case_id=payload.case_id)
    if not success:
        status_code = status.HTTP_404_NOT_FOUND if message == "Case not found" else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=message)
    return {"success": True, "message": message, "data": results}


@app.get("/api/chat/{case_id}/messages/")
def get_chat_history(case_id: int, user=Depends(get_current_user)):
    success, message, messages = chat_service.get_history(user, case_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)
    return {"success": True, "message": message, "data": [_serialize_message(m) for m in messages]}


@app.post("/api/chat/{case_id}/messages/", status_code=status.HTTP_201_CREATED)
def send_chat_message(
    case_id: int,
    payload: ChatMessageRequest,
    user=Depends(get_current_user),
    _csrf=Depends(verify_csrf),
):
    success, message, assistant_message = chat_service.send_message(user, case_id, payload.message)
    if not success:
        status_code = status.HTTP_404_NOT_FOUND if message == "Case not found" else status.HTTP_400_BAD_REQUEST
        logger.error(f"[FastAPI chat] {message} (case_id={case_id}, user={user.id})")
        raise HTTPException(status_code=status_code, detail=message)

    logger.info(f"[FastAPI chat] Answered question for case {case_id} by user {user.id}")
    return {"success": True, "message": message, "data": _serialize_message(assistant_message)}
