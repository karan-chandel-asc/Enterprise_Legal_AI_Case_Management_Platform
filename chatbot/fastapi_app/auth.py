"""Authentication/CSRF bridge so the standalone FastAPI upload service can
trust the same login session as the main Django app, without inventing a
second auth system (no separate tokens/JWTs to issue or refresh).

Both processes share one database, so a Django session id is enough to look
the user up. These dependency functions are plain ``def`` (not ``async def``)
on purpose: FastAPI runs sync dependencies in a threadpool, which is exactly
what the blocking Django ORM/session calls need.
"""

from django.contrib.auth import get_user_model
from django.contrib.sessions.backends.db import SessionStore
from fastapi import HTTPException, Request, status


def get_current_user(request: Request):
    session_key = request.cookies.get("sessionid")
    if not session_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    session = SessionStore(session_key=session_key)
    if not session.exists(session_key):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired, please log in again")

    user_id = session.get("_auth_user_id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    UserModel = get_user_model()
    try:
        return UserModel.objects.get(pk=user_id)
    except UserModel.DoesNotExist:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")


def verify_csrf(request: Request) -> None:
    """Double-submit CSRF check, mirroring Django's own CsrfViewMiddleware
    strategy: the caller must echo the csrftoken cookie value back as a
    header. A cross-site attacker page cannot read the cookie value (browser
    same-origin policy blocks that), so it can never forge a matching
    header, even though the browser would still attach the cookie itself."""
    cookie_token = request.cookies.get("csrftoken")
    header_token = request.headers.get("x-csrftoken")
    if not cookie_token or not header_token or cookie_token != header_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF verification failed")
