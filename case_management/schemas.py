from datetime import date, time
from typing import Optional

from pydantic import BaseModel, field_validator

from case_management.models import Case, Hearing


class CaseListSchema(BaseModel):
    search: Optional[str] = None
    case_type: Optional[str] = None
    case_status: Optional[str] = None
    page: int = 1
    page_size: int = 10

    @field_validator("search", "case_type", "case_status")
    def blank_to_none(cls, value):
        if value is None:
            return None
        value = value.strip()
        return value or None

    @field_validator("page")
    def validate_page(cls, value):
        if value < 1:
            raise ValueError("Page must be 1 or greater")
        return value

    @field_validator("page_size")
    def validate_page_size(cls, value):
        if value < 1 or value > 100:
            raise ValueError("Page size must be between 1 and 100")
        return value



class CreateCaseSchema(BaseModel):
    case_id: str
    case_title: str
    case_type: str
    case_status: str
    client_name: str
    opposing_party_name: str
    court_name: str
    hearing_date: date
    case_description: str

    @field_validator('case_id', 'case_title', 'client_name', 'opposing_party_name', 'court_name', 'case_description')
    def validate_str_not_blank(cls, value):
        if not isinstance(value, str):
            raise ValueError('Must be a string')
        value = value.strip()
        if not value:
            raise ValueError('Must not be blank')
        return value

    @field_validator('case_type')
    def validate_case_type(cls, value):
        valid_choices = [choice[0] for choice in Case.case_type_choices]
        if value not in valid_choices:
            raise ValueError(f"case_type must be one of {valid_choices}")
        return value

    @field_validator('case_status')
    def validate_case_status(cls, value):
        valid_choices = [choice[0] for choice in Case.case_status_choices]
        if value not in valid_choices:
            raise ValueError(f"case_status must be one of {valid_choices}")
        return value


class UpdateCaseSchema(BaseModel):
    case_id: Optional[str] = None
    case_title: Optional[str] = None
    case_type: Optional[str] = None
    case_status: Optional[str] = None
    client_name: Optional[str] = None
    opposing_party_name: Optional[str] = None
    court_name: Optional[str] = None
    hearing_date: Optional[date] = None
    case_description: Optional[str] = None

    @field_validator('case_id', 'case_title', 'client_name', 'opposing_party_name', 'court_name', 'case_description')
    def validate_str_not_blank(cls, value):
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError('Must be a string')
        value = value.strip()
        if not value:
            raise ValueError('Must not be blank')
        return value

    @field_validator('case_type')
    def validate_case_type(cls, value):
        if value is None:
            return None
        valid_choices = [choice[0] for choice in Case.case_type_choices]
        if value not in valid_choices:
            raise ValueError(f"case_type must be one of {valid_choices}")
        return value

    @field_validator('case_status')
    def validate_case_status(cls, value):
        if value is None:
            return None
        valid_choices = [choice[0] for choice in Case.case_status_choices]
        if value not in valid_choices:
            raise ValueError(f"case_status must be one of {valid_choices}")
        return value


class CreateNoteSchema(BaseModel):
    note_title: str
    note_content: str

    @field_validator('note_title', 'note_content')
    def validate_not_blank(cls, value):
        if not isinstance(value, str):
            raise ValueError('Must be a string')
        value = value.strip()
        if not value:
            raise ValueError('Must not be blank')
        return value


class UpdateNoteSchema(BaseModel):
    note_title: Optional[str] = None
    note_content: Optional[str] = None

    @field_validator('note_title', 'note_content')
    def validate_not_blank(cls, value):
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError('Must be a string')
        value = value.strip()
        if not value:
            raise ValueError('Must not be blank')
        return value


class CreateHearingSchema(BaseModel):
    case_id: int
    hearing_date: date
    hearing_time: Optional[time] = None
    court_name: Optional[str] = None
    judge_name: Optional[str] = None
    status: Optional[str] = "confirmed"
    notes: Optional[str] = None

    @field_validator('status')
    def validate_status(cls, value):
        if value is None:
            return "confirmed"
        valid_choices = [choice[0] for choice in Hearing.status_choices]
        if value not in valid_choices:
            raise ValueError(f"status must be one of {valid_choices}")
        return value


class UpdateHearingSchema(BaseModel):
    hearing_date: Optional[date] = None
    hearing_time: Optional[time] = None
    court_name: Optional[str] = None
    judge_name: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None

    @field_validator('status')
    def validate_status(cls, value):
        if value is None:
            return None
        valid_choices = [choice[0] for choice in Hearing.status_choices]
        if value not in valid_choices:
            raise ValueError(f"status must be one of {valid_choices}")
        return value


class HearingListSchema(BaseModel):
    month: Optional[int] = None
    year: Optional[int] = None
    status: Optional[str] = None
    case_id: Optional[int] = None
    search: Optional[str] = None

    @field_validator('month')
    def validate_month(cls, value):
        if value is None:
            return None
        if value < 1 or value > 12:
            raise ValueError('month must be between 1 and 12')
        return value
