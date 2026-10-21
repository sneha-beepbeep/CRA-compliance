"""Docker build-context evaluation without a Docker daemon.

Implements the .dockerignore rules Docker uses (moby/patternmatcher) for the
pattern forms this repo uses: patterns are evaluated in order, the last match
wins, '!' re-includes, a pattern matching a parent directory matches everything
under it, and '**' matches any number of path segments.
"""
import fnmatch
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_patterns(root: Path = ROOT):
    out = []
    for line in (root / ".dockerignore").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        neg = line.startswith("!")
        pat = os.path.normpath(line[1:] if neg else line).lstrip("/")
        out.append((neg, _compile(pat)))
    return out


def _compile(pat: str):
    rx = ""
    i = 0
    while i < len(pat):
        if pat.startswith("**/", i):
            rx += "(?:.*/)?"
            i += 3
        elif pat.startswith("**", i):
            rx += ".*"
            i += 2
        else:
            c = pat[i]
            rx += "[^/]*" if c == "*" else "[^/]" if c == "?" else re.escape(c)
            i += 1
    return re.compile(rx + r"\Z")


def _matches(rx, rel: str) -> bool:
    parts = rel.split("/")
    return any(rx.match("/".join(parts[:n])) for n in range(1, len(parts) + 1))


def excluded(rel: str, patterns) -> bool:
    result = False
    for neg, rx in patterns:
        if _matches(rx, rel):
            result = not neg
    return result


def context_files(root: Path = ROOT):
    """Every file Docker would send, pruning excluded dirs nothing can re-include."""
    patterns = load_patterns(root)
    negations = [rx.pattern for neg, rx in patterns if neg]
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        rel_dir = os.path.relpath(dirpath, root)
        rel_dir = "" if rel_dir == "." else rel_dir
        keep = []
        for d in dirnames:
            rel = f"{rel_dir}/{d}" if rel_dir else d
            if excluded(rel, patterns) and not any(n.startswith(re.escape(rel)) for n in negations):
                continue
            keep.append(d)
        dirnames[:] = keep
        for f in filenames:
            rel = f"{rel_dir}/{f}" if rel_dir else f
            if not excluded(rel, patterns):
                files.append(rel)
    return sorted(files)


def fnmatch_any(rel, globs):
    return any(fnmatch.fnmatch(rel, g) for g in globs)
