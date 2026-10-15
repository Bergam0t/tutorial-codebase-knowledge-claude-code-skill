#!/usr/bin/env python3
"""Check links in generated .qmd files without rendering.

Checks every Markdown link [text](target) outside code blocks:

  relative paths    target file must exist (relative to the linking file);
                    a #anchor on a .qmd target must exist as {#anchor} in that file
  #anchor only      must exist as {#anchor} in some .qmd under --project
                    (books resolve #sec-... anchors across chapters)
  [](`pkg.obj`)     quartodoc interlinks: the object (optionally ~-prefixed) must be in
                    the inventory (objects.json). Unresolved interlinks render silently
                    as plain code, so this is the only way to catch them.
  ](@sec-...)       always fails: renders as a broken link (use #sec-... instead)

External links (http, https, mailto) are not fetched.

Usage:
  python check_links.py --out <tutorial dir> [--project <quarto project root>]
                        [--inventory <objects.json>] [--json report.json]

--project defaults to --out. --inventory defaults to <project>/objects.json if it exists.
Exit code 0 if there are no failures, 1 otherwise. Standard library only.
"""
import argparse
import json
import re
import sys
from pathlib import Path

FENCE = re.compile(r"^[ \t]*(`{3,}|~{3,})")
LINK = re.compile(r"(!?)\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
INTERLINK = re.compile(r"^`(~?)([A-Za-z_][\w.]*)`$")
ANCHOR_DEF = re.compile(r"\{\s*#([A-Za-z][\w:.-]*)")  # quartodoc writes "{ #pkg.Obj }"
INLINE_CODE = re.compile(r"(?<!\()`[^`\n]*`(?!\))")


def prose_lines(text):
    """Yield (line_number, line) for lines outside fenced code blocks."""
    fence = None
    for n, line in enumerate(text.splitlines(), 1):
        m = FENCE.match(line)
        if fence:
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence) and not line.strip()[len(m.group(1)):].strip():
                fence = None
            continue
        if m:
            fence = m.group(1)
            continue
        yield n, line


def anchors_in(path, cache):
    if path not in cache:
        try:
            cache[path] = set(ANCHOR_DEF.findall(path.read_text(encoding="utf-8", errors="replace")))
        except OSError:
            cache[path] = set()
    return cache[path]


def load_inventory(path):
    if not path or not Path(path).is_file():
        return None
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return {item["name"] for item in data.get("items", [])}


def check_file(qmd, project, inventory, cache, all_anchors):
    results = []
    text = qmd.read_text(encoding="utf-8", errors="replace")
    for n, line in prose_lines(text):
        for m in LINK.finditer(INLINE_CODE.sub("", line) if "](`" not in line else line):
            target = m.group(3)
            rec = {"file": str(qmd.relative_to(project)) if qmd.is_relative_to(project) else qmd.name,
                   "line": n, "target": target}
            if re.match(r"^(https?:|mailto:)", target):
                continue
            if target.startswith("@"):
                rec.update(status="fail", detail="[text](@ref) renders as a broken link; use [text](#ref)")
            elif INTERLINK.match(target):
                name = INTERLINK.match(target).group(2)
                if inventory is None:
                    rec.update(status="warn", detail="interlink, but no objects.json inventory to verify against")
                elif name in inventory:
                    rec.update(status="ok", detail="interlink resolves")
                else:
                    near = sorted(i for i in inventory if i.endswith("." + name.split(".")[-1]))[:3]
                    rec.update(status="fail", detail="interlink target not in inventory (renders as plain code)"
                               + (f"; did you mean {', '.join(near)}?" if near else ""))
            elif target.startswith("#"):
                anchor = target[1:]
                if anchor in anchors_in(qmd, cache) or anchor in all_anchors:
                    rec.update(status="ok", detail="anchor found")
                else:
                    rec.update(status="fail", detail=f"anchor {{#{anchor}}} not defined in any .qmd")
            else:
                path_part, _, anchor = target.partition("#")
                dest = (qmd.parent / path_part).resolve()
                if not dest.exists():
                    hint = " (is the quartodoc reference built?)" if "reference" in path_part else ""
                    rec.update(status="fail", detail=f"file not found: {path_part}{hint}")
                elif anchor and dest.suffix == ".qmd" and anchor not in anchors_in(dest, cache):
                    rec.update(status="warn", detail=f"file exists but {{#{anchor}}} not found in it")
                else:
                    rec.update(status="ok", detail="ok")
            results.append(rec)
    return results


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True, help="directory containing the generated .qmd files")
    ap.add_argument("--project", help="Quarto project root (default: --out)")
    ap.add_argument("--inventory", help="quartodoc objects.json (default: <project>/objects.json)")
    ap.add_argument("--json", help="also write the full report to this JSON file")
    args = ap.parse_args()

    out = Path(args.out).resolve()
    project = Path(args.project).resolve() if args.project else out
    inv_path = args.inventory or (project / "objects.json")
    inventory = load_inventory(inv_path)

    cache = {}
    all_anchors = set()
    for q in project.rglob("*.qmd"):
        if not any(part.startswith(("_", ".")) for part in q.relative_to(project).parts[:-1]):
            all_anchors |= anchors_in(q, cache)

    results = []
    for qmd in sorted(out.glob("*.qmd")):
        results.extend(check_file(qmd, project, inventory, cache, all_anchors))

    counts = {s: sum(r["status"] == s for r in results) for s in ("ok", "warn", "fail")}
    for r in results:
        if r["status"] != "ok":
            print(f"[{r['status'].upper()}] {r['file']}:{r['line']} -> {r['target']}  {r['detail']}")
    inv_note = f"inventory: {len(inventory)} objects" if inventory is not None else "inventory: none"
    print(f"\n{len(results)} links checked: {counts['ok']} ok, {counts['warn']} warn, {counts['fail']} fail ({inv_note})")
    if args.json:
        Path(args.json).write_text(json.dumps(results, indent=2), encoding="utf-8")
    sys.exit(1 if counts["fail"] else 0)


if __name__ == "__main__":
    main()
