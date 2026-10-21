"""Copy rules (design spec 15.2, 10.2): banned wording and the neutral palette.

Scans what users can see: template text and user-facing attributes, string
literals in user-facing Python modules (messages, errors, labels, choices), and
catalog YAML. "Compliance" is allowed only inside the NFR-8 notice.
"""
import ast
import re
from html.parser import HTMLParser
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = sorted((ROOT / "templates").rglob("*.html"))
PY_UI = sorted(p for pattern in ("apps/*/views.py", "apps/*/services.py", "apps/*/forms.py", "apps/*/models.py",
                                 "apps/ui/context_processors.py", "apps/ui/templatetags/*.py", "apps/audit/render.py",
                                 "apps/art14/localtime.py", "apps/art14/deadlines.py") for p in ROOT.glob(pattern))
CATALOG = sorted((ROOT / "data" / "catalog").rglob("*.yaml"))

BANNED = [
    r"\bnon-?compliant\b", r"\bcompliant\b", r"\bcompliance\b",
    r"\bcertified\b", r"\battested\b", r"\bverified\b", r"\bapproved\b",
    r"\bensures?\b", r"\bguarantee[sd]?\b",
    r"\bpassed\b", r"\bfailed\b", r"\bpass/fail\b", r"\bhealthy\b", r"\bhealth\b", r"\bsecure(ly)?\b", r"\bsafe(ly)?\b",
    r"\bready\b", r"\bCRA-ready\b",
    r"\brisk score\b", r"\bseverity rating\b", r"\brobustness rating\b", r"\bscore\b",
    r"\bno incidents\b", r"\bno vulnerabilities\b", r"\ball clear\b",
    r"\bsubmit\b", r"\bnotif(y|ies|ied|ication sent)\b", r"\balerts?\b",
    r"\banonymous\b", r"\bCRM\b", r"\bArt\. 51\b", r"\bbanks?\b",
]
# Phrases the design itself prescribes (15.1, 6.2, 7.2, 8.3a, 10.2, 11.1, 14).
ALLOWED = [
    r"It is not a determination of compliance\.",
    r"It is not a score\.", r"It is not a robustness rating\.",
    r"The dashboard does not notify (them|anyone)\.?",
    r"(date|dates|deadline|already|has) passed",
    r"\(context, not binding\)",
]


def scrub(text: str) -> str:
    for a in ALLOWED:
        text = re.sub(a, " ", text, flags=re.I)
    return text


def violations(text: str):
    t = scrub(text)
    return [m.group(0) for pat in BANNED for m in re.finditer(pat, t, flags=re.I)]


class Visible(HTMLParser):
    ATTRS = {"title", "aria-label", "placeholder", "alt", "data-announce", "data-tab-title"}

    def __init__(self):
        super().__init__()
        self.chunks = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1
        self.chunks += [v for k, v in attrs if k in self.ATTRS and v]
        if tag in ("progress", "meter"):
            self.chunks.append("<progress-or-meter>")

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip:
            self.chunks.append(data)


def template_text(path: Path) -> str:
    raw = path.read_text(encoding="utf-8")
    raw = re.sub(r"\{#.*?#\}", " ", raw, flags=re.S)
    raw = re.sub(r"\{%.*?%\}", " ", raw, flags=re.S)
    raw = re.sub(r"\{\{.*?\}\}", " ", raw, flags=re.S)
    p = Visible()
    p.feed(raw)
    return " ".join(p.chunks)


def python_strings(path: Path) -> str:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant):
                docstrings.add(id(node.body[0].value))
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docstrings:
            s = node.value
            if " " in s.strip() or s[:1].isupper():  # user-facing copy, not identifiers
                out.append(s)
    return "\n".join(out)


def catalog_text(path: Path) -> str:
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    vals = [doc.get(k, "") for k in ("title", "context_note", "name")]
    for r in doc.get("requirements", []) + doc.get("categories", []) + doc.get("items", []):
        vals += [r.get("short_title", ""), r.get("label", ""), r.get("name", ""), r.get("citation", "")]
    return "\n".join(v for v in vals if v)


@pytest.mark.parametrize("path", TEMPLATES, ids=lambda p: str(p.relative_to(ROOT)))
def test_templates(path):
    assert violations(template_text(path)) == []


@pytest.mark.parametrize("path", PY_UI, ids=lambda p: str(p.relative_to(ROOT)))
def test_python_user_strings(path):
    assert violations(python_strings(path)) == []


@pytest.mark.parametrize("path", CATALOG, ids=lambda p: str(p.relative_to(ROOT)))
def test_catalog_copy(path):
    assert violations(catalog_text(path)) == []


def test_lint_catches_banned_words():
    assert violations("Your product is CRA-ready and compliant.") != []
    assert violations("No incidents") and violations("Bank A") and violations("pass/fail")
    assert violations("Status reflects information entered by X. It is not a determination of compliance.") == []


def test_no_progress_bars_or_meters():
    for path in TEMPLATES:
        assert "<progress-or-meter>" not in template_text(path), path


# --- Neutral palette (design 10.2): status tokens are greys; no green anywhere ---

CSS = re.sub(r"/\*.*?\*/", " ", (ROOT / "static" / "css" / "app.css").read_text(encoding="utf-8"), flags=re.S)


def rgb(h):
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def test_status_tokens_are_neutral_greys():
    tokens = dict(re.findall(r"--(status-[\w-]+):\s*(#[0-9a-fA-F]{3,6})", CSS))
    assert tokens, "no --status-* tokens found"
    for name, hexv in tokens.items():
        r, g, b = rgb(hexv)
        assert max(r, g, b) - min(r, g, b) <= 16, f"{name} {hexv} is not a neutral grey"


def test_chip_rules_use_only_status_tokens():
    for selector, body in re.findall(r"(\.chip[^{]*)\{([^}]*)\}", CSS):
        for prop, val in re.findall(r"(color|background|border)[\w-]*:\s*([^;]+);", body):
            assert "#" not in val and "rgb" not in val, (selector, prop, val)


def test_no_green_anywhere():
    assert "green" not in CSS.lower()
    for hexv in re.findall(r"#[0-9a-fA-F]{6}\b", CSS):
        r, g, b = rgb(hexv)
        assert not (g > r + 30 and g > b + 30), f"greenish colour {hexv}"
