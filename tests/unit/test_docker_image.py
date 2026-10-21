"""Docker build context (allowlist) and Dockerfile checks, without a Docker daemon."""
import re
from pathlib import Path

from tests.docker_context import ROOT, context_files, excluded, load_patterns

DOCKERFILE = (ROOT / "infra" / "Dockerfile").read_text(encoding="utf-8")


def test_matcher_semantics():
    pats = load_patterns()
    assert excluded("regtech_cyber.db", pats) and excluded(".playwright/chromium-1248/x", pats)
    assert not excluded("apps/art14/deadlines.py", pats)
    assert excluded("apps/art14/__pycache__/deadlines.cpython-312.pyc", pats)
    assert excluded("apps/tenancy/devdata.py", pats)


def test_context_is_small_and_contains_only_allowed_paths():
    files = context_files()
    allowed_top = {"pyproject.toml", "uv.lock", "manage.py", "tracker", "apps", "templates", "static", "data", "db"}
    assert {f.split("/")[0] for f in files} <= allowed_top
    size = sum((ROOT / f).stat().st_size for f in files)
    assert size < 5 * 1024 * 1024, f"context is {size} bytes"


def test_context_excludes_dev_test_and_local_environments():
    files = context_files()
    for prefix in (".playwright/", ".venv/", ".venv-bootstrap/", ".uv/", ".localpg", ".git/", "tests/", "docs/",
                   ".claude/", "scripts/", ".github/", "infra/", ".hypothesis/", ".pytest_cache/", "staticfiles/"):
        assert not any(f.startswith(prefix) for f in files), prefix
    assert not any("__pycache__" in f or f.endswith(".pyc") for f in files)
    assert "apps/tenancy/devdata.py" not in files
    assert "apps/tenancy/management/commands/seed_dev.py" not in files


def test_every_copy_source_is_in_the_context():
    files = context_files()
    for line in DOCKERFILE.splitlines():
        m = re.match(r"COPY (?!--from)(.+) \S+$", line.strip())
        if not m:
            continue
        for src in m.group(1).split():
            assert any(f == src or f.startswith(src.rstrip("/") + "/") for f in files), src


def test_dockerfile_hardening():
    froms = re.findall(r"^ARG \w+_IMAGE=(\S+)", DOCKERFILE, re.M)
    assert froms and all("@sha256:" in ref and ":latest" not in ref for ref in froms)  # pinned by digest
    stages = DOCKERFILE.split("FROM ${PYTHON_IMAGE} AS runtime")
    assert len(stages) == 2, "multi-stage with a separate runtime stage"
    runtime = stages[1]
    assert "uv" not in re.sub(r"#.*", "", runtime).replace("/app/.venv", "")  # no uv or build tooling at runtime
    assert re.search(r"^USER 10001:10001$", runtime, re.M)  # non-root, numeric
    assert "--no-default-groups" in DOCKERFILE and "--frozen" in DOCKERFILE  # no dev/localpg/browser groups
    assert not re.search(r"^ADD ", DOCKERFILE, re.M)
    assert "chown" not in runtime  # code stays root-owned, read-only to the app user
