"""Catalog YAML schema validation (no database needed) and placeholder-content guards."""
from pathlib import Path

import pytest
import yaml

from apps.catalog.loader import CATALOG_DIR, CatalogError, read_documents, validate


def docs():
    return read_documents(CATALOG_DIR)


def test_shipped_catalog_validates():
    validate(docs())


def test_every_requirement_row_is_pending_oj_check_and_draft():
    rows = [(d, r) for _, d in docs() if d["kind"] == "requirement_set" for r in d["requirements"]]
    assert len(rows) == 29
    assert all(r["pending_oj_check"] is True for _, r in rows)
    assert all(d["draft"] is True and r["short_title"] == "DRAFT – pending legal review" for d, r in rows)


def test_expected_citations_present():
    cits = {r["citation"] for _, d in docs() if d["kind"] == "requirement_set" for r in d["requirements"]}
    expected = ({"CRA Annex I, Part I(1)"} | {f"CRA Annex I, Part I(2)({c})" for c in "abcdefghijklm"}
                | {f"CRA Annex I, Part II({n})" for n in range(1, 9)} | {f"AI Act Art. 15({n})" for n in range(1, 6)})
    assert expected <= cits


def test_taxonomies_pending_and_samples_marked():
    tx = [d for _, d in docs() if d["kind"] == "taxonomy"]
    assert {t["code"] for t in tx} == {"mitre_atlas", "nist_ai_100_2"}
    for t in tx:
        assert t["licence_status"] == "pending"
        assert all(i.get("sample") is True and i["name"].startswith("SAMPLE – ") for i in t["items"])
        assert len(t["items"]) <= 5


def _with(tmp_path: Path, doc: dict, name="x.yaml"):
    (tmp_path / name).write_text(yaml.safe_dump(doc), encoding="utf-8")
    return read_documents(tmp_path)


BASE = {"kind": "requirement_set", "schema_version": 1, "code": "s", "title": "S", "source_citation": "x",
        "official_url": "https://eur-lex.europa.eu/eli/reg/2024/2847/oj", "draft": True,
        "requirements": [{"id": "R-1", "citation": "CRA Annex I, Part I(1)", "short_title": "t",
                          "official_url": "https://eur-lex.europa.eu/x", "pending_oj_check": True}]}


@pytest.mark.parametrize("mutate,msg", [
    (lambda d: d["requirements"][0].pop("pending_oj_check"), "missing pending_oj_check"),
    (lambda d: d["requirements"][0].update(pending_oj_check="yes"), "pending_oj_check must be"),
    (lambda d: d["requirements"][0].update(citation="Article 14"), "design 15.3 format"),
    (lambda d: d["requirements"][0].update(official_url="http://example.com"), "EUR-Lex"),
    (lambda d: d["requirements"].append(dict(d["requirements"][0])), "duplicate requirement id"),
    (lambda d: d["requirements"][0].update(attack_class="lasers"), "unknown attack_class"),
    (lambda d: d.update(schema_version=2), "schema_version"),
])
def test_validation_errors(tmp_path, mutate, msg):
    import copy
    d = copy.deepcopy(BASE)
    mutate(d)
    with pytest.raises(CatalogError, match=msg):
        validate(_with(tmp_path, d))


def test_categories_must_reference_known_sets(tmp_path):
    (tmp_path / "a.yaml").write_text(yaml.safe_dump(BASE), encoding="utf-8")
    cat = {"kind": "categories", "schema_version": 1, "categories": [
        {"code": "5(b)", "label": "x", "citation": "AI Act Annex III 5(b)", "supported": True,
         "requirement_sets": ["nope"]}]}
    (tmp_path / "b.yaml").write_text(yaml.safe_dump(cat), encoding="utf-8")
    with pytest.raises(CatalogError, match="unknown requirement sets"):
        validate(read_documents(tmp_path))


def test_taxonomy_licence_status_enforced(tmp_path):
    t = {"kind": "taxonomy", "schema_version": 1, "code": "t", "name": "T", "source_url": "https://x",
         "licence": "x", "licence_status": "probably-fine", "items": []}
    with pytest.raises(CatalogError, match="licence_status"):
        validate(_with(tmp_path, t))
