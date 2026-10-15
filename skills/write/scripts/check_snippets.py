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

  included      ```{.python include="../../src/pkg/module.py" start-line=12 end-line=30 filename="src/pkg/module.py:12-30"}
                (quarto-ext/include-code-files) Pulled from the file at render time, so
                exact by construction, but a wrong path renders an EMPTY block silently.
                Checked: path exists inside the repo (relative to the .qmd), range is valid,
                caption matches. With --stamp, an include-hash="..." of the included lines
                is recorded; later runs fail if those lines change (drift detection).

Anything else (plain ```python with no filename, executable ```{python} cells) fails.

Usage:
  python check_snippets.py --repo <target repo> --out <tutorial dir> [--file NAME.qmd] [--json report.json]
                           [--stamp] [--restamp]

  --stamp     add include-hash to included blocks that lack one
  --restamp   also overwrite hashes that no longer match (only after re-checking the prose)
  --no-code   stakeholder (zero-code) pages: any non-mermaid code block FAILS; inline code,
              file paths and identifier-like tokens in prose WARN (glossary.qmd is exempt
              from the prose checks, as it may name technical components once)

Exit code 0 if there are no failures, 1 otherwise. Standard library only.
"""
import argparse
import difflib
import hashlib
import json
import re
import sys
import textwrap
from pathlib import Path

FENCE_OPEN = re.compile(r"^[ \t]*(?P<fence>`{3,}|~{3,})\s*(?P<info>.*?)\s*$")
FILENAME_ATTR = re.compile(r'filename\s*=\s*"([^"]*)"')
LINE_RANGE = re.compile(r"^(?P<path>.+?):(?P<start>\d+)(?:-(?P<end>\d+))?$")
ANNOTATION = re.compile(r"\s*(#|//|--|;)\s*<\d+>\s*$")
ATTR = re.compile(r'([\w-]+)\s*=\s*(?:"([^"]*)"|([^\s"}]+))')
HASH_ATTR = re.compile(r'\s*include-hash\s*=\s*"[^"]*"')


def attrs_of(info):
    return {m.group(1): (m.group(2) if m.group(2) is not None else m.group(3)) for m in ATTR.finditer(info)}


def lines_hash(lines):
    return hashlib.sha1("\n".join(l.rstrip() for l in lines).encode("utf-8")).hexdigest()[:12]


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
        if "include" in attrs_of(inner):
            return "included", lang, filename
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


def check_included(repo, qmd, info, content, filename, stamp, restamp):
    """Return (status, detail, new_info_or_None)."""
    a = attrs_of(info)
    repo_root = Path(repo).resolve()
    src_path = (qmd.parent / a["include"]).resolve()
    if not src_path.is_relative_to(repo_root):
        return "fail", f"include path leaves the repo: {a['include']}", None
    if not src_path.is_file():
        return "fail", f"included file not found: {a['include']} (renders as an EMPTY block)", None
    src = src_path.read_text(encoding="utf-8", errors="replace").splitlines()
    try:
        start = int(a.get("start-line", 1))
        end = int(a.get("end-line", len(src)))
    except ValueError:
        return "fail", "start-line/end-line must be integers", None
    if not (1 <= start <= end <= len(src)):
        return "fail", f"line range {start}-{end} outside file (1-{len(src)})", None
    rel = src_path.relative_to(repo_root).as_posix()
    notes = []
    if any(l.strip() for l in content):
        notes.append("block body is ignored by include-code-files; leave it empty")
    if filename:
        m = LINE_RANGE.match(filename)
        cap_path, cap_range = (m.group("path"), (int(m.group("start")), int(m.group("end") or m.group("start")))) if m else (filename, None)
        if cap_path != rel:
            notes.append(f'caption path "{cap_path}" differs from included file "{rel}"')
        if cap_range and cap_range != (start, end):
            notes.append(f"caption range {cap_range[0]}-{cap_range[1]} differs from include {start}-{end}")
    else:
        notes.append(f'no filename caption; use filename="{rel}:{start}-{end}"')
    current = lines_hash(src[start - 1:end])
    recorded = a.get("include-hash")
    new_info = None
    if recorded and recorded != current:
        if restamp:
            new_info = HASH_ATTR.sub("", info).rstrip()[:-1].rstrip() + f' include-hash="{current}"}}'
            notes.append("hash updated (--restamp)")
        else:
            return "fail", (f"included lines {rel}:{start}-{end} changed since stamped "
                            f"(hash {recorded} -> {current}); re-check the prose, then --restamp"), None
    elif not recorded:
        if stamp or restamp:
            new_info = info.rstrip()[:-1].rstrip() + f' include-hash="{current}"}}'
            notes.append("hash stamped")
        else:
            notes.append("not stamped (run with --stamp to enable drift detection)")
    status = "warn" if any(not n.startswith("hash") for n in notes) else "ok"
    return status, f"included {rel}:{start}-{end}" + (f"; {'; '.join(notes)}" if notes else ""), new_info


INLINE_CODE = re.compile(r"`[^`\n]+`")
LINK_TARGET = re.compile(r"\]\([^)]*\)")
PATH_LIKE = re.compile(r"(?<![\w/])(?:[\w.-]+/)+[\w.-]+\.[A-Za-z]{1,5}\b")
IDENT_LIKE = re.compile(r"\b(?:[a-z][a-z0-9]*_[a-z0-9_]+|[A-Z][a-z0-9]+(?:[A-Z][a-z0-9]+)+|\w+\.\w+\(\))")


def check_no_code(qmd):
    """Zero-code checks for stakeholder pages."""
    results = []
    text = qmd.read_text(encoding="utf-8", errors="replace")
    for line_no, info, _ in iter_blocks(text):
        kind, lang, _f = classify(info)
        if kind != "mermaid":
            results.append({"file": qmd.name, "line": line_no, "kind": "code-in-plain", "lang": lang,
                            "status": "fail", "detail": f"code block ({kind}) not allowed on a zero-code page"})
    if qmd.name == "glossary.qmd":
        return results
    in_block, in_front, fence = False, False, None
    for n, line in enumerate(text.splitlines(), 1):
        if n == 1 and line.strip() == "---":
            in_front = True
            continue
        if in_front:
            in_front = line.strip() not in ("---", "...")
            continue
        m = FENCE_OPEN.match(line)
        if in_block:
            if m and m.group("fence")[0] == fence[0] and len(m.group("fence")) >= len(fence) and not m.group("info"):
                in_block = False
            continue
        if m:
            in_block, fence = True, m.group("fence")
            continue
        if line.lstrip().startswith("<!--"):
            continue
        prose = LINK_TARGET.sub("]()", line)
        for kind, rx, what in (("inline-code", INLINE_CODE, "inline code"),
                               ("path-like", PATH_LIKE, "file path"),
                               ("identifier-like", IDENT_LIKE, "identifier-like token")):
            for hit in rx.findall(INLINE_CODE.sub(" ", prose) if kind != "inline-code" else prose):
                results.append({"file": qmd.name, "line": n, "kind": kind, "lang": "",
                                "status": "warn", "detail": f"{what} in prose: {hit!r} (use the plain name; technical names belong in the glossary)"})
    return results


def check_file(repo, qmd, stamp=False, restamp=False):
    results = []
    text = qmd.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines(keepends=True)
    changed = False
    for line_no, info, content in iter_blocks(text):
        kind, lang, filename = classify(info)
        rec = {"file": qmd.name, "line": line_no, "kind": kind, "lang": lang, "filename": filename}
        if kind == "mermaid":
            continue
        if kind == "included":
            status, detail, new_info = check_included(repo, qmd, info, content, filename, stamp, restamp)
            rec.update(status=status, detail=detail)
            if new_info:
                old = lines[line_no - 1]
                lines[line_no - 1] = old.replace(info, new_info, 1)
                changed = True
        elif kind == "bare-mermaid":
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
    if changed:
        qmd.write_text("".join(lines), encoding="utf-8")
    return results


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", required=True, help="target repository root")
    ap.add_argument("--out", required=True, help="tutorial output directory containing .qmd files")
    ap.add_argument("--file", action="append", help="check only these .qmd filenames (repeatable)")
    ap.add_argument("--json", help="also write the full report to this JSON file")
    ap.add_argument("--stamp", action="store_true", help="add include-hash to unstamped included blocks")
    ap.add_argument("--restamp", action="store_true", help="also overwrite mismatched include-hash values")
    ap.add_argument("--no-code", action="store_true", help="zero-code checks for stakeholder pages")
    args = ap.parse_args()

    out = Path(args.out)
    files = [out / f for f in args.file] if args.file else sorted(out.glob("*.qmd"))
    results = []
    for qmd in files:
        if not qmd.is_file():
            results.append({"file": qmd.name, "line": 0, "kind": "-", "status": "fail", "detail": "file not found"})
            continue
        if args.no_code:
            results.extend(check_no_code(qmd))
        else:
            results.extend(check_file(args.repo, qmd, args.stamp, args.restamp))

    counts = {s: sum(r["status"] == s for r in results) for s in ("ok", "warn", "fail")}
    kinds = {k: sum(r["kind"] == k for r in results) for k in ("verbatim", "illustrative", "included")}
    for r in results:
        if r["status"] != "ok":
            print(f"[{r['status'].upper()}] {r['file']}:{r['line']} ({r['kind']}) {r['detail']}")
            if r.get("diff"):
                print(textwrap.indent(r["diff"], "    "))
    print(f"\n{len(results)} blocks checked: {counts['ok']} ok, {counts['warn']} warn, {counts['fail']} fail "
          f"({kinds['verbatim']} verbatim, {kinds['included']} included, {kinds['illustrative']} illustrative)")
    if args.json:
        Path(args.json).write_text(json.dumps(results, indent=2), encoding="utf-8")
    sys.exit(1 if counts["fail"] else 0)


if __name__ == "__main__":
    main()
