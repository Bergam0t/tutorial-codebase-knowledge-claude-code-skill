#!/usr/bin/env python3
"""Report which chapters of a generated tutorial are out of date with the code.

Reads <tutorial>/_generation.json (written by write_record.py) and compares the
content hash of every source file each chapter or page depends on with the file
as it is now. No AI and no network: it is safe to run in CI.

Usage:
  python check_drift.py --repo <repo root> --tutorial <tutorial dir>
                        [--json report.json] [--fail-on stale|never] [--fail-unmapped]

Statuses per chapter or page:
  fresh   every source file it depends on is byte-identical to when it was written
  stale   a source file changed, was deleted, or has appeared since it was written

Also reported (advisory, never stale by themselves):
  tests_changed     test files a chapter relies on changed
  unmapped changes  files changed since the recorded commit that no chapter cites,
                    which may mean a new component or module the tutorial doesn't cover

Exit code: 0 = nothing stale (or --fail-on never); 1 = stale chapters (or unmapped
changes with --fail-unmapped); 2 = no usable record. Standard library only.
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import subprocess
import sys
from pathlib import Path

RECORD = "_generation.json"
DEFAULT_IGNORED_DIRS = {
    ".git", "node_modules", ".venv", "venv", "dist", "build", "__pycache__", "vendor",
    "tests", "test", "docs", "doc", ".github", "_site", "_book", ".quarto",
}
DEFAULT_IGNORED_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".pdf", ".zip", ".gz", ".lock",
    ".md", ".txt", ".rst", ".qmd", ".ipynb", ".csv", ".json.lock",
}
DEFAULT_IGNORED_NAMES = {"package-lock.json", "yarn.lock", "poetry.lock", "uv.lock", "Cargo.lock"}


def blob_hash(path: Path) -> str | None:
    try:
        data = path.read_bytes()
    except OSError:
        return None
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def git(repo: Path, *args: str) -> str | None:
    try:
        r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True,
                           text=True, timeout=60, check=False)
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout if r.returncode == 0 else None


def classify(repo: Path, entries: list[dict]) -> list[dict]:
    changed = []
    for e in entries:
        now = blob_hash(repo / e["path"])
        was = e.get("blob")
        if now == was:
            continue
        reason = "deleted" if now is None else "appeared" if was is None else "changed"
        changed.append({"path": e["path"], "reason": reason})
    return changed


def is_ignored(path: str, tutorial_rel: str | None, args: dict) -> bool:
    p = Path(path)
    if tutorial_rel and (path == tutorial_rel or path.startswith(tutorial_rel.rstrip("/") + "/")):
        return True
    if set(p.parts[:-1]) & DEFAULT_IGNORED_DIRS:
        return True
    if p.name in DEFAULT_IGNORED_NAMES or p.suffix.lower() in DEFAULT_IGNORED_SUFFIXES:
        return True
    excludes = args.get("exclude") or []
    if isinstance(excludes, str):
        excludes = [g.strip() for g in excludes.split(",") if g.strip()]
    if any(fnmatch.fnmatch(path, g) for g in excludes):
        return True
    includes = args.get("include") or []
    if isinstance(includes, str):
        includes = [g.strip() for g in includes.split(",") if g.strip()]
    if includes and not any(fnmatch.fnmatch(path, g) for g in includes):
        return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", required=True, help="repository root the tutorial describes")
    ap.add_argument("--tutorial", required=True, help="tutorial folder containing _generation.json")
    ap.add_argument("--json", help="also write the report to this file")
    ap.add_argument("--fail-on", choices=("stale", "never"), default="stale")
    ap.add_argument("--fail-unmapped", action="store_true",
                    help="also exit 1 when changed files are not covered by any chapter")
    a = ap.parse_args()

    repo, tutorial = Path(a.repo).resolve(), Path(a.tutorial).resolve()
    try:
        rec = json.loads((tutorial / RECORD).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"error: no usable {RECORD} in {tutorial}: {exc}\n"
              "Generate the tutorial with the codebase-tutorial plugin (v1.5.0 or later) first.",
              file=sys.stderr)
        return 2

    items = [("chapter", c) for c in rec.get("chapters", [])] + [("page", p) for p in rec.get("pages", [])]
    results, covered = [], set()
    for kind, it in items:
        files = it.get("files", [])
        covered.update(f["path"] for f in files)
        changed = classify(repo, files)
        tests_changed = classify(repo, it.get("tests", []))
        results.append({
            "kind": kind,
            "id": it.get("id"),
            "name": it.get("name") or it.get("id"),
            "filename": it.get("filename"),
            "audience": it.get("audience"),
            "status": "stale" if changed else "fresh",
            "changed": changed,
            "tests_changed": [t["path"] for t in tests_changed],
        })

    src = rec.get("source", {})
    sha = src.get("commit")
    behind, unmapped = None, []
    if sha and git(repo, "cat-file", "-e", f"{sha}^{{commit}}") is not None:
        n = git(repo, "rev-list", "--count", f"{sha}..HEAD")
        behind = int(n.strip()) if n and n.strip().isdigit() else None
        names = set((git(repo, "diff", "--name-only", sha, "--") or "").split())
        names |= set((git(repo, "ls-files", "--others", "--exclude-standard") or "").split())
        try:
            tutorial_rel = tutorial.relative_to(repo).as_posix()
        except ValueError:
            tutorial_rel = None
        args = rec.get("args", {})
        unmapped = sorted(n for n in names
                          if n not in covered and (repo / n).is_file()
                          and not is_ignored(n, tutorial_rel, args))

    stale = [r for r in results if r["status"] == "stale"]
    report = {
        "tutorial": str(tutorial),
        "plugin_version": rec.get("plugin", {}).get("version"),
        "generated_at": rec.get("generated_at"),
        "commit": sha,
        "commits_behind": behind,
        "dirty_when_generated": src.get("dirty"),
        "results": results,
        "stale_count": len(stale),
        "total": len(results),
        "unmapped_changes": unmapped,
    }
    if a.json:
        Path(a.json).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    short = (sha or "unknown")[:7]
    when = (rec.get("generated_at") or "")[:10]
    line = f"Tutorial generated from commit {short} on {when}"
    if behind is not None:
        line += f"; HEAD is {behind} commit(s) ahead"
    print(line + ".")
    if src.get("dirty"):
        print("Note: it was generated from a working tree with uncommitted changes.")
    for r in results:
        label = f"{r['filename']}" + (f" [{r['audience']}]" if r["audience"] else "")
        if r["status"] == "stale":
            why = "; ".join(f"{c['path']} {c['reason']}" for c in r["changed"])
            print(f"  STALE  {label}: {why}")
        else:
            extra = f" (tests changed: {', '.join(r['tests_changed'])})" if r["tests_changed"] else ""
            print(f"  fresh  {label}{extra}")
    if unmapped:
        print(f"Changed since that commit but cited by no chapter ({len(unmapped)}):")
        for n in unmapped[:25]:
            print(f"  - {n}")
        if len(unmapped) > 25:
            print(f"  ... and {len(unmapped) - 25} more")
    print(f"{len(stale)} of {len(results)} chapters/pages stale.")

    if a.fail_on == "stale" and stale:
        return 1
    if a.fail_unmapped and unmapped:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
