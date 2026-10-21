"""Helpers to enumerate every routed view."""
from django.urls import URLPattern, URLResolver, get_resolver


def all_routes(resolver=None, prefix=""):
    resolver = resolver or get_resolver()
    for p in resolver.url_patterns:
        if isinstance(p, URLResolver):
            yield from all_routes(p, prefix + str(p.pattern))
        elif isinstance(p, URLPattern):
            yield prefix + str(p.pattern), p.callback
