from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from Enterprise_Legal_AI_Case_Management_Platform.logger import logger
from auth_app.models import User


class AuthenticationService:
    def check_email_already_exists(self, email):
        try:
            user = User.objects.filter(email=email).first()
            if user:
                return True, "Email already exists"
            return False, "Email does not exist"
        except Exception as e:
            logger.error(f"Error checking email already exists: {e}")
            return False, f"Error checking email already exists: {e}"

    def register_user(self, data):
        try:
            User.objects.create_user(
                full_name=data['full_name'],
                law_firm_name=data['law_firm_name'],
                email=data['email'],
                password=data['password']
            )
            return True, "User registered successfully"
        except Exception as e:
            logger.error(f"Error registering user: {e}")
            return False, f"Error registering user: {e}"

    def get_user_by_email(self, email):
        return User.objects.filter(email=email).first()

    def authenticate_user(self, email, password):
        try:
            user = self.get_user_by_email(email)
            if not user or not user.check_password(password):
                return False, "Invalid email or password", None
            if not user.is_active:
                return False, "This account has been deactivated", None
            return True, "Credentials verified", user
        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            return False, f"Error authenticating user: {e}", None

    def mark_email_verified(self, email):
        try:
            user = self.get_user_by_email(email)
            if not user:
                return False, "User not found"
            user.email_verified = True
            user.save(update_fields=["email_verified"])
            return True, "Email verified successfully"
        except Exception as e:
            logger.error(f"Error marking email verified: {e}")
            return False, f"Error marking email verified: {e}"

    def generate_password_reset_token(self, user):
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        return uidb64, token

    def validate_password_reset_token(self, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.filter(pk=uid).first()
        except (TypeError, ValueError, OverflowError):
            return None
        if user and default_token_generator.check_token(user, token):
            return user
        return None

    def update_password(self, user, new_password):
        try:
            user.set_password(new_password)
            user.save(update_fields=["password"])
            return True, "Password updated successfully"
        except Exception as e:
            logger.error(f"Error updating password: {e}")
            return False, f"Error updating password: {e}"
