from django.conf import settings


class SecurityHeadersMiddleware:
    """Strict CSP (no inline script or style) and related headers."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response.setdefault("Content-Security-Policy", settings.CONTENT_SECURITY_POLICY)
        response.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        response.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        if getattr(request, "tenant_ctx", None) is not None:
            response.setdefault("Cache-Control", "no-store")
        return response
