"""Keycloak over plain OIDC (mozilla-django-oidc).

Users are provisioned (vendor) or invited (customer); OIDC never creates users.
MFA is enforced in Keycloak (realm export in infra/keycloak/). We additionally
refuse a sign-in whose ID token doesn't carry an MFA authentication method
(`amr`), so a misconfigured realm can't silently drop MFA.
"""
import time

from mozilla_django_oidc.auth import OIDCAuthenticationBackend

MFA_AMR = {"otp", "mfa", "hwk", "swk", "webauthn", "passkey"}


class TrackerOIDCBackend(OIDCAuthenticationBackend):
    def filter_users_by_claims(self, claims):
        sub = claims.get("sub")
        if not sub:
            return self.UserModel.objects.none()
        return self.UserModel.objects.filter(oidc_subject=sub, is_active=True)

    def verify_claims(self, claims):
        return bool(claims.get("sub")) and super().verify_claims(claims)

    def get_or_create_user(self, access_token, id_token, payload):
        amr = set(payload.get("amr") or [])
        if not amr & MFA_AMR:
            return None  # S-0: "MFA not set up" -> blocked
        user = super().get_or_create_user(access_token, id_token, payload)
        if user is not None and self.request is not None:
            record_auth_time(self.request, payload.get("auth_time"))
        return user


def record_auth_time(request, auth_time=None):
    """Store when the user last authenticated (for step-up, D6)."""
    request.session["auth_time"] = int(auth_time or time.time())
    request.session["session_started"] = int(time.time())
