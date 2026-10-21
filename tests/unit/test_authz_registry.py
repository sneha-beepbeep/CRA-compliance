"""Every route declares a capability; the matrix matches design spec 2.3."""
from apps.authz.capabilities import MATRIX, Capability, Role, has_capability
from apps.tenancy.context import TenantContext
from tests.routes import all_routes


def test_every_route_declares_a_capability():
    missing = [path for path, cb in all_routes() if not isinstance(getattr(cb, "capability", None), Capability)]
    assert missing == [], f"routes without a declared capability: {missing}"


def test_only_sign_in_routes_are_public_or_context_exempt():
    public = {path for path, cb in all_routes() if cb.capability is Capability.PUBLIC}
    assert public <= {"sign-in/", "signed-out/", "sign-out/", "oidc/authenticate/", "oidc/callback/", "dev/login/"}
    exempt = {path for path, cb in all_routes() if getattr(cb, "db_context_exempt", False)}
    assert exempt == public


def test_matrix_covers_every_capability():
    assert set(MATRIX) == set(Capability) - {Capability.PUBLIC, Capability.AUTHENTICATED}


def test_incident_detail_capabilities_are_responder_only():
    for cap in (Capability.ART14_DETAILS, Capability.ART14_AWARENESS_EDIT, Capability.ART14_RECLASSIFY,
                Capability.ART14_CLOSE, Capability.ART14_MARK_INFORMED, Capability.ART14_DRILL):
        assert MATRIX[cap] == {Role.INCIDENT_RESPONDER}, cap


def test_customer_capabilities_are_customer_only_and_vendor_caps_exclude_customers():
    for cap, roles in MATRIX.items():
        if cap.value.startswith(("customer_", "activity_sharing")):
            assert roles == {Role.CUSTOMER_ADMIN}
        else:
            assert Role.CUSTOMER_ADMIN not in roles, cap


def ctx(workspace="vendor", responder=False, manager=False):
    return TenantContext("u", "t", "t", workspace, responder, manager)


def test_role_resolution():
    admin, resp, mgr, cust = ctx(), ctx(responder=True), ctx(manager=True), ctx("customer")
    assert has_capability(admin, Capability.ART14_START_CLOCK) and not has_capability(admin, Capability.ART14_DETAILS)
    assert has_capability(resp, Capability.ART14_DETAILS)
    assert not has_capability(admin, Capability.ROLES_MANAGE) and has_capability(mgr, Capability.ROLES_MANAGE)
    assert not has_capability(cust, Capability.REQUIREMENTS_VIEW) and has_capability(cust, Capability.CUSTOMER_VIEW)
    assert not has_capability(None, Capability.AUTHENTICATED) and has_capability(None, Capability.PUBLIC)
    # a customer flagged as access manager still gets no vendor rights
    assert ctx("customer", manager=True).roles == {"customer_admin"}
