from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse
from pydantic import ValidationError
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from Enterprise_Legal_AI_Case_Management_Platform.logger import logger
from Enterprise_Legal_AI_Case_Management_Platform.responses import error_response, success_response
from analytics.services import AnalyticsService

from .feature_flags import EMAIL_VERIFICATION_ENABLED, MFA_LOGIN_ENABLED
from .pipelines.forgot_password_pipeline import ForgotPasswordPipeline
from .pipelines.login_pipeline import LoginPipeline
from .pipelines.mfa_verify_pipeline import MfaVerifyPipeline
from .pipelines.register_user_pipeline import RegisterUserPipeline
from .pipelines.resend_otp_pipeline import ResendOtpPipeline
from .pipelines.reset_password_pipeline import ResetPasswordPipeline
from .pipelines.verify_email_pipeline import VerifyEmailPipeline
from .schemas import (
    ChangePasswordSchema,
    ForgotPasswordSchema,
    LoginSchema,
    MfaVerifySchema,
    RegisterSchema,
    ResetPasswordSchema,
    UpdateMfaSchema,
    UpdateProfileSchema,
    VerifyEmailSchema,
)

PENDING_VERIFICATION_EMAIL_SESSION_KEY = "pending_verification_email"
PENDING_MFA_EMAIL_SESSION_KEY = "pending_mfa_email"


# ---------------------------------------------------------------------------
# Page views — these ONLY render templates. All real work happens through the
# API views below, which the templates call via JavaScript fetch requests.
# ---------------------------------------------------------------------------

def landing_page(request):
    return render(request, "landing.html")


def register_page(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "auth/register.html")


def login_page(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "auth/login.html")


def logout_page(request):
    AnalyticsService.track(
        "user.logged_out",
        request=request,
        status="succeeded",
        page="logout",
    )
    auth_logout(request)
    return redirect("login")


@login_required(login_url="login")
def profile_page(request):
    return render(request, "profile.html")


def _profile_payload(user):
    full_name = (user.full_name or "").strip()
    parts = [p for p in full_name.split() if p]
    if len(parts) >= 2:
        initials = (parts[0][0] + parts[-1][0]).upper()
    elif parts:
        initials = parts[0][:2].upper()
    else:
        initials = (user.email or "?")[:2].upper()
    return {
        "full_name": full_name,
        "law_firm_name": user.law_firm_name or "",
        "email": user.email,
        "phone_number": user.phone_number or "",
        "mfa_enabled": bool(getattr(user, "mfa_enabled", False)),
        "email_verified": bool(user.email_verified),
        "initials": initials,
    }

def forgot_password_page(request):
    return render(request, "auth/forgot_password.html")


def reset_password_page(request):
    return render(request, "auth/reset_password.html")


def verify_email_page(request):
    if not EMAIL_VERIFICATION_ENABLED:
        return redirect("login")
    email = request.session.get(PENDING_VERIFICATION_EMAIL_SESSION_KEY, "")
    return render(request, "auth/verify_email.html", {"email": email})


def mfa_otp_page(request):
    email = request.session.get(PENDING_MFA_EMAIL_SESSION_KEY, "")
    return render(request, "auth/mfa_otp.html", {"email": email})


# ---------------------------------------------------------------------------
# API views
# ---------------------------------------------------------------------------

class BaseAuthApiView(APIView):
    """Template-method base class shared by every auth API endpoint:
    validate the request body against `schema_class`, delegate the actual
    use case to `handle()`, and always respond with a consistent envelope.
    """

    schema_class = None
    def handle(self, request, schema):
        raise NotImplementedError

    def post(self, request):
        try:
            data = request.data.dict() if hasattr(request.data, "dict") else dict(request.data)
            try:
                schema = self.schema_class(**data)
            except ValidationError as e:
                message = e.errors()[0]["msg"].replace("Value error, ", "")
                return Response(error_response(message=message), status=status.HTTP_400_BAD_REQUEST)

            success, message, payload = self.handle(request, schema)
            if success:
                return Response(success_response(message=message, data=payload), status=status.HTTP_200_OK)
            return Response(error_response(message=message), status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error in {self.__class__.__name__}: {e}")
            return Response(
                error_response(message=f"Error in {self.__class__.__name__}: {e}"),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class BaseResendOtpApiView(APIView):
    """Shared by the two "resend code" endpoints. Subclasses just configure
    which OTP purpose to regenerate and which session key holds the pending
    email address."""

    purpose = None
    session_key = None

    def post(self, request):
        try:
            email = request.session.get(self.session_key)
            if not email:
                return Response(
                    error_response(message="Your session has expired. Please start again."),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            pipeline = ResendOtpPipeline()
            success, message, _ = pipeline.process_item({"purpose": self.purpose, "email": email})
            response = success_response(message=message) if success else error_response(message=message)
            return Response(response, status=status.HTTP_200_OK if success else status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error in {self.__class__.__name__}: {e}")
            return Response(
                error_response(message=f"Error in {self.__class__.__name__}: {e}"),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class RegisterViewApi(BaseAuthApiView):
    schema_class = RegisterSchema

    def handle(self, request, schema):
        pipeline = RegisterUserPipeline()
        success, message, payload = pipeline.process_item(schema.model_dump())
        if success and payload and payload.get("requires_verification"):
            request.session[PENDING_VERIFICATION_EMAIL_SESSION_KEY] = schema.email
        AnalyticsService.track(
            "user.signed_up" if success else "user.signup_failed",
            request=request,
            email=schema.email,
            status="succeeded" if success else "failed",
            page="register",
            message=message,
            metadata={"requires_verification": bool(payload and payload.get("requires_verification"))},
        )
        return success, message, payload


class LoginViewApi(BaseAuthApiView):
    schema_class = LoginSchema

    def handle(self, request, schema):
        pipeline = LoginPipeline()
        success, message, user = pipeline.process_item(schema.model_dump())
        if not success:
            AnalyticsService.track(
                "user.login_failed",
                request=request,
                email=schema.email,
                status="failed",
                page="login",
                message=message,
            )
            return False, message, None

        # Pipeline returns the user when MFA is not required; None when an OTP was sent.
        if user is not None:
            auth_login(request, user)
            AnalyticsService.track(
                "user.logged_in",
                request=request,
                user=user,
                email=schema.email,
                status="succeeded",
                page="login",
                metadata={"mfa": False},
            )
            return True, message, {"requires_mfa": False}

        request.session[PENDING_MFA_EMAIL_SESSION_KEY] = schema.email
        AnalyticsService.track(
            "user.login_mfa_required",
            request=request,
            email=schema.email,
            status="started",
            page="login",
        )
        return True, message, {"requires_mfa": True}


class MfaVerifyViewApi(BaseAuthApiView):
    schema_class = MfaVerifySchema

    def handle(self, request, schema):
        email = request.session.get(PENDING_MFA_EMAIL_SESSION_KEY)
        if not email:
            return False, "Your session has expired. Please login again.", None

        pipeline = MfaVerifyPipeline()
        success, message, user = pipeline.process_item({"email": email, "otp": schema.otp})
        if success and user:
            auth_login(request, user)
            del request.session[PENDING_MFA_EMAIL_SESSION_KEY]
            AnalyticsService.track(
                "user.logged_in",
                request=request,
                user=user,
                email=email,
                status="succeeded",
                page="mfa",
                metadata={"mfa": True},
            )
        else:
            AnalyticsService.track(
                "user.login_failed",
                request=request,
                email=email,
                status="failed",
                page="mfa",
                message=message,
                metadata={"mfa": True},
            )
        return success, message, None


class ResendMfaOtpViewApi(BaseResendOtpApiView):
    purpose = "mfa"
    session_key = PENDING_MFA_EMAIL_SESSION_KEY


class ForgotPasswordViewApi(BaseAuthApiView):
    schema_class = ForgotPasswordSchema

    def handle(self, request, schema):
        pipeline = ForgotPasswordPipeline()
        reset_base_url = request.build_absolute_uri(reverse("reset_password"))
        return pipeline.process_item({**schema.model_dump(), "reset_base_url": reset_base_url})


class ResetPasswordViewApi(BaseAuthApiView):
    schema_class = ResetPasswordSchema

    def handle(self, request, schema):
        pipeline = ResetPasswordPipeline()
        return pipeline.process_item(schema.model_dump())


class VerifyEmailViewApi(BaseAuthApiView):
    schema_class = VerifyEmailSchema

    def handle(self, request, schema):
        email = request.session.get(PENDING_VERIFICATION_EMAIL_SESSION_KEY)
        if not email:
            return False, "Your session has expired. Please register again.", None

        pipeline = VerifyEmailPipeline()
        success, message, _ = pipeline.process_item({"email": email, "otp": schema.otp})
        if success:
            del request.session[PENDING_VERIFICATION_EMAIL_SESSION_KEY]
        return success, message, None


class ResendVerifyEmailOtpViewApi(BaseResendOtpApiView):
    purpose = "verify_email"
    session_key = PENDING_VERIFICATION_EMAIL_SESSION_KEY


class ProfileApi(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            success_response(message="Profile fetched", data=_profile_payload(request.user)),
            status=status.HTTP_200_OK,
        )

    def patch(self, request):
        try:
            data = request.data.dict() if hasattr(request.data, "dict") else dict(request.data)
            try:
                schema = UpdateProfileSchema(**data)
            except ValidationError as e:
                message = e.errors()[0]["msg"].replace("Value error, ", "")
                return Response(error_response(message=message), status=status.HTTP_400_BAD_REQUEST)

            user = request.user
            user.full_name = schema.full_name
            user.law_firm_name = schema.law_firm_name
            user.phone_number = schema.phone_number
            user.save(update_fields=["full_name", "law_firm_name", "phone_number"])
            return Response(
                success_response(message="Profile updated", data=_profile_payload(user)),
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.error(f"Error in ProfileApi.patch: {e}")
            return Response(error_response(message=f"Error updating profile: {e}"), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ChangePasswordApi(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            data = request.data.dict() if hasattr(request.data, "dict") else dict(request.data)
            try:
                schema = ChangePasswordSchema(**data)
            except ValidationError as e:
                message = e.errors()[0]["msg"].replace("Value error, ", "")
                return Response(error_response(message=message), status=status.HTTP_400_BAD_REQUEST)

            user = request.user
            if not user.check_password(schema.current_password):
                return Response(error_response(message="Current password is incorrect"), status=status.HTTP_400_BAD_REQUEST)

            user.set_password(schema.new_password)
            user.save(update_fields=["password"])
            # Keep the user logged in after password change.
            auth_login(request, user)
            return Response(success_response(message="Password updated"), status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error in ChangePasswordApi: {e}")
            return Response(error_response(message=f"Error updating password: {e}"), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UpdateMfaApi(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            data = request.data.dict() if hasattr(request.data, "dict") else dict(request.data)
            try:
                schema = UpdateMfaSchema(**data)
            except ValidationError as e:
                message = e.errors()[0]["msg"].replace("Value error, ", "")
                return Response(error_response(message=message), status=status.HTTP_400_BAD_REQUEST)

            user = request.user
            user.mfa_enabled = bool(schema.enabled)
            user.save(update_fields=["mfa_enabled"])
            msg = "Email OTP enabled" if user.mfa_enabled else "Email OTP disabled"
            return Response(
                success_response(message=msg, data=_profile_payload(user)),
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.error(f"Error in UpdateMfaApi: {e}")
            return Response(error_response(message=f"Error updating MFA: {e}"), status=status.HTTP_500_INTERNAL_SERVER_ERROR)