#!/usr/bin/env python3
"""Run every mechanical check on a generated tutorial in one go (no AI, no network).

Meant for CI and for a quick local "is this tutorial still right?" check. It uses the
audiences and options recorded in <tutorial>/_generation.json to choose the right
checks for each folder, then runs:

  1. check_drift.py     which chapters depend on source files that have changed
  2. check_snippets.py  verbatim and included snippets still match the code
                        (--no-code for stakeholder folders)
  3. check_links.py     relative links, anchors, @-link mistakes, quartodoc interlinks

Usage:
  python check_tutorial.py --repo . --tutorial docs/tutorial [--strict]

  --strict   exit 1 when any chapter is stale. Without it, staleness is reported but
             does not fail the run (snippet and link failures always do), which suits
             pull requests where the tutorial is refreshed in a follow-up.

If $GITHUB_STEP_SUMMARY is set, a Markdown summary is appended to it.
Exit code: 0 = ok, 1 = a check failed, 2 = no usable record. Standard library only.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def run(script: str, *args: str) -> tuple[int, str]:
    r = subprocess.run([sys.executable, str(HERE / script), *args],
                       capture_output=True, text=True, check=False)
    return r.returncode, (r.stdout + r.stderr).strip()


def tail(text: str, n: int = 40) -> str:
    lines = text.splitlines()
    return "\n".join(lines[-n:]) if len(lines) > n else text


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--tutorial", required=True)
    ap.add_argument("--strict", action="store_true")
    a = ap.parse_args()

    repo, tut = Path(a.repo).resolve(), Path(a.tutorial).resolve()
    try:
        rec = json.loads((tut / "_generation.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"error: no usable _generation.json in {tut}: {exc}", file=sys.stderr)
        return 2

    sections: list[tuple[str, int, str]] = []
    failed = False

    code, out = run("check_drift.py", "--repo", str(repo), "--tutorial", str(tut),
                    "--fail-on", "stale" if a.strict else "never")
    sections.append(("Freshness (what changed since generation)", code, out))
    failed |= code != 0

    audiences = rec.get("audiences") or [{"slug": "default", "folder": ".", "kind": "chapters"}]
    for aud in audiences:
        folder = tut / (aud.get("folder") or ".")
        args = ["--repo", str(repo), "--out", str(folder)]
        if aud.get("kind") == "stakeholder":
            args.append("--no-code")
        code, out = run("check_snippets.py", *args)
        sections.append((f"Snippets: {aud.get('slug')}", code, out))
        failed |= code != 0

    project = tut
    if rec.get("mode") == "integration" and rec.get("docs"):
        candidate = repo / rec["docs"]
        if candidate.is_dir():
            project = candidate
    code, out = run("check_links.py", "--out", str(tut), "--project", str(project))
    sections.append(("Links", code, out))
    failed |= code != 0

    for title, code, out in sections:
        print(f"\n=== {title}: {'ok' if code == 0 else 'FAILED'} ===")
        print(out)

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as fh:
            fh.write("## Tutorial checks\n\n")
            for title, code, out in sections:
                fh.write(f"<details{' open' if code else ''}><summary>{'✅' if code == 0 else '❌'} {title}</summary>\n\n```\n{tail(out)}\n```\n\n</details>\n\n")

    print("\nResult:", "FAILED" if failed else "ok")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
