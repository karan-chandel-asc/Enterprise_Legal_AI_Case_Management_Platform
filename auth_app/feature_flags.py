# Toggle switches for auth behaviour. Flip these back to True to re-enable
# the corresponding flow without deleting any of the underlying code.

# When True, logging in requires verifying a one-time code emailed to the
# user before a session is created. When False, a correct password logs the
# user in immediately and redirects straight to the dashboard.
MFA_LOGIN_ENABLED = False

# When True, a newly registered user must verify a one-time code emailed to
# them before their account is usable. When False, new accounts are marked
# verified immediately on signup and skip the OTP page entirely.
EMAIL_VERIFICATION_ENABLED = False
