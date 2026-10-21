"""AI-risk register operations (R-2, OQ3)."""
from __future__ import annotations

from collections import Counter

from django.db import transaction

from apps.audit.log import record
from apps.catalog.models import Taxonomy
from apps.core import clock

from .models import AIRisk, AIRiskRequirementLink

ORDER = ["treatment_in_place", "evidence_stale", "assessed_planned", "accepted", "not_applicable", "not_assessed"]
LABEL = {"not_assessed": "not assessed", "assessed_planned": "assessed – treatment planned",
         "treatment_in_place": "treatment in place – evidence attached", "evidence_stale": "evidence stale",
         "accepted": "accepted with rationale", "not_applicable": "not applicable with rationale"}


class RiskError(ValueError):
    def __init__(self, message, field=None):
        super().__init__(message)
        self.message, self.field = message, field


def summary(risks) -> dict:
    counts = Counter(r.display_stage for r in risks)
    return {"total": sum(counts.values()), "breakdown": [(LABEL[k], counts[k]) for k in ORDER if counts[k]]}


@transaction.atomic
def create_risk(request, *, version, name, description="", attack_class="", taxonomy_item=None):
    r = AIRisk.objects.create(vendor_tenant_id=version.vendor_tenant_id, version=version, name=name.strip(),
                              description=description.strip(), attack_class=attack_class,
                              taxonomy_item=taxonomy_item)
    record(request, area="airisks", action="added_risk", target=r, target_label=r.name,
           new={"name": r.name, "attack_class": attack_class,
                "taxonomy": f"{taxonomy_item.taxonomy.code} {taxonomy_item.ref}" if taxonomy_item else None})
    return r


@transaction.atomic
def seed_from_taxonomy(request, *, version, taxonomy: Taxonomy) -> int:
    if not taxonomy.seedable:
        raise RiskError(f"{taxonomy.name}: licence check {taxonomy.licence_status}. Seeding is available once "
                        "the licence is cleared.")
    existing = set(AIRisk.objects.filter(version=version).values_list("taxonomy_item_id", flat=True))
    n = 0
    for item in taxonomy.items.all():
        if item.pk in existing:
            continue
        AIRisk.objects.create(vendor_tenant_id=version.vendor_tenant_id, version=version, name=item.name,
                              description=item.description, attack_class=item.attack_class, taxonomy_item=item)
        n += 1
    record(request, area="airisks", action="seeded_register", target=version, target_label=str(version),
           new={"taxonomy": taxonomy.code, "risks_created": n})
    return n


@transaction.atomic
def change_stage(request, risk_id, *, stage, planned_treatment="", rationale="", review_by=None, owner=None,
                 row_version: int) -> AIRisk:
    r = AIRisk.objects.select_for_update().get(pk=risk_id)
    if r.row_version != row_version:
        raise RiskError("Someone changed this risk since you opened it. Review their change before saving yours.")
    if stage not in AIRisk.Stage.values:
        raise RiskError("Choose a handling stage.", "stage")
    if stage == "assessed_planned" and not planned_treatment.strip():
        raise RiskError("Planned treatment is required.", "planned_treatment")
    if stage == "treatment_in_place":
        if not r.evidence.exists():
            raise RiskError("Add at least one evidence item first.", "stage")
        if review_by is None:
            raise RiskError("A review-by date is required.", "review_by")
    if stage in ("accepted", "not_applicable") and not rationale.strip():
        raise RiskError("A rationale is required. It is visible to your customers.", "rationale")
    old = {"stage": r.display_stage, "owner": r.owner.display_name if r.owner else None}
    r.stage = stage
    r.planned_treatment = planned_treatment.strip() or r.planned_treatment
    r.rationale = rationale.strip() if stage in ("accepted", "not_applicable") else r.rationale
    r.review_by = review_by or r.review_by
    r.owner = owner
    r.updated_by, r.updated_at = request.user, clock.now()
    r.row_version += 1
    r.save()
    record(request, area="airisks", action="stage_change", target=r, target_label=r.name, old=old,
           new={"stage": r.display_stage, "owner": owner.display_name if owner else None,
                "review_by": r.review_by, "rationale": r.rationale})
    return r


@transaction.atomic
def mark_reviewed(request, risk) -> None:
    today = clock.now().date()
    AIRisk.objects.filter(pk=risk.pk).update(last_reviewed_on=today)
    record(request, area="airisks", action="marked_reviewed", target=risk, target_label=risk.name,
           old={"last_reviewed": risk.last_reviewed_on}, new={"last_reviewed": today})


@transaction.atomic
def link_requirement(request, risk, requirement) -> None:
    AIRiskRequirementLink.objects.get_or_create(vendor_tenant_id=risk.vendor_tenant_id, ai_risk=risk,
                                                requirement=requirement)
    record(request, area="airisks", action="linked_requirement", target=risk, target_label=risk.name,
           new={"requirement": requirement.citation})
