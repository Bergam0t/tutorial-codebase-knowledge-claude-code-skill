#!/usr/bin/env python3
"""Record what a tutorial was generated from, so it can be kept up to date.

Standard library only (Python 3.9+).

Three subcommands:

  info   Print the commit the tutorial is being generated from, as JSON. The
         orchestrator uses it to build the footer line ("Generated from commit ...").

    write_record.py info --repo <repo> [--repo-url <url>]

  write  Write <out>/_generation.json (plus copies of the outline files), recording
         the plugin version, the commit, the resolved options, and a content hash
         for every source file each chapter or page depends on.

    write_record.py write --repo <repo> --out <tutorial dir> --info <info.json>
                          [--outline outline.yaml] [--plain-outline plain-outline.yaml]
                          [--evidence evidence.yaml] [--site-profile site-profile.yaml]
                          [--styles-dir <_work dir>]

The --info file is JSON written by the orchestrator:

  {
    "project_name": "mypkg", "mode": "standalone", "format": "website",
    "language": "English", "theme": null, "extensions": ["code-window"],
    "repo_url": "https://github.com/me/mypkg", "docs": null, "section": null,
    "audiences": [{"slug": "beginner", "preset": "beginner", "folder": ".", "kind": "chapters"}],
    "chapters": [{"id": "A1", "name": "Router", "filename": "01_router.qmd",
                  "files": ["src/router.py"], "tests": ["tests/test_router.py"]}],
    "pages":    [{"audience": "stakeholder-public", "id": "what-it-does",
                  "filename": "what-it-does.qmd", "evidence": ["src/router.py:10-40"]}],
    "source_base_url": "https://github.com/me/mypkg/blob/<sha>/",   (or "none")
    "args": {"max_abstractions": 8, "critique": "on"}
  }

The analysis that does not depend on the audience's voice is copied next to the record,
so a later run (an update, or a new audience) need not redo it: _outline.yaml,
_evidence.yaml, _plain-outline.yaml and _site-profile.yaml (each only if its source
file was given), plus _styles/. Schema 2 added source_base_url and the extra copies;
readers must accept schema 1 records, which have neither.

  extend Change the audiences of an existing tutorial (used by add-audience) without
         rebuilding the record: existing chapters keep their recorded hashes.

    write_record.py extend --repo <repo> --tutorial <dir> --audiences <audiences.json>
                           [--pages <new-pages.json>] [--chapter-tests <tests.json>]
                           [--format website] [--source-base-url <url|none>]
                           [--outline f] [--plain-outline f] [--evidence f] [--site-profile f]
                           [--styles-dir <dir>] [--remove-style NAME]... [--rename-style OLD=NEW]...
                           [--note TEXT]

    --audiences is the COMPLETE new list (JSON, the same shape as in the info file).
    Pages of audiences no longer listed are dropped; --pages holds only the NEW pages
    (info-file shape), which replace any page with the same audience and id.
    --chapter-tests maps a chapter id to test paths, hashed and stored on that chapter.
    The change is appended to a "history" list in the record.

Files starting with "_" are ignored by Quarto, so the record never renders.
Hashes are git blob hashes of the *working tree* content, so they are identical
to `git hash-object` and need no git repository to compute.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

RECORD_NAME = "_generation.json"
OUTLINE_COPY = "_outline.yaml"
PLAIN_OUTLINE_COPY = "_plain-outline.yaml"
EVIDENCE_COPY = "_evidence.yaml"
SITE_PROFILE_COPY = "_site-profile.yaml"
SCHEMA = 2
LOCATION_SUFFIX = re.compile(r":\d+(?:-\d+)?$")


def run_git(repo: Path, *args: str) -> str | None:
    try:
        out = subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True, text=True, timeout=30, check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None
    # Porcelain status lines start with a space, so only trim trailing whitespace.
    return out.stdout.rstrip() if args and args[0] == "status" else out.stdout.strip()


def blob_hash(path: Path) -> str | None:
    """Git blob hash of a file's current content, or None if it is missing."""
    try:
        data = path.read_bytes()
    except OSError:
        return None
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def https_url(repo_url: str | None) -> str | None:
    """Normalise a git remote to an https URL without .git, or None."""
    if not repo_url or repo_url == "none":
        return None
    url = repo_url.strip()
    m = re.match(r"^git@([^:]+):(.+)$", url)
    if m:
        url = f"https://{m.group(1)}/{m.group(2)}"
    url = re.sub(r"^ssh://git@", "https://", url)
    url = re.sub(r"\.git$", "", url).rstrip("/")
    return url if url.startswith("https://") or url.startswith("http://") else None


def commit_url(repo_url: str | None, sha: str | None) -> str | None:
    base = https_url(repo_url)
    if not base or not sha:
        return None
    if re.match(r"https?://(www\.)?(github\.com|gitlab\.com)/", base):
        return f"{base}/commit/{sha}"
    return None


def source_info(repo: Path, repo_url: str | None) -> dict:
    sha = run_git(repo, "rev-parse", "HEAD")
    if repo_url is None:
        repo_url = run_git(repo, "remote", "get-url", "origin")
    status = run_git(repo, "status", "--porcelain") if sha else None
    dirty_files = [ln[3:] for ln in status.splitlines() if len(ln) > 3] if status else []
    return {
        "repo_url": https_url(repo_url) or repo_url,
        "commit": sha,
        "short": sha[:7] if sha else None,
        "branch": run_git(repo, "rev-parse", "--abbrev-ref", "HEAD") if sha else None,
        "commit_date": run_git(repo, "log", "-1", "--format=%cI") if sha else None,
        "dirty": bool(dirty_files),
        "dirty_files": dirty_files[:20],
        "commit_url": commit_url(repo_url, sha),
    }


def plugin_version() -> str | None:
    manifest = Path(__file__).resolve().parents[3] / ".claude-plugin" / "plugin.json"
    try:
        return json.loads(manifest.read_text(encoding="utf-8")).get("version")
    except (OSError, ValueError):
        return None


def hash_paths(repo: Path, paths: list[str]) -> list[dict]:
    result = []
    for raw in paths:
        rel = LOCATION_SUFFIX.sub("", str(raw).strip()).replace("\\", "/")
        if not rel:
            continue
        result.append({"path": rel, "blob": blob_hash(repo / rel)})
    return result


def build_pages(repo: Path, pages_info: list[dict]) -> list[dict]:
    pages = []
    for pg in pages_info:
        evidence = list(pg.get("evidence", []))
        if pg.get("id") == "briefing" and not evidence:
            # The briefing summarises the audience's other pages, so it depends on all their sources.
            for other in pages_info:
                if other.get("audience") == pg.get("audience") and other is not pg:
                    evidence.extend(other.get("evidence", []))
        pages.append({
            "audience": pg.get("audience"),
            "id": pg.get("id"),
            "filename": pg.get("filename"),
            "files": hash_paths(repo, list(dict.fromkeys(evidence))),
        })
    return pages


def cmd_info(args: argparse.Namespace) -> int:
    info = source_info(Path(args.repo), args.repo_url)
    info["date"] = dt.date.today().isoformat()
    print(json.dumps(info, indent=2))
    return 0


ANALYSIS_COPIES = (
    ("outline", OUTLINE_COPY),
    ("plain_outline", PLAIN_OUTLINE_COPY),
    ("evidence", EVIDENCE_COPY),
    ("site_profile", SITE_PROFILE_COPY),
)


def cmd_extend(args: argparse.Namespace) -> int:
    repo, tut = Path(args.repo), Path(args.tutorial)
    try:
        record = json.loads((tut / RECORD_NAME).read_text(encoding="utf-8"))
        audiences = json.loads(Path(args.audiences).read_text(encoding="utf-8"))
        new_pages = json.loads(Path(args.pages).read_text(encoding="utf-8")) if args.pages else []
        chapter_tests = json.loads(Path(args.chapter_tests).read_text(encoding="utf-8")) if args.chapter_tests else {}
    except (OSError, ValueError) as exc:
        print(f"error: cannot read input: {exc}", file=sys.stderr)
        return 2
    slugs = [a.get("slug") for a in audiences]
    if len(set(slugs)) != len(slugs) or not all(slugs):
        print("error: audience slugs must be present and unique", file=sys.stderr)
        return 2

    for ch in record.get("chapters", []):
        if ch.get("id") in chapter_tests:
            ch["tests"] = hash_paths(repo, chapter_tests[ch["id"]])
    fresh = build_pages(repo, new_pages)
    replaced = {(p["audience"], p["id"]) for p in fresh}
    kept = [p for p in record.get("pages", [])
            if p.get("audience") in slugs and (p.get("audience"), p.get("id")) not in replaced]
    record["pages"] = kept + fresh
    record["audiences"] = audiences
    if args.format:
        record["format"] = args.format
    if args.source_base_url and not record.get("source_base_url"):
        record["source_base_url"] = args.source_base_url
    record["schema"] = SCHEMA
    record.setdefault("source_base_url", None)
    record.setdefault("history", []).append({
        "at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "plugin": plugin_version(),
        "action": "audiences changed",
        "audiences": slugs,
        "note": args.note,
    })

    for attr, name in ANALYSIS_COPIES:
        src = getattr(args, attr)
        if src and Path(src).is_file() and Path(src).resolve() != (tut / name).resolve():
            shutil.copyfile(src, tut / name)
    styles = tut / "_styles"
    for old in args.rename_style or []:
        a, _, b = old.partition("=")
        if (styles / a).is_file() and b:
            (styles / a).replace(styles / b)
    for name in args.remove_style or []:
        (styles / name).unlink(missing_ok=True)
    if args.styles_dir and Path(args.styles_dir).is_dir():
        styles.mkdir(exist_ok=True)
        for f in Path(args.styles_dir).glob("style*.md"):
            shutil.copyfile(f, styles / f.name)

    (tut / RECORD_NAME).write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(f"updated {tut / RECORD_NAME}: audiences {', '.join(slugs)}; "
          f"{len(record['chapters'])} chapters, {len(record['pages'])} pages")
    return 0


def cmd_write(args: argparse.Namespace) -> int:
    repo, out = Path(args.repo), Path(args.out)
    try:
        info = json.loads(Path(args.info).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"error: cannot read --info: {exc}", file=sys.stderr)
        return 2
    out.mkdir(parents=True, exist_ok=True)

    chapters = []
    for ch in info.get("chapters", []):
        chapters.append({
            "id": ch.get("id"),
            "name": ch.get("name"),
            "filename": ch.get("filename"),
            "files": hash_paths(repo, ch.get("files", [])),
            "tests": hash_paths(repo, ch.get("tests", [])),
        })
    pages = build_pages(repo, info.get("pages", []))

    record = {
        "schema": SCHEMA,
        "plugin": {"name": "codebase-tutorial", "version": plugin_version()},
        "generated_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": source_info(repo, info.get("repo_url")),
        "project_name": info.get("project_name"),
        "mode": info.get("mode", "standalone"),
        "docs": info.get("docs"),
        "section": info.get("section"),
        "format": info.get("format"),
        "language": info.get("language"),
        "theme": info.get("theme"),
        "extensions": info.get("extensions", []),
        "source_base_url": info.get("source_base_url"),
        "audiences": info.get("audiences", []),
        "args": info.get("args", {}),
        "chapters": chapters,
        "pages": pages,
    }

    # A rewrite (an update refreshing the record) must not lose the log of audience changes.
    try:
        previous = json.loads((out / RECORD_NAME).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        previous = {}
    if previous.get("history"):
        record["history"] = previous["history"]

    # Copy the analysis files next to the record: _work/ is deleted at the end of a run,
    # and later runs need what the tutorial was built from. The update step needs the
    # abstractions and relationships, and the evidence it can refresh incrementally. A new
    # audience needs all of it, so that no analysis has to be repeated.
    for src, name in (
        (args.outline, OUTLINE_COPY),
        (args.plain_outline, PLAIN_OUTLINE_COPY),
        (args.evidence, EVIDENCE_COPY),
        (args.site_profile, SITE_PROFILE_COPY),
    ):
        if src and Path(src).is_file():
            # Skip a copy onto itself (an update may pass the stored file back in).
            if Path(src).resolve() != (out / name).resolve():
                shutil.copyfile(src, out / name)

    # Keep the resolved style blocks too, so an update writes in exactly the same voice
    # (this matters most for free-text audiences, whose block was written ad hoc).
    if args.styles_dir and Path(args.styles_dir).is_dir():
        dest = out / "_styles"
        dest.mkdir(exist_ok=True)
        for f in Path(args.styles_dir).glob("style*.md"):
            shutil.copyfile(f, dest / f.name)

    (out / RECORD_NAME).write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")

    missing = [f["path"] for c in chapters for f in c["files"] if f["blob"] is None]
    n_files = len({f["path"] for c in chapters for f in c["files"]})
    print(f"wrote {out / RECORD_NAME}: {len(chapters)} chapters, {len(pages)} pages, "
          f"{n_files} source files hashed, commit {record['source']['short'] or 'unknown'}"
          f"{' (+uncommitted changes)' if record['source']['dirty'] else ''}")
    if missing:
        print(f"warning: {len(missing)} listed source file(s) not found: " + ", ".join(sorted(set(missing))[:10]))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_info = sub.add_parser("info", help="print commit info as JSON")
    p_info.add_argument("--repo", required=True)
    p_info.add_argument("--repo-url")
    p_info.set_defaults(func=cmd_info)

    p_write = sub.add_parser("write", help="write _generation.json")
    p_write.add_argument("--repo", required=True)
    p_write.add_argument("--out", required=True, help="tutorial output folder")
    p_write.add_argument("--info", required=True, help="JSON file from the orchestrator")
    p_write.add_argument("--outline")
    p_write.add_argument("--plain-outline")
    p_write.add_argument("--evidence", help="evidence.yaml to keep (advanced or stakeholder audiences)")
    p_write.add_argument("--site-profile", help="site-profile.yaml to keep (integration mode)")
    p_write.add_argument("--styles-dir", help="folder holding style.md / style-<slug>.md (usually _work)")
    p_write.set_defaults(func=cmd_write)

    p_ext = sub.add_parser("extend", help="change the audiences of an existing record")
    p_ext.add_argument("--repo", required=True)
    p_ext.add_argument("--tutorial", required=True, help="tutorial folder containing _generation.json")
    p_ext.add_argument("--audiences", required=True, help="JSON file: the complete new audiences list")
    p_ext.add_argument("--pages", help="JSON file: the new stakeholder pages (info-file shape)")
    p_ext.add_argument("--chapter-tests", help="JSON file: {chapter id: [test paths]}")
    p_ext.add_argument("--format", choices=("book", "website"))
    p_ext.add_argument("--source-base-url")
    p_ext.add_argument("--outline")
    p_ext.add_argument("--plain-outline")
    p_ext.add_argument("--evidence")
    p_ext.add_argument("--site-profile")
    p_ext.add_argument("--styles-dir")
    p_ext.add_argument("--remove-style", action="append", help="file name in _styles/ to delete (repeatable)")
    p_ext.add_argument("--rename-style", action="append", help="OLD=NEW file names in _styles/ (repeatable)")
    p_ext.add_argument("--note")
    p_ext.set_defaults(func=cmd_extend)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
