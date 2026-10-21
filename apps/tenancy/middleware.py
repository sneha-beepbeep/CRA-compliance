"""Wraps each request in a transaction running as app_vendor / app_customer with
the tenant context set (technical plan, "Request context")."""
from django.db import DatabaseError, transaction
from django.urls import Resolver404, resolve

from . import context


class TenantContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            match = resolve(request.path_info)
            exempt = getattr(match.func, "db_context_exempt", False)
        except Resolver404:
            exempt = False
        if exempt:
            # Sign-in flows need the login role to look up the account.
            request.tenant_ctx = None
            return self.get_response(request)

        # Load the session and the user with the login role's rights, before
        # dropping to the tenant role (django_session isn't visible to it).
        _ = list(request.session.keys())
        user = getattr(request, "user", None)
        if user is not None:
            _ = user.is_authenticated and user.pk
        ctx = context.resolve(user)
        request.tenant_ctx = ctx
        with transaction.atomic():
            context.apply(ctx)
            try:
                response = self.get_response(request)
                if hasattr(response, "render") and callable(response.render) and not response.is_rendered:
                    response.render()
            finally:
                try:
                    context.reset()
                except DatabaseError:
                    pass  # aborted transaction: the rollback restores the role
        return response
