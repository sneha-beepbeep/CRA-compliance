"""Catalog loader: validates and upserts data/catalog/*.yaml (R-X1).

File kinds (key ``kind``):

* ``categories``       Annex III categories and which requirement sets attach to each.
* ``requirement_set``  one set with its requirement rows.
* ``taxonomy``         a risk taxonomy (data/catalog/taxonomies/) with licence status.

Validation is strict and runs before anything is written; the whole load is one
transaction. Rows are upserted by stable ID and never deleted (statuses reference
them); rows missing from the YAML are reported as ``retired``.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from django.conf import settings
from django.db import transaction

SCHEMA_VERSION = 1
CATALOG_DIR = Path(settings.BASE_DIR) / "data" / "catalog"
CITATION_RE = re.compile(r"^(CRA|AI Act) (Art\. \d+|Annex [IVX]+|Recital \d+)")
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.\-]{1,63}$")
OFFICIAL_URL_RE = re.compile(r"^https://eur-lex\.europa\.eu/")
LICENCE_STATUSES = {"pending", "cleared", "hold"}
ATTACK_CLASSES = {"", "data_poisoning", "model_poisoning", "adversarial_examples",
                  "confidentiality_attacks", "model_flaws"}


class CatalogError(ValueError):
    pass


@dataclass
class LoadReport:
    categories: int = 0
    requirement_sets: int = 0
    requirements: int = 0
    taxonomies: int = 0
    taxonomy_items: int = 0
    draft_rows: int = 0
    pending_oj_rows: int = 0
    retired: list[str] = field(default_factory=list)


def _need(doc: dict, keys: list[str], where: str):
    missing = [k for k in keys if k not in doc]
    if missing:
        raise CatalogError(f"{where}: missing {', '.join(missing)}")


def read_documents(root: Path = CATALOG_DIR) -> list[tuple[Path, dict]]:
    docs = []
    for path in sorted(root.rglob("*.yaml")):
        with path.open(encoding="utf-8") as fh:
            doc = yaml.safe_load(fh)
        if not isinstance(doc, dict):
            raise CatalogError(f"{path.name}: not a mapping")
        _need(doc, ["kind", "schema_version"], path.name)
        if doc["schema_version"] != SCHEMA_VERSION:
            raise CatalogError(f"{path.name}: schema_version {doc['schema_version']} != {SCHEMA_VERSION}")
        docs.append((path, doc))
    return docs


def validate(docs: list[tuple[Path, dict]]) -> None:
    req_ids: set[str] = set()
    set_codes: set[str] = set()
    referenced_sets: set[str] = set()
    for path, doc in docs:
        where = path.name
        kind = doc["kind"]
        if kind == "requirement_set":
            _need(doc, ["code", "title", "source_citation", "official_url", "draft", "requirements"], where)
            if doc["code"] in set_codes:
                raise CatalogError(f"{where}: duplicate set code {doc['code']}")
            set_codes.add(doc["code"])
            if not OFFICIAL_URL_RE.match(doc["official_url"]):
                raise CatalogError(f"{where}: official_url must be an EUR-Lex https URL")
            for i, row in enumerate(doc["requirements"], 1):
                w = f"{where} row {i}"
                _need(row, ["id", "citation", "short_title", "official_url", "pending_oj_check"], w)
                if not ID_RE.match(str(row["id"])):
                    raise CatalogError(f"{w}: bad id {row['id']!r}")
                if row["id"] in req_ids:
                    raise CatalogError(f"{w}: duplicate requirement id {row['id']}")
                req_ids.add(row["id"])
                if not CITATION_RE.match(row["citation"]):
                    raise CatalogError(f"{w}: citation {row['citation']!r} not in the design 15.3 format")
                if not isinstance(row["pending_oj_check"], bool):
                    raise CatalogError(f"{w}: pending_oj_check must be true or false")
                if not OFFICIAL_URL_RE.match(row["official_url"]):
                    raise CatalogError(f"{w}: official_url must be an EUR-Lex https URL")
                if row.get("attack_class", "") not in ATTACK_CLASSES:
                    raise CatalogError(f"{w}: unknown attack_class {row.get('attack_class')!r}")
                if len(row["short_title"]) > 120:
                    raise CatalogError(f"{w}: short_title too long")
        elif kind == "categories":
            _need(doc, ["categories"], where)
            for c in doc["categories"]:
                _need(c, ["code", "label", "citation", "supported", "requirement_sets"], f"{where} {c.get('code')}")
                referenced_sets.update(c["requirement_sets"])
        elif kind == "taxonomy":
            _need(doc, ["code", "name", "source_url", "licence", "licence_status", "items"], where)
            if doc["licence_status"] not in LICENCE_STATUSES:
                raise CatalogError(f"{where}: licence_status must be one of {sorted(LICENCE_STATUSES)}")
            refs = set()
            for item in doc["items"]:
                _need(item, ["ref", "name"], f"{where} item")
                if item["ref"] in refs:
                    raise CatalogError(f"{where}: duplicate item ref {item['ref']}")
                refs.add(item["ref"])
                if item.get("attack_class", "") not in ATTACK_CLASSES:
                    raise CatalogError(f"{where}: unknown attack_class {item.get('attack_class')!r}")
        else:
            raise CatalogError(f"{where}: unknown kind {kind!r}")
    unknown = referenced_sets - set_codes
    if unknown:
        raise CatalogError(f"categories reference unknown requirement sets: {sorted(unknown)}")


@transaction.atomic
def load(root: Path = CATALOG_DIR) -> LoadReport:
    from .models import (AnnexIIICategory, CategoryRequirementSet, Requirement, RequirementSet, Taxonomy,
                         TaxonomyItem)

    docs = read_documents(root)
    validate(docs)
    rep = LoadReport()
    seen_reqs: set[str] = set()

    for order, (_, doc) in enumerate(d for d in docs if d[1]["kind"] == "requirement_set"):
        rs, _ = RequirementSet.objects.update_or_create(code=doc["code"], defaults=dict(
            title=doc["title"], source_citation=doc["source_citation"], official_url=doc["official_url"],
            context_note=doc.get("context_note", ""), draft=bool(doc["draft"]), sort_order=doc.get("sort_order", order)))
        rep.requirement_sets += 1
        for i, row in enumerate(doc["requirements"]):
            Requirement.objects.update_or_create(id=row["id"], defaults=dict(
                requirement_set=rs, citation=row["citation"], short_title=row["short_title"],
                official_url=row["official_url"], pending_oj_check=row["pending_oj_check"],
                context_only=bool(row.get("context_only", False)), attack_class=row.get("attack_class", ""),
                sort_order=i))
            seen_reqs.add(row["id"])
            rep.requirements += 1
            rep.pending_oj_rows += row["pending_oj_check"]
            rep.draft_rows += bool(doc["draft"]) or bool(row.get("draft", False))

    for _, doc in (d for d in docs if d[1]["kind"] == "categories"):
        for i, c in enumerate(doc["categories"]):
            cat, _ = AnnexIIICategory.objects.update_or_create(code=c["code"], defaults=dict(
                label=c["label"], citation=c["citation"], supported=bool(c["supported"]), sort_order=i))
            rep.categories += 1
            CategoryRequirementSet.objects.filter(category=cat).exclude(
                requirement_set_id__in=c["requirement_sets"]).delete()
            for code in c["requirement_sets"]:
                CategoryRequirementSet.objects.get_or_create(category=cat, requirement_set_id=code)

    for _, doc in (d for d in docs if d[1]["kind"] == "taxonomy"):
        tx, _ = Taxonomy.objects.update_or_create(code=doc["code"], defaults=dict(
            name=doc["name"], source_url=doc["source_url"], licence=doc["licence"],
            attribution=doc.get("attribution", ""), licence_status=doc["licence_status"]))
        rep.taxonomies += 1
        for item in doc["items"]:
            TaxonomyItem.objects.update_or_create(taxonomy=tx, ref=item["ref"], defaults=dict(
                name=item["name"], description=item.get("description", ""),
                attack_class=item.get("attack_class", ""), sample=bool(item.get("sample", False))))
            rep.taxonomy_items += 1

    rep.retired = sorted(set(Requirement.objects.values_list("id", flat=True)) - seen_reqs)
    return rep
