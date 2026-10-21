"""S-3 requirements list and S-4 requirement detail (R-1)."""
from itertools import groupby

from django import forms
from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from apps.airisks.models import AIRiskRequirementLink
from apps.audit.models import AuditEvent
from apps.authz.capabilities import Capability, requires
from apps.catalog.models import Requirement
from apps.registry.services import requirements_for_category
from apps.ui.context_processors import current_version

from . import services
from .models import RATIONALE_MIN, EvidenceItem, RequirementStatus


class StatusForm(forms.Form):
    status = forms.ChoiceField(label="Status", choices=RequirementStatus.Status.choices)
    review_by = forms.DateField(label="Review by", required=False, help_text="YYYY-MM-DD. Required for evidence attached.",
                                widget=forms.DateInput(attrs={"type": "date"}))
    rationale = forms.CharField(label="Rationale (visible to your customers)", widget=forms.Textarea, required=False,
                                help_text=f"Required for not applicable, at least {RATIONALE_MIN} characters.")
    note = forms.CharField(label="Note (optional)", widget=forms.Textarea, required=False)
    row_version = forms.IntegerField(widget=forms.HiddenInput)


class EvidenceForm(forms.Form):
    title = forms.CharField(label="Title", max_length=300)
    type = forms.ChoiceField(label="Type", choices=EvidenceItem.Type.choices)
    evidence_date = forms.DateField(label="Date of evidence", widget=forms.DateInput(attrs={"type": "date"}))
    url = forms.URLField(label="Link (optional; never shown to customers)", required=False, assume_scheme="https")


@requires(Capability.REQUIREMENTS_VIEW)
def requirement_list(request):
    version = current_version(request)
    if version is None:
        return render(request, "requirements/list.html", {"version": None})
    statuses = list(RequirementStatus.objects.filter(version=version)
                    .select_related("requirement", "requirement__requirement_set")
                    .order_by("requirement__requirement_set__sort_order", "requirement__sort_order"))
    summary = services.summary(statuses)
    f_status = request.GET.get("status", "")
    f_set = request.GET.get("set", "")
    q = request.GET.get("q", "").strip().lower()
    shown = [s for s in statuses
             if (not f_status or s.display_status == f_status)
             and (not f_set or s.requirement.requirement_set_id == f_set)
             and (not q or q in s.requirement.citation.lower() or q in s.requirement.short_title.lower())]
    links = {}
    for link in AIRiskRequirementLink.objects.filter(ai_risk__version=version):
        links[link.requirement_id] = links.get(link.requirement_id, 0) + 1
    groups = [(rs, list(items)) for rs, items in groupby(shown, key=lambda s: s.requirement.requirement_set)]
    context_rows = requirements_for_category(version.product.category_id).filter(context_only=True)
    return render(request, "requirements/list.html", {
        "version": version, "summary": summary, "groups": groups, "links": links, "context_rows": context_rows,
        "sets": sorted({s.requirement.requirement_set for s in statuses}, key=lambda r: r.sort_order),
        "f_status": f_status, "f_set": f_set, "q": request.GET.get("q", ""),
        "status_filters": [("not_started", "not started"), ("in_progress", "in progress"),
                           ("evidence_attached", "evidence attached"), ("evidence_stale", "evidence stale"),
                           ("not_applicable", "not applicable")]})


def _status(pk):
    s = RequirementStatus.objects.select_related("requirement", "requirement__requirement_set", "version",
                                                 "updated_by", "carried_forward_from").filter(pk=pk).first()
    if s is None:
        raise Http404
    return s


@requires(Capability.REQUIREMENTS_VIEW)
@require_http_methods(["GET", "POST"])
def requirement_detail(request, pk):
    s = _status(pk)
    form = StatusForm(request.POST or None, initial={"status": s.status, "review_by": s.review_by,
                                                      "rationale": s.rationale, "row_version": s.row_version})
    if request.method == "POST":
        if form.is_valid():
            cd = form.cleaned_data
            try:
                services.change_status(request, s.pk, status=cd["status"], review_by=cd["review_by"],
                                       rationale=cd["rationale"], note=cd["note"], row_version=cd["row_version"])
                messages.info(request, "Status saved.")
                return redirect(f"/requirements/{s.pk}/")
            except services.StatusError as e:
                form.add_error(e.field if e.field in form.fields else None, e.message)
    history = AuditEvent.objects.filter(target_id=str(s.pk), area="requirements").order_by("-seq")[:50]
    links = AIRiskRequirementLink.objects.filter(requirement=s.requirement, ai_risk__version=s.version).select_related("ai_risk")
    return render(request, "requirements/detail.html", {
        "s": s, "form": form, "evidence_form": EvidenceForm(), "evidence": s.evidence.select_related("added_by"),
        "links": links, "history": history}, status=400 if request.method == "POST" else 200)


@requires(Capability.REQUIREMENTS_EDIT)
@require_POST
def add_evidence(request, pk):
    s = _status(pk)
    form = EvidenceForm(request.POST)
    if form.is_valid():
        services.add_evidence(request, requirement_status=s, **form.cleaned_data)
        messages.info(request, "Evidence item added.")
        return redirect(f"/requirements/{s.pk}/")
    return render(request, "requirements/evidence_error.html", {"s": s, "form": form}, status=400)
