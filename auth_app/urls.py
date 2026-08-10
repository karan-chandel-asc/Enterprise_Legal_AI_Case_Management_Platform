from django.urls import path
from . import views

urlpatterns = [
    # Pages
    path('', views.landing_page, name='landing'),
    path('register/', views.register_page, name='register'),
    path('login/', views.login_page, name='login'),
    path('logout/', views.logout_page, name='logout'),
    path('profile/', views.profile_page, name='profile'),
    path('forgot-password/', views.forgot_password_page, name='forgot_password'),
    path('reset-password/', views.reset_password_page, name='reset_password'),
    path('verify-email/', views.verify_email_page, name='verify_email'),
    path('mfa/', views.mfa_otp_page, name='mfa_otp'),

    # API endpoints
    path('register/api/', views.RegisterViewApi.as_view(), name='register_api'),
    path('login/api/', views.LoginViewApi.as_view(), name='login_api'),
    path('mfa/api/', views.MfaVerifyViewApi.as_view(), name='mfa_verify_api'),
    path('mfa/resend/api/', views.ResendMfaOtpViewApi.as_view(), name='resend_mfa_otp_api'),
    path('forgot-password/api/', views.ForgotPasswordViewApi.as_view(), name='forgot_password_api'),
    path('reset-password/api/', views.ResetPasswordViewApi.as_view(), name='reset_password_api'),
    path('verify-email/api/', views.VerifyEmailViewApi.as_view(), name='verify_email_api'),
    path('verify-email/resend/api/', views.ResendVerifyEmailOtpViewApi.as_view(), name='resend_verify_email_otp_api'),
    path('profile/api/', views.ProfileApi.as_view(), name='profile_api'),
    path('profile/password/api/', views.ChangePasswordApi.as_view(), name='change_password_api'),
    path('profile/mfa/api/', views.UpdateMfaApi.as_view(), name='update_mfa_api'),
]
