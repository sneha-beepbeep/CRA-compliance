"""Application policy: the design's permission matrix (design spec 2.3) as data.

Every routed view must declare exactly one capability with ``@requires``; the
route-registry test fails the build otherwise. Anything outside the caller's
scope returns the same 404 as an object that doesn't exist (design 11.3).

Database-level enforcement (RLS, app_customer limited to cust_* views) is the
second, independent layer; this module is the first.
"""
from __future__ import annotations

import functools
from enum import StrEnum

from django.http import Http404
from django.shortcuts import redirect


class Role(StrEnum):
    VENDOR_ADMIN = "vendor_admin"
    INCIDENT_RESPONDER = "incident_responder"
    ACCESS_MANAGER = "access_manager"
    CUSTOMER_ADMIN = "customer_admin"


class Capability(StrEnum):
    PUBLIC = "public"                                # sign-in pages, static error pages
    AUTHENTICATED = "authenticated"                  # own profile, sign-out landing
    VENDOR_OVERVIEW = "vendor_overview"
    REGISTRY_EDIT = "registry_edit"                  # products, versions, deployments
    ROLES_MANAGE = "roles_manage"                    # grant/remove responder; invite customers
    REQUIREMENTS_VIEW = "requirements_view"
    REQUIREMENTS_EDIT = "requirements_edit"
    AIRISKS_VIEW = "airisks_view"
    AIRISKS_EDIT = "airisks_edit"
    ART14_CLOCKS_VIEW = "art14_clocks_view"          # "C": states, countdowns, responder, awaiting flag
    ART14_START_CLOCK = "art14_start_clock"          # S-8a (D4)
    ART14_REASSIGN = "art14_reassign"                # proposed 8.3a
    ART14_DETAILS = "art14_details"                  # S-8 log event, S-9 detail, filings
    ART14_AWARENESS_EDIT = "art14_awareness_edit"    # S-11
    ART14_RECLASSIFY = "art14_reclassify"            # S-12 (phase 1b screen)
    ART14_CLOSE = "art14_close"                      # S-13, incl. reopen
    ART14_DRILL = "art14_drill"                      # "+ Log drill", drill outcome
    ART14_MARK_INFORMED = "art14_mark_informed"      # S-10 (phase 1b), step-up
    IMPORT_CSV = "import_csv"                        # S-15 (pilot week 1)
    AUDIT_VIEW = "audit_view"                        # S-16, masked per role
    EXPORTS_VENDOR = "exports_vendor"                # S-17 (phase 1b)
    CUSTOMER_VIEW = "customer_view"                  # S-B1..S-B5 (phase 1b)
    CUSTOMER_EXPORT = "customer_export"              # S-B6 (phase 1b)
    ACTIVITY_SHARING_EDIT = "activity_sharing_edit"  # S-B0, S-B7 (phase 1b)


V, R, AM, C = Role.VENDOR_ADMIN, Role.INCIDENT_RESPONDER, Role.ACCESS_MANAGER, Role.CUSTOMER_ADMIN

# Which roles hold each capability. A responder is always also a vendor admin;
# an access manager is a flag on a vendor admin.
MATRIX: dict[Capability, frozenset[Role]] = {
    Capability.VENDOR_OVERVIEW: frozenset({V}),
    Capability.REGISTRY_EDIT: frozenset({V}),
    Capability.ROLES_MANAGE: frozenset({AM}),
    Capability.REQUIREMENTS_VIEW: frozenset({V}),
    Capability.REQUIREMENTS_EDIT: frozenset({V}),
    Capability.AIRISKS_VIEW: frozenset({V}),
    Capability.AIRISKS_EDIT: frozenset({V}),
    Capability.ART14_CLOCKS_VIEW: frozenset({V}),
    Capability.ART14_START_CLOCK: frozenset({V}),
    Capability.ART14_REASSIGN: frozenset({V}),
    Capability.ART14_DETAILS: frozenset({R}),
    Capability.ART14_AWARENESS_EDIT: frozenset({R}),
    Capability.ART14_RECLASSIFY: frozenset({R}),
    Capability.ART14_CLOSE: frozenset({R}),
    Capability.ART14_DRILL: frozenset({R}),
    Capability.ART14_MARK_INFORMED: frozenset({R}),
    Capability.IMPORT_CSV: frozenset({V}),
    Capability.AUDIT_VIEW: frozenset({V}),
    Capability.EXPORTS_VENDOR: frozenset({V}),
    Capability.CUSTOMER_VIEW: frozenset({C}),
    Capability.CUSTOMER_EXPORT: frozenset({C}),
    Capability.ACTIVITY_SHARING_EDIT: frozenset({C}),
}


def roles_of(ctx) -> frozenset[str]:
    return ctx.roles if ctx is not None else frozenset()


def has_capability(ctx, cap: Capability) -> bool:
    if cap is Capability.PUBLIC:
        return True
    if ctx is None:
        return False
    if cap is Capability.AUTHENTICATED:
        return True
    return bool(MATRIX[cap] & roles_of(ctx))


def requires(cap: Capability, *, db_context_exempt: bool = False):
    """Declare and enforce a view's capability.

    Unauthenticated callers of non-public views are sent to sign-in. Authenticated
    callers without the capability get Http404, identical to a missing object.
    """

    def decorate(view):
        @functools.wraps(view)
        def wrapped(request, *args, **kwargs):
            if cap is not Capability.PUBLIC:
                ctx = getattr(request, "tenant_ctx", None)
                if ctx is None:
                    return redirect("/sign-in/")
                if not has_capability(ctx, cap):
                    raise Http404
            return view(request, *args, **kwargs)

        wrapped.capability = cap
        wrapped.db_context_exempt = db_context_exempt
        return wrapped

    return decorate
