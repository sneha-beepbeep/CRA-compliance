"""Art. 14 screens: S-7, S-8, S-8a, S-9, filings, S-11, S-13, drills, strip partial."""
from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from apps.authz.capabilities import Capability, has_capability, requires
from apps.core import clock
from apps.registry.models import Deployment, Product, ProductVersion
from apps.tenancy.models import UserAccount

from . import deadlines as engine
from . import localtime, services
from .forms import (AwarenessEditForm, CloseForm, DetailsForm, DrillOutcomeForm, LogEventForm, ReassignForm,
                    ReopenForm, StartClockForm, TimeForm)
from .models import Art14Event


def _event(pk) -> Art14Event:
    ev = (Art14Event.objects.select_related("assigned_responder", "started_by", "product", "product_version")
          .filter(pk=pk).first())
    if ev is None:
        raise Http404
    return ev


def _responder_qs(request):
    ids = [u.pk for u in services.responders(request.tenant_ctx.vendor_tenant_id)]
    return UserAccount.objects.filter(pk__in=ids).order_by("display_name")


def _preview(form, rule):
    """Deadline preview while typing (S-8); computed server-side from the authoritative engine."""
    if not form.is_bound or not form.is_valid() or not form.cleaned_data.get("awareness_at"):
        return None
    aw = form.cleaned_data["awareness_at"]
    d = engine.compute(engine.EventTimes(form.cleaned_data["event_type"], aw), clock.now(), rule)
    return d


@requires(Capability.ART14_CLOCKS_VIEW)
def strip(request):
    return render(request, "ui/strip.html")


@requires(Capability.ART14_CLOCKS_VIEW)
def event_list(request):
    show = request.GET.get("show", "open")
    qs = Art14Event.objects.select_related("assigned_responder", "started_by", "product")
    counts = {"open": qs.filter(status="open", is_drill=False).count(),
              "closed": qs.exclude(status="open").filter(is_drill=False).count(),
              "drills": qs.filter(is_drill=True).count()}
    if show == "closed":
        qs = qs.exclude(status="open").filter(is_drill=False)
    elif show == "drills":
        qs = qs.filter(is_drill=True)
    else:
        show = "open"
        qs = qs.filter(status="open", is_drill=False)
    rows = services.event_rows(qs)
    if show == "open":
        rows.sort(key=lambda r: r.sort_key)
    return render(request, "art14/event_list.html", {
        "rows": rows, "show": show, "counts": counts,
        "is_responder": has_capability(request.tenant_ctx, Capability.ART14_DETAILS),
        "real_events_enabled": services.real_events_enabled(), "now": clock.now()})


def _create(request, form_cls, template, via, drill):
    ctx = request.tenant_ctx
    responders = _responder_qs(request)
    kw = {"products": Product.objects.all(), "responders": responders, "user_tz": request.user.time_zone}
    if form_cls is LogEventForm:
        kw.update(versions=ProductVersion.objects.all(), deployments=Deployment.objects.all())
    if not responders.exists():
        managers = UserAccount.objects.filter(tenant_id=ctx.tenant_id, is_access_manager=True)
        return render(request, "art14/no_responder.html", {"managers": managers}, status=409)
    form = form_cls(request.POST or None, initial={"assignee": request.user.pk if form_cls is LogEventForm else None},
                    **kw)
    preview = _preview(form, services.month_rule())
    if request.method == "POST" and form.is_valid() and form.cleaned_data.get("awareness_at") \
            and request.POST.get("action") == "save":
        cd = form.cleaned_data
        is_drill = drill or bool(cd.get("is_drill"))
        try:
            ev = services.create_event(
                request, event_type=cd["event_type"], awareness_at=cd["awareness_at"], product=cd["product"],
                assignee=cd["assignee"], is_drill=is_drill, via=via, version=cd.get("version"),
                deployments=list(cd.get("deployments") or []), title=cd.get("title", ""),
                description=cd.get("description", ""), component=cd.get("affected_component", ""),
                vector=cd.get("vector", ""))
        except services.EventError as e:
            form.add_error(e.field if e.field in form.fields else None, e.message)
        else:
            if via == Art14Event.StartedVia.START_CLOCK:
                request.session[f"started:{ev.pk}"] = True
                return redirect(f"/events/{ev.pk}/started/")
            messages.info(request, f"{ev.ref} logged. Clocks started.")
            return redirect(f"/events/{ev.pk}/")
    stale_warning = None
    if preview and preview.early_warning.state is engine.State.OVERDUE:
        stale_warning = "The early warning deadline for this time has already passed. The event will show as overdue."
    tz = form.data.get(f"{form.time_prefix}_tz") or request.user.time_zone
    return render(request, template, {
        "form": form, "preview": preview, "drill": drill, "stale_warning": stale_warning,
        "dst_note": localtime.dst_note(preview.notification.start_at, preview.notification.due_at, tz) if preview else None,
        "real_events_enabled": services.real_events_enabled(), "preview_tz": tz})


@requires(Capability.ART14_DETAILS)
@require_http_methods(["GET", "POST"])
def log_event(request):
    drill = request.GET.get("drill") == "1" or request.POST.get("drill") == "1"
    if not drill and not services.real_events_enabled():
        drill = True  # C6: drills only until the pentest passes
    return _create(request, LogEventForm, "art14/log_event.html", Art14Event.StartedVia.LOG_EVENT, drill)


@requires(Capability.ART14_START_CLOCK)
@require_http_methods(["GET", "POST"])
def start_clock(request):
    return _create(request, StartClockForm, "art14/start_clock.html", Art14Event.StartedVia.START_CLOCK,
                   drill=not services.real_events_enabled())


@requires(Capability.ART14_START_CLOCK)
def started(request, pk):
    ev = _event(pk)
    if not request.session.pop(f"started:{ev.pk}", False):
        raise Http404  # shown once, to the starter only
    d = engine.compute(ev.times(), clock.now(), services.month_rule())
    return render(request, "art14/started.html", {"ev": ev, "d": d})


@requires(Capability.ART14_CLOCKS_VIEW)
def detail(request, pk):
    ev = _event(pk)
    d = engine.compute(ev.times(), clock.now(), services.month_rule())
    if not has_capability(request.tenant_ctx, Capability.ART14_DETAILS):
        # Role checked on every request (D4): non-responders get the restricted view.
        return render(request, "art14/detail_restricted.html", {"ev": ev, "d": d,
                                                                 "responders": _responder_qs(request)})
    services.record_detail_view(request, ev)
    detail_obj = getattr(ev, "detail", None) if hasattr(ev, "detail") else None
    tz = request.user.time_zone
    return render(request, "art14/detail.html", {
        "ev": ev, "d": d, "detail": detail_obj, "deployments": [x.deployment for x in ev.affected_deployments.select_related("deployment")],
        "dst_note": localtime.dst_note(d.notification.start_at, d.notification.due_at, tz),
        "recalculated_recently": ev.last_recalculated_at and (clock.now() - ev.last_recalculated_at).total_seconds() < 86400,
        "time_forms": {w: TimeForm(initial={"which": w, "row_version": ev.row_version}, user_tz=tz,
                                   prefix=w) for w in ("early_warning", "notification", "final_report", "fix")},
        "close_form": CloseForm(initial={"row_version": ev.row_version}),
        "reopen_form": ReopenForm(initial={"row_version": ev.row_version}),
        "drill_form": DrillOutcomeForm() if ev.is_drill and not hasattr(ev, "drill_outcome") else None,
        "month_rule_note": services.SystemSetting.get("month_rule_note")
        if ev.event_type == "severe_incident" else None,
        "fix_warning": engine.Warning_.FIX_BEFORE_AWARENESS in d.warnings,
    })


@requires(Capability.ART14_DETAILS)
@require_POST
def record_time(request, pk):
    ev = _event(pk)
    which = request.POST.get("which_prefix", "")
    if which not in ("early_warning", "notification", "final_report", "fix"):
        raise Http404
    form = TimeForm(request.POST, user_tz=request.user.time_zone, prefix=which)
    if form.is_valid() and form.cleaned_data.get("when_at"):
        try:
            services.record_time(request, ev.pk, which=which, when=form.cleaned_data["when_at"],
                                 reason=form.cleaned_data.get("reason", ""),
                                 row_version=form.cleaned_data["row_version"])
            messages.info(request, "Time recorded.")
            return redirect(f"/events/{ev.pk}/")
        except services.EventError as e:
            form.add_error(None, e.message)
    return render(request, "art14/time_form.html", {"ev": ev, "form": form, "which": which}, status=400)


@requires(Capability.ART14_DETAILS)
@require_http_methods(["GET", "POST"])
def edit_details(request, pk):
    ev = _event(pk)
    detail_obj = getattr(ev, "detail", None) if hasattr(ev, "detail") else None
    kw = {"versions": ProductVersion.objects.filter(product=ev.product), "deployments": Deployment.objects.filter(product=ev.product)}
    initial = {"version": ev.product_version_id,
               "deployments": [x.deployment_id for x in ev.affected_deployments.all()]}
    if detail_obj:
        initial.update(title=detail_obj.title, description=detail_obj.description,
                       affected_component=detail_obj.affected_component, vector=detail_obj.vector)
    form = DetailsForm(request.POST or None, initial=initial, **kw)
    if request.method == "POST" and form.is_valid():
        cd = form.cleaned_data
        services.update_details(request, ev, title=cd["title"], description=cd["description"],
                                component=cd["affected_component"], vector=cd["vector"], version=cd["version"],
                                deployments=list(cd["deployments"]))
        messages.info(request, "Details saved.")
        return redirect(f"/events/{ev.pk}/")
    return render(request, "art14/edit_details.html", {"ev": ev, "form": form})


@requires(Capability.ART14_AWARENESS_EDIT)
@require_http_methods(["GET", "POST"])
def edit_awareness(request, pk):
    ev = _event(pk)
    form = AwarenessEditForm(request.POST or None, initial={"row_version": ev.row_version},
                             user_tz=request.user.time_zone)
    changes = None
    if request.method == "POST" and form.is_valid() and form.cleaned_data.get("awareness_at"):
        new_aw = form.cleaned_data["awareness_at"]
        changes = services.preview_awareness(ev, new_aw)
        if request.POST.get("action") == "confirm":
            try:
                services.edit_awareness(request, ev.pk, new_awareness=new_aw, reason=form.cleaned_data["reason"],
                                        row_version=form.cleaned_data["row_version"])
                messages.info(request, "Awareness time changed. Deadlines recalculated.")
                return redirect(f"/events/{ev.pk}/")
            except services.EventError as e:
                form.add_error(None, e.message)
    return render(request, "art14/edit_awareness.html", {"ev": ev, "form": form, "changes": changes})


@requires(Capability.ART14_CLOSE)
@require_POST
def close(request, pk):
    ev = _event(pk)
    form = CloseForm(request.POST)
    if form.is_valid():
        try:
            services.close_event(request, ev.pk, outcome=form.cleaned_data["outcome"],
                                 rationale=form.cleaned_data["rationale"], row_version=form.cleaned_data["row_version"])
            messages.info(request, f"{ev.ref} closed.")
            return redirect(f"/events/{ev.pk}/")
        except services.EventError as e:
            form.add_error(None, e.message)
    return render(request, "art14/close.html", {"ev": ev, "form": form}, status=400)


@requires(Capability.ART14_CLOSE)
@require_POST
def reopen(request, pk):
    ev = _event(pk)
    form = ReopenForm(request.POST)
    if form.is_valid():
        try:
            services.reopen_event(request, ev.pk, reason=form.cleaned_data["reason"],
                                  row_version=form.cleaned_data["row_version"])
            messages.info(request, f"{ev.ref} reopened.")
            return redirect(f"/events/{ev.pk}/")
        except services.EventError as e:
            form.add_error(None, e.message)
    return render(request, "art14/reopen.html", {"ev": ev, "form": form}, status=400)


@requires(Capability.ART14_DETAILS)
@require_POST
def take_over(request, pk):
    ev = _event(pk)
    services.reassign(request, ev.pk, assignee=request.user, take_over=True)
    return redirect(f"/events/{ev.pk}/")


@requires(Capability.ART14_REASSIGN)
@require_http_methods(["GET", "POST"])
def reassign(request, pk):
    ev = _event(pk)
    form = ReassignForm(request.POST or None, responders=_responder_qs(request))
    if request.method == "POST" and form.is_valid():
        services.reassign(request, ev.pk, assignee=form.cleaned_data["assignee"])
        messages.info(request, f"{ev.ref} assigned to {form.cleaned_data['assignee'].display_name}. "
                               "The dashboard does not notify them.")
        return redirect("/events/")
    return render(request, "art14/reassign.html", {"ev": ev, "form": form})


@requires(Capability.ART14_DRILL)
@require_POST
def drill_outcome(request, pk):
    ev = _event(pk)
    form = DrillOutcomeForm(request.POST)
    if form.is_valid():
        try:
            services.record_drill_outcome(request, ev, answer=form.cleaned_data["answer"],
                                          notes=form.cleaned_data["notes"])
        except services.EventError as e:
            messages.error(request, e.message)
    return redirect(f"/events/{ev.pk}/")
