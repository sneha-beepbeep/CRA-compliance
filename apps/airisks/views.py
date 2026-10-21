"""S-5 AI-risk register and S-6 risk detail (R-2, OQ3)."""
from django import forms
from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from apps.audit.models import AuditEvent
from apps.authz.capabilities import Capability, requires
from apps.catalog.models import Taxonomy
from apps.registry.services import requirements_for_category
from apps.requirements.views import EvidenceForm
from apps.requirements.services import add_evidence as add_evidence_item
from apps.tenancy.models import UserAccount
from apps.ui.context_processors import current_version

from . import services
from .models import AIRisk

ATTACK_CLASSES = [("", "–"), ("data_poisoning", "Data poisoning"), ("model_poisoning", "Model poisoning"),
                  ("adversarial_examples", "Adversarial examples"),
                  ("confidentiality_attacks", "Confidentiality attacks"), ("model_flaws", "Model flaws")]


class RiskForm(forms.Form):
    name = forms.CharField(label="Risk", max_length=300)
    description = forms.CharField(label="Description", widget=forms.Textarea, required=False)
    attack_class = forms.ChoiceField(label="AI Act Art. 15(5) attack class", choices=ATTACK_CLASSES, required=False)


class StageForm(forms.Form):
    stage = forms.ChoiceField(label="Handling stage", choices=AIRisk.Stage.choices)
    planned_treatment = forms.CharField(label="Planned treatment", widget=forms.Textarea, required=False)
    rationale = forms.CharField(label="Rationale (visible to your customers)", widget=forms.Textarea, required=False)
    review_by = forms.DateField(label="Review by", required=False, widget=forms.DateInput(attrs={"type": "date"}))
    owner = forms.ModelChoiceField(label="Owner", queryset=None, required=False)
    row_version = forms.IntegerField(widget=forms.HiddenInput)

    def __init__(self, *a, owners, **kw):
        super().__init__(*a, **kw)
        self.fields["owner"].queryset = owners


def _owners(request):
    return UserAccount.objects.filter(tenant_id=request.tenant_ctx.tenant_id, is_active=True).order_by("display_name")


def _risk(pk):
    r = AIRisk.objects.select_related("version", "version__product", "owner", "taxonomy_item",
                                      "taxonomy_item__taxonomy").filter(pk=pk).first()
    if r is None:
        raise Http404
    return r


@requires(Capability.AIRISKS_VIEW)
def risk_list(request):
    version = current_version(request)
    risks = list(AIRisk.objects.filter(version=version).select_related("owner", "taxonomy_item__taxonomy")) if version else []
    return render(request, "airisks/list.html", {
        "version": version, "risks": risks, "summary": services.summary(risks),
        "taxonomies": Taxonomy.objects.all().order_by("name"), "form": RiskForm()})


@requires(Capability.AIRISKS_EDIT)
@require_POST
def risk_add(request):
    version = current_version(request)
    if version is None:
        raise Http404
    form = RiskForm(request.POST)
    if form.is_valid():
        r = services.create_risk(request, version=version, **form.cleaned_data)
        return redirect(f"/ai-risks/{r.pk}/")
    return render(request, "airisks/list.html", {"version": version, "risks": [], "summary": services.summary([]),
                                                 "form": form, "taxonomies": Taxonomy.objects.all()}, status=400)


@requires(Capability.AIRISKS_EDIT)
@require_POST
def seed(request):
    version = current_version(request)
    tx = Taxonomy.objects.filter(pk=request.POST.get("taxonomy", "")).first()
    if version is None or tx is None:
        raise Http404
    try:
        n = services.seed_from_taxonomy(request, version=version, taxonomy=tx)
        messages.info(request, f"{n} risks added from {tx.name}, each in “not assessed”.")
    except services.RiskError as e:
        messages.error(request, e.message)
    return redirect("/ai-risks/")


@requires(Capability.AIRISKS_VIEW)
@require_http_methods(["GET", "POST"])
def risk_detail(request, pk):
    r = _risk(pk)
    form = StageForm(request.POST or None, owners=_owners(request), initial={
        "stage": r.stage, "planned_treatment": r.planned_treatment, "rationale": r.rationale,
        "review_by": r.review_by, "owner": r.owner_id, "row_version": r.row_version})
    if request.method == "POST" and form.is_valid():
        cd = form.cleaned_data
        try:
            services.change_stage(request, r.pk, **cd)
            messages.info(request, "Handling stage saved.")
            return redirect(f"/ai-risks/{r.pk}/")
        except services.RiskError as e:
            form.add_error(e.field if e.field in form.fields else None, e.message)
    linkable = requirements_for_category(r.version.product.category_id).filter(context_only=False)
    return render(request, "airisks/detail.html", {
        "r": r, "form": form, "evidence_form": EvidenceForm(), "evidence": r.evidence.select_related("added_by"),
        "links": r.requirement_links.select_related("requirement"), "linkable": linkable,
        "history": AuditEvent.objects.filter(target_id=str(r.pk), area="airisks").order_by("-seq")[:50]},
        status=400 if request.method == "POST" else 200)


@requires(Capability.AIRISKS_EDIT)
@require_POST
def risk_evidence(request, pk):
    r = _risk(pk)
    form = EvidenceForm(request.POST)
    if form.is_valid():
        add_evidence_item(request, ai_risk=r, **form.cleaned_data)
        messages.info(request, "Evidence item added.")
    else:
        messages.error(request, "Not saved. Check the evidence fields.")
    return redirect(f"/ai-risks/{r.pk}/")


@requires(Capability.AIRISKS_EDIT)
@require_POST
def risk_reviewed(request, pk):
    r = _risk(pk)
    services.mark_reviewed(request, r)
    messages.info(request, "Marked reviewed today.")
    return redirect(f"/ai-risks/{r.pk}/")


@requires(Capability.AIRISKS_EDIT)
@require_POST
def risk_link(request, pk):
    from apps.catalog.models import Requirement
    r = _risk(pk)
    req = Requirement.objects.filter(pk=request.POST.get("requirement", ""), context_only=False).first()
    if req is None:
        raise Http404
    services.link_requirement(request, r, req)
    return redirect(f"/ai-risks/{r.pk}/")
