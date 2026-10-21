"""Reference data (R-X1): nothing regulation-specific is hard-coded.

Loaded from YAML in data/catalog/ by `manage.py load_catalog`. Global, read-only
for application roles; no tenant column.
"""
from django.db import models


class AnnexIIICategory(models.Model):
    code = models.CharField(max_length=16, primary_key=True)  # e.g. "5(b)"
    label = models.CharField(max_length=300)
    citation = models.CharField(max_length=100)  # e.g. "AI Act Annex III 5(b)"
    supported = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=0)

    class Meta:
        db_table = "annex_iii_category"
        ordering = ["sort_order", "code"]


class RequirementSet(models.Model):
    code = models.CharField(max_length=64, primary_key=True)
    title = models.CharField(max_length=300)
    source_citation = models.CharField(max_length=300)
    official_url = models.URLField(max_length=500)
    context_note = models.TextField(blank=True)
    draft = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)

    class Meta:
        db_table = "requirement_set"
        ordering = ["sort_order", "code"]


class Requirement(models.Model):
    id = models.CharField(max_length=64, primary_key=True)  # stable ID, e.g. "CRA-AI-I-2a"
    requirement_set = models.ForeignKey(RequirementSet, on_delete=models.PROTECT, related_name="requirements")
    citation = models.CharField(max_length=100)
    short_title = models.CharField(max_length=200)
    official_url = models.URLField(max_length=500)
    pending_oj_check = models.BooleanField(default=True)
    context_only = models.BooleanField(default=False)  # e.g. CRA Art. 12, Recital 51: no status
    attack_class = models.CharField(max_length=64, blank=True)  # Art. 15(5) split, from data
    sort_order = models.IntegerField(default=0)

    class Meta:
        db_table = "requirement"
        ordering = ["requirement_set__sort_order", "sort_order", "id"]


class CategoryRequirementSet(models.Model):
    category = models.ForeignKey(AnnexIIICategory, on_delete=models.PROTECT)
    requirement_set = models.ForeignKey(RequirementSet, on_delete=models.PROTECT)

    class Meta:
        db_table = "category_requirement_set"
        constraints = [models.UniqueConstraint(fields=["category", "requirement_set"], name="crs_unique")]


class Taxonomy(models.Model):
    class LicenceStatus(models.TextChoices):
        PENDING = "pending"
        CLEARED = "cleared"
        HOLD = "hold"

    code = models.CharField(max_length=64, primary_key=True)
    name = models.CharField(max_length=300)
    source_url = models.URLField(max_length=500)
    licence = models.CharField(max_length=100)
    attribution = models.TextField(blank=True)
    licence_status = models.CharField(max_length=16, choices=LicenceStatus.choices,
                                      default=LicenceStatus.PENDING)

    class Meta:
        db_table = "taxonomy"

    @property
    def seedable(self):
        return self.licence_status == self.LicenceStatus.CLEARED


class TaxonomyItem(models.Model):
    taxonomy = models.ForeignKey(Taxonomy, on_delete=models.PROTECT, related_name="items")
    ref = models.CharField(max_length=64)
    name = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    attack_class = models.CharField(max_length=64, blank=True)
    sample = models.BooleanField(default=False)

    class Meta:
        db_table = "taxonomy_item"
        constraints = [models.UniqueConstraint(fields=["taxonomy", "ref"], name="taxonomy_item_ref")]
