from pydantic import BaseModel, field_validator, model_validator
import re

class RegisterSchema(BaseModel):
    full_name: str
    law_firm_name: str
    email: str
    password: str

    @field_validator("full_name")
    def validate_full_name(cls, value):
        if not value or str(value).strip() == "":
            raise ValueError("Full name is required")
        return value.strip()
    
    @field_validator("law_firm_name")
    def validate_law_firm_name(cls, value):
        if not value or str(value).strip() == "":
            raise ValueError("Law firm name is required")
        return value.strip()
    
    @field_validator("email")
    def validate_email(cls, value):
        if not value or str(value).strip() == "":
            raise ValueError("Email is required")
        email = value.strip().lower()
        if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w{2,}$", email):
            raise ValueError("Enter a valid email address")
        return email
    
    @field_validator("password")
    def validate_password(cls, value):
        if not value or str(value).strip() == "":
            raise ValueError("Password is required")
        return value




class LoginSchema(BaseModel):
    email: str
    password: str

    @field_validator("email")
    def validate_email(cls, value):
        if not value or str(value).strip() == "":
            raise ValueError("Email is required")
        return value.strip().lower()

    @field_validator("password")
    def validate_password(cls, value):
        if not value or str(value).strip() == "":
            raise ValueError("Password is required")
        return value

class ForgotPasswordSchema(BaseModel):
    email: str

    @field_validator("email")
    def validate_email(cls, value):
        if not value or str(value).strip() == "":
            raise ValueError("Email is required")
        return value.strip().lower()


class ResetPasswordSchema(BaseModel):
    uid: str
    token: str
    password: str
    confirm_password: str

    @field_validator("password")
    def validate_password(cls, value):
        if not value or str(value).strip() == "":
            raise ValueError("Password is required")
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters")
        return value

    @field_validator("confirm_password")
    def validate_confirm_password(cls, value):
        if not value or str(value).strip() == "":
            raise ValueError("Confirm password is required")
        return value

    @model_validator(mode="after")
    def passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class MfaVerifySchema(BaseModel):
    otp: str

    @field_validator("otp")
    def validate_otp(cls, value):
        value = str(value).strip()
        if not value:
            raise ValueError("Code is required")
        if not re.match(r"^\d{6}$", value):
            raise ValueError("Enter the 6-digit code")
        return value


class VerifyEmailSchema(BaseModel):
    otp: str

    @field_validator("otp")
    def validate_otp(cls, value):
        value = str(value).strip()
        if not value:
            raise ValueError("Code is required")
        if not re.match(r"^\d{6}$", value):
            raise ValueError("Enter the 6-digit code")
        return value


class UpdateProfileSchema(BaseModel):
    full_name: str
    law_firm_name: str = ""
    phone_number: str = ""

    @field_validator("full_name")
    def validate_full_name(cls, value):
        if not value or str(value).strip() == "":
            raise ValueError("Full name is required")
        return value.strip()

    @field_validator("law_firm_name")
    def validate_law_firm_name(cls, value):
        return (value or "").strip()

    @field_validator("phone_number")
    def validate_phone_number(cls, value):
        value = (value or "").strip()
        if value and not re.match(r"^[\d\s+\-()]{7,20}$", value):
            raise ValueError("Enter a valid phone number")
        return value


class ChangePasswordSchema(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str

    @field_validator("current_password")
    def validate_current_password(cls, value):
        if not value or str(value).strip() == "":
            raise ValueError("Current password is required")
        return value

    @field_validator("new_password")
    def validate_new_password(cls, value):
        if not value or str(value).strip() == "":
            raise ValueError("New password is required")
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters")
        return value

    @field_validator("confirm_password")
    def validate_confirm_password(cls, value):
        if not value or str(value).strip() == "":
            raise ValueError("Confirm password is required")
        return value

    @model_validator(mode="after")
    def passwords_match(self):
        if self.new_password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class UpdateMfaSchema(BaseModel):
    enabled: bool
