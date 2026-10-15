#!/usr/bin/env python3
"""Check that code blocks in generated .qmd files faithfully reflect the source repo.

Every fenced code block (other than ```{mermaid}) must be one of:

  verbatim      ```{.python filename="src/pkg/module.py"}
                ```{.python filename="src/pkg/module.py:12-30"}
                Contiguous lines copied exactly from that repo file. The only
                tolerated differences are uniform removal of leading indentation,
                trailing whitespace, and Quarto code-annotation markers (# <1>).

  illustrative  ```{.python .illustrative filename="Simplified from src/pkg/module.py"}
                Simplified, elided, invented-example or pseudo code. Not compared
                to the source (critics review these by hand).

Anything else (plain ```python with no filename, executable ```{python} cells) fails.

Usage:
  python check_snippets.py --repo <target repo> --out <tutorial dir> [--file NAME.qmd] [--json report.json]

Exit code 0 if there are no failures, 1 otherwise. Standard library only.
"""
import argparse
import difflib
import json
import re
import sys
import textwrap
from pathlib import Path

FENCE_OPEN = re.compile(r"^[ \t]*(?P<fence>`{3,}|~{3,})\s*(?P<info>.*?)\s*$")
FILENAME_ATTR = re.compile(r'filename\s*=\s*"([^"]*)"')
LINE_RANGE = re.compile(r"^(?P<path>.+?):(?P<start>\d+)(?:-(?P<end>\d+))?$")
ANNOTATION = re.compile(r"\s*(#|//|--|;)\s*<\d+>\s*$")


def iter_blocks(text):
    """Yield (line_number_of_opening_fence, info_string, content_lines)."""
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        m = FENCE_OPEN.match(lines[i])
        if not m:
            i += 1
            continue
        fence = m.group("fence")
        close = re.compile(r"^[ \t]*" + re.escape(fence[0]) + "{" + str(len(fence)) + r",}\s*$")
        j = i + 1
        while j < len(lines) and not close.match(lines[j]):
            j += 1
        yield i + 1, m.group("info"), lines[i + 1:j]
        i = j + 1


def classify(info):
    """Return (kind, lang, filename_attr)."""
    filename = None
    fm = FILENAME_ATTR.search(info)
    if fm:
        filename = fm.group(1).strip()
    if info.startswith("{"):
        inner = info.strip("{} ")
        tokens = inner.split()
        first = tokens[0] if tokens else ""
        if first == "mermaid" or first == ".mermaid":
            return "mermaid", "mermaid", filename
        if first and not first.startswith("."):
            return "executable", first, filename
        classes = [t for t in tokens if t.startswith(".")]
        lang = classes[0][1:] if classes else ""
        if ".illustrative" in classes:
            return "illustrative", lang, filename
        return ("verbatim" if filename else "unmarked"), lang, filename
    if info == "mermaid":
        return "bare-mermaid", "mermaid", None
    return "unmarked", info, None


def normalise(lines):
    lines = [ANNOTATION.sub("", l).rstrip() for l in lines]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return textwrap.dedent("\n".join(lines)).split("\n") if lines else []


def find_exact(src, snip):
    n = len(snip)
    first = snip[0].strip()
    for s in range(len(src) - n + 1):
        if src[s].strip() == first and normalise(src[s:s + n]) == snip:
            return s + 1, s + n
    return None


def closest_diff(src, snip, max_lines=25):
    sm = difflib.SequenceMatcher(None, [l.strip() for l in src], [l.strip() for l in snip], autojunk=False)
    a, b, size = sm.find_longest_match(0, len(src), 0, len(snip))
    if size == 0:
        return None, None
    s = max(0, a - b)
    window = normalise(src[s:s + len(snip)])
    diff = list(difflib.unified_diff(window, snip, f"repo (from line {s + 1})", "snippet", lineterm="", n=1))
    return s + 1, "\n".join(diff[:max_lines])


def check_verbatim(repo, filename, snip):
    path, start, end = filename, None, None
    rm = LINE_RANGE.match(filename)
    if rm and not Path(repo, filename).exists():
        path, start = rm.group("path"), int(rm.group("start"))
        end = int(rm.group("end") or start)
    src_path = (Path(repo) / path).resolve()
    if not str(src_path).startswith(str(Path(repo).resolve())) or not src_path.is_file():
        return "fail", f"source file not found in repo: {path}", None
    src = [l.rstrip() for l in src_path.read_text(encoding="utf-8", errors="replace").splitlines()]
    if not snip:
        return "fail", "empty code block", None
    if start is not None and normalise(src[start - 1:end]) == snip:
        return "ok", f"matches {path}:{start}-{end}", None
    found = find_exact(src, snip)
    if found:
        if start is not None:
            return "warn", f"matches {path}:{found[0]}-{found[1]} but caption says {start}-{end}", None
        return "ok", f"matches {path}:{found[0]}-{found[1]}", None
    near, diff = closest_diff(src, snip)
    detail = f"not found verbatim in {path}" + (f"; closest region starts at line {near}" if near else "")
    return "fail", detail, diff


def check_file(repo, qmd):
    results = []
    text = qmd.read_text(encoding="utf-8", errors="replace")
    for line_no, info, content in iter_blocks(text):
        kind, lang, filename = classify(info)
        rec = {"file": qmd.name, "line": line_no, "kind": kind, "lang": lang, "filename": filename}
        if kind == "mermaid":
            continue
        if kind == "bare-mermaid":
            rec.update(status="fail", detail="use ```{mermaid} not ```mermaid")
        elif kind == "executable":
            rec.update(status="fail", detail=f"executable cell {{{lang}}}: use a plain .{lang} block")
        elif kind == "unmarked":
            rec.update(status="fail", detail='no filename="..." and not marked .illustrative')
        elif kind == "illustrative":
            if filename:
                rec.update(status="ok", detail="illustrative (not compared)")
            else:
                rec.update(status="warn", detail='illustrative but has no visible filename="..." caption')
        else:
            status, detail, diff = check_verbatim(repo, filename, normalise(content))
            rec.update(status=status, detail=detail)
            if diff:
                rec["diff"] = diff
        results.append(rec)
    return results


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", required=True, help="target repository root")
    ap.add_argument("--out", required=True, help="tutorial output directory containing .qmd files")
    ap.add_argument("--file", action="append", help="check only these .qmd filenames (repeatable)")
    ap.add_argument("--json", help="also write the full report to this JSON file")
    args = ap.parse_args()

    out = Path(args.out)
    files = [out / f for f in args.file] if args.file else sorted(out.glob("*.qmd"))
    results = []
    for qmd in files:
        if not qmd.is_file():
            results.append({"file": qmd.name, "line": 0, "kind": "-", "status": "fail", "detail": "file not found"})
            continue
        results.extend(check_file(args.repo, qmd))

    counts = {s: sum(r["status"] == s for r in results) for s in ("ok", "warn", "fail")}
    kinds = {k: sum(r["kind"] == k for r in results) for k in ("verbatim", "illustrative")}
    for r in results:
        if r["status"] != "ok":
            print(f"[{r['status'].upper()}] {r['file']}:{r['line']} ({r['kind']}) {r['detail']}")
            if r.get("diff"):
                print(textwrap.indent(r["diff"], "    "))
    print(f"\n{len(results)} blocks checked: {counts['ok']} ok, {counts['warn']} warn, {counts['fail']} fail "
          f"({kinds['verbatim']} verbatim, {kinds['illustrative']} illustrative)")
    if args.json:
        Path(args.json).write_text(json.dumps(results, indent=2), encoding="utf-8")
    sys.exit(1 if counts["fail"] else 0)


if __name__ == "__main__":
    main()
