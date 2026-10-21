"""The pre-built finding table and its views are gone from the knowledge base;
a rebuild reproduces the same counts; nothing book-derived can ship in an image."""
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KB_FILES = ["schema.sql", "build_db.py", "risks.json", "innovations.json", "mitigations.json", "barriers.json"]


def test_rebuild_counts_unchanged(tmp_path):
    for f in KB_FILES:
        shutil.copy(ROOT / f, tmp_path / f)
    subprocess.run([sys.executable, "-I", str(tmp_path / "build_db.py")], check=True, capture_output=True,
                   cwd=tmp_path)
    c = sqlite3.connect(tmp_path / "regtech_cyber.db")
    counts = {t: c.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
              for t in ("risk", "innovation", "mitigation", "mitigation_barrier", "source", "risk_mitigation")}
    assert counts == {"risk": 8, "innovation": 9, "mitigation": 17, "mitigation_barrier": 4, "source": 19,
                      "risk_mitigation": 20}
    names = {r[0] for r in c.execute("SELECT name FROM sqlite_master")}
    assert not names & {"finding", "security_changelog", "cra_deadline_check"}


def test_findings_artifacts_removed():
    assert not (ROOT / "findings.json").exists()
    assert "finding" not in (ROOT / "build_db.py").read_text()
    schema = (ROOT / "schema.sql").read_text()
    assert "CREATE TABLE finding" not in schema and "security_changelog" not in schema


def test_dockerignore_excludes_book_derived_content():
    lines = {line.strip() for line in (ROOT / ".dockerignore").read_text().splitlines()}
    for f in ["regtech_cyber.db", "schema.sql", "build_db.py", "risks.json", "innovations.json", "mitigations.json",
              "barriers.json", "*.ipynb", "docs/"]:
        assert f in lines, f


def test_product_never_reads_the_knowledge_base():
    for py in (ROOT / "apps").rglob("*.py"):
        assert "regtech_cyber" not in py.read_text(), py
