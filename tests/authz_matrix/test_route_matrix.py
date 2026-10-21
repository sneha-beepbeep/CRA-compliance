"""Route matrix (blocks merges): for every role and every route that takes an
object ID, another tenant's object and a non-existent UUID give byte-identical
responses. Plus a smoke pass over own objects (no 500s) and role checks."""
import uuid

import pytest
from django.test import Client

from apps.authz.capabilities import Capability
from apps.tenancy.models import RoleGrant
from tests.routes import all_routes

pytestmark = pytest.mark.django_db

OBJECT_ROUTES = [(p, cb) for p, cb in all_routes() if "<uuid:pk>" in p]


def foreign_id(path, b):
    if path.startswith("requirements/"):
        return b.status.pk
    if path.startswith("ai-risks/"):
        return b.risk.pk
    if path.startswith("events/"):
        return b.event.pk
    if path.startswith("setup/users/"):
        return b.manager.pk
    raise AssertionError(f"no foreign object mapping for {path}")


def own_id(path, a):
    return foreign_id(path, a)


def personas(a):
    return {"vendor_admin": a.admin, "responder": a.manager, "customer": a.customer_user}


def url(path, pk):
    return "/" + path.replace("<uuid:pk>", str(pk))


@pytest.fixture
def clients(world):
    out = {}
    for name, user in personas(world["A"]).items():
        c = Client()
        c.force_login(user)
        out[name] = c
    return out


def test_object_routes_are_mapped():
    assert len(OBJECT_ROUTES) >= 15


@pytest.mark.parametrize("path", [p for p, _ in OBJECT_ROUTES])
@pytest.mark.parametrize("method", ["get", "post"])
@pytest.mark.parametrize("persona", ["vendor_admin", "responder", "customer"])
def test_foreign_object_indistinguishable_from_missing(world, clients, path, method, persona):
    c = clients[persona]
    foreign = getattr(c, method)(url(path, foreign_id(path, world["B"])))
    missing = getattr(c, method)(url(path, uuid.uuid4()))
    assert foreign.status_code == missing.status_code, (path, foreign.status_code, missing.status_code)
    assert foreign.status_code in (404, 405)
    assert foreign.content == missing.content


@pytest.mark.parametrize("path", [p for p, cb in all_routes() if cb.capability not in (Capability.PUBLIC,)])
def test_anonymous_is_sent_to_sign_in(world, path):
    pk = foreign_id(path, world["A"]) if "<uuid:pk>" in path else None
    r = Client().get(url(path, pk) if pk else "/" + path)
    assert r.status_code == 302 and r["Location"] == "/sign-in/"


VENDOR_ONLY = [p for p, cb in all_routes() if cb.capability not in (Capability.PUBLIC, Capability.AUTHENTICATED)]


@pytest.mark.parametrize("path", VENDOR_ONLY)
def test_customer_gets_404_on_every_vendor_route(world, clients, path):
    pk = own_id(path, world["A"]) if "<uuid:pk>" in path else None
    r = clients["customer"].get(url(path, pk) if pk else "/" + path)
    assert r.status_code == 404


GET_PAGES = [p for p, cb in all_routes() if cb.capability not in (Capability.PUBLIC,)]


@pytest.mark.parametrize("path", GET_PAGES)
@pytest.mark.parametrize("persona", ["vendor_admin", "responder"])
def test_smoke_own_objects_never_500(world, clients, path, persona):
    pk = own_id(path, world["A"]) if "<uuid:pk>" in path else None
    r = clients[persona].get(url(path, pk) if pk else "/" + path)
    assert r.status_code in (200, 302, 400, 404, 405, 409), (path, r.status_code)
    assert r.status_code != 500


def test_non_responder_gets_restricted_view_without_details(world, clients):
    a = world["A"]
    r = clients["vendor_admin"].get(f"/events/{a.event.pk}/")
    assert r.status_code == 200
    body = r.content.decode()
    assert "Details restricted to incident responders" in body
    assert "Secret title" not in body and "Exploit detail" not in body


def test_responder_sees_details_and_view_is_audited(world, clients):
    from apps.audit.models import AuditEvent
    a = world["A"]
    r = clients["responder"].get(f"/events/{a.event.pk}/")
    assert "Secret title alpha" in r.content.decode()
    assert AuditEvent.objects.filter(action="viewed_details", target_id=str(a.event.pk)).count() == 1


def test_revoking_responder_takes_effect_on_next_request(world, clients):
    a = world["A"]
    c = clients["responder"]
    assert "Secret title alpha" in c.get(f"/events/{a.event.pk}/").content.decode()
    RoleGrant.objects.filter(user=a.manager).update(revoked_at=a.event.started_at)
    body = c.get(f"/events/{a.event.pk}/").content.decode()
    assert "Secret title alpha" not in body and "Details restricted to incident responders" in body
    assert c.get(f"/events/{a.event.pk}/details").status_code == 404


def test_strip_never_shows_other_tenants(world, clients):
    body = clients["responder"].get("/clocks/strip").content.decode()
    assert "E-0001" in body
    assert str(world["B"].event.pk) not in body and "Beta" not in body


def test_404_page_has_no_request_specific_content(world, clients):
    a = clients["responder"].get(f"/events/{uuid.uuid4()}/")
    b = Client().get("/does-not-exist/")
    assert a.content == b.content
