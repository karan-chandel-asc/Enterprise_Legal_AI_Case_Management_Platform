from pydantic import BaseModel, Field, field_validator

from analytics.services import ALLOWED_FRONTEND_EVENTS


class TrackEventSchema(BaseModel):
    event_name: str = Field(min_length=1, max_length=80)
    status: str = "info"
    page: str = ""
    message: str = ""
    visitor_id: str = ""
    referrer: str = ""
    metadata: dict = Field(default_factory=dict)

    @field_validator("event_name")
    @classmethod
    def validate_event_name(cls, value: str) -> str:
        name = (value or "").strip()
        if name not in ALLOWED_FRONTEND_EVENTS:
            allowed = ", ".join(sorted(ALLOWED_FRONTEND_EVENTS))
            raise ValueError(f"Unsupported event_name. Allowed: {allowed}")
        return name

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        status = (value or "info").strip().lower()
        if status not in {"started", "succeeded", "failed", "info"}:
            raise ValueError("status must be one of: started, succeeded, failed, info")
        return status
