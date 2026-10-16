#!/usr/bin/env python3
"""Move a flat (single-audience) tutorial into one audience subfolder, keeping its links valid.

Used by /codebase-tutorial:add-audience when a tutorial that was generated with one
audience (pages directly in the tutorial folder) gains a second audience, which needs
the multi-audience layout (one subfolder per audience).

  relayout.py --tutorial <dir> --slug <slug> [--alias] [--dry-run] [--json <file>]

What it does:
  1. Moves every top-level file and folder of <dir> into <dir>/<slug>/, except names
     starting with "_" or "." (the record, _outline.yaml, _styles/, _extensions/, _work/,
     _quarto.yml, ...), which stay where they are.
  2. Rewrites relative references inside the moved .qmd pages, because every page is now
     one folder deeper. A reference that pointed OUTSIDE the tutorial folder (an existing
     docs page, the quartodoc reference, an included source file) gets a "../" prefix.
     A reference to another moved page is left alone (they all moved together).
     Covered: Markdown links and images, reference-style link definitions,
     include="..." attributes on code fences, {{< include ... >}} shortcodes, and
     href=/src= attributes. Fenced code bodies and inline code are never touched.
  3. With --alias, adds `aliases: ["../<name>.html"]` to each moved page's front matter,
     so Quarto writes a redirect from the page's old URL to its new one (links from
     other pages and from outside the site keep working).

It does not write the landing page, the navigation or the switcher; the orchestrator
does. Pages without YAML front matter (book-format chapters) are not supported: the
script stops before changing anything.

Standard library only. Exit code: 0 = ok, 1 = refused (nothing changed), 2 = bad usage.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path

SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
INLINE_CODE = re.compile(r"(`+)(?:(?!\1).)+?\1")
FENCE = re.compile(r"^\s*(`{3,}|~{3,})")
MD_LINK = re.compile(r"(\]\(\s*<?)([^)\s>]+)(>?)")
REF_DEF = re.compile(r"^(\s{0,3}\[[^\]]+\]:\s*<?)(\S+?)(>?)(\s|$)")
INCLUDE_ATTR = re.compile(r'(\binclude\s*=\s*")([^"]*)(")')
SHORTCODE = re.compile(r"(\{\{<\s*include\s+)([^\s>]+)")
HTML_ATTR = re.compile(r'(\b(?:href|src)\s*=\s*")([^"]*)(")')


def needs_prefix(target: str, root: Path) -> bool:
    """True if a relative target, written in a page at <root>, points outside <root>."""
    t = target.strip()
    if not t or t[0] in "#/@{<" or SCHEME.match(t):
        return False
    path = re.split(r"[#?]", t, maxsplit=1)[0]
    if not path:
        return False
    resolved = os.path.normpath(os.path.join(str(root), path))
    inside = os.path.commonpath([str(root), resolved]) == str(root)
    return not inside


def fix_target(m: re.Match, root: Path, count: list[int]) -> str:
    groups = m.groups()
    target = groups[1]
    if needs_prefix(target, root):
        count[0] += 1
        return groups[0] + "../" + target + "".join(groups[2:])
    return m.group(0)


def rewrite_line(line: str, root: Path, count: list[int], in_fence_info: bool) -> str:
    if in_fence_info:
        return INCLUDE_ATTR.sub(lambda m: fix_target(m, root, count), line)
    m = REF_DEF.match(line)
    if m and needs_prefix(m.group(2), root):
        count[0] += 1
        return m.group(1) + "../" + m.group(2) + m.group(3) + line[m.end(3):]
    # Rewrite only outside inline code spans.
    out, last = [], 0
    for code in INLINE_CODE.finditer(line):
        out.append(rewrite_prose(line[last:code.start()], root, count))
        out.append(code.group(0))
        last = code.end()
    out.append(rewrite_prose(line[last:], root, count))
    return "".join(out)


def rewrite_prose(seg: str, root: Path, count: list[int]) -> str:
    for rx in (MD_LINK, SHORTCODE, HTML_ATTR):
        seg = rx.sub(lambda m: fix_target(m, root, count), seg)
    return seg


def split_front_matter(text: str):
    """Return (front matter lines incl. fences, body) or None if there is no front matter."""
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return None
    for j in range(1, len(lines)):
        if lines[j].strip() in ("---", "..."):
            return lines[:j + 1], "".join(lines[j + 1:])
    return None


def add_alias(front: list[str], old_name: str) -> tuple[list[str], bool]:
    if any(re.match(r"^aliases\s*:", ln) for ln in front):
        return front, False
    eol = "\r\n" if front[0].endswith("\r\n") else "\n"
    block = [f"aliases:{eol}", f'  - "../{old_name}"{eol}']
    return front[:-1] + block + front[-1:], True


def rewrite_page(text: str, root: Path, alias_name: str | None) -> tuple[str, int, bool]:
    fm = split_front_matter(text)
    count, aliased = [0], False
    front, body = (fm if fm else ([], text))
    if alias_name and front:
        front, aliased = add_alias(front, alias_name)
    out, fence = [], None
    for line in body.splitlines(keepends=True):
        m = FENCE.match(line)
        if fence is None and m:
            fence = m.group(1)[0] * 3
            out.append(rewrite_line(line, root, count, in_fence_info=True))
        elif fence is not None:
            if m and m.group(1).startswith(fence) and line.strip().strip(fence[0]) == "":
                fence = None
            out.append(line)
        else:
            out.append(rewrite_line(line, root, count, in_fence_info=False))
    # Front matter can hold links too (e.g. a `image:` path); rewrite plain values on the same terms.
    new_front = []
    for ln in front:
        if re.match(r"^\s*(image|include-before-body|include-after-body|bibliography|css)\s*:", ln):
            ln = re.sub(r"(:\s*[\"']?)([^\"'\s]+)", lambda m: fix_target(m, root, count), ln, count=1)
        new_front.append(ln)
    return "".join(new_front) + "".join(out), count[0], aliased


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tutorial", required=True, help="the flat tutorial folder")
    ap.add_argument("--slug", required=True, help="subfolder to move the pages into")
    ap.add_argument("--alias", action="store_true", help="add redirect aliases from the old page URLs")
    ap.add_argument("--dry-run", action="store_true", help="report what would change, change nothing")
    ap.add_argument("--json", help="write a manifest of the moves to this file")
    a = ap.parse_args()

    root = Path(a.tutorial).resolve()
    if not root.is_dir():
        print(f"error: {root} is not a folder", file=sys.stderr)
        return 2
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", a.slug):
        print("error: slug must be lowercase letters, digits and hyphens", file=sys.stderr)
        return 2
    dest = root / a.slug
    movers = sorted(p for p in root.iterdir() if not p.name.startswith(("_", ".")))
    if dest.exists():
        print(f"refused: {dest} already exists", file=sys.stderr)
        return 1
    if not any(p.suffix == ".qmd" for p in movers):
        print(f"refused: no .qmd pages directly in {root}; is it already multi-audience?", file=sys.stderr)
        return 1
    no_fm = [p.name for p in movers if p.suffix == ".qmd"
             and split_front_matter(p.read_text(encoding="utf-8")) is None]
    if no_fm:
        print("refused: these pages have no YAML front matter (book-format chapters?): "
              + ", ".join(no_fm) + ". Regenerate them in website form instead.", file=sys.stderr)
        return 1

    # Compute every rewrite before touching the disk.
    plan, manifest = {}, []
    for p in movers:
        entry = {"from": p.name, "to": f"{a.slug}/{p.name}", "links_rewritten": 0, "alias": False}
        if p.suffix == ".qmd":
            text = p.read_bytes().decode("utf-8")
            alias_name = (p.stem + ".html") if a.alias else None
            new, n, aliased = rewrite_page(text, root, alias_name)
            plan[p] = new
            entry.update(links_rewritten=n, alias=aliased)
        manifest.append(entry)

    for e in manifest:
        extra = f", {e['links_rewritten']} link(s) re-based" if e["links_rewritten"] else ""
        extra += ", alias added" if e["alias"] else ""
        print(f"{'would move' if a.dry_run else 'moved'} {e['from']} -> {e['to']}{extra}")
    if a.json:
        Path(a.json).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    if a.dry_run:
        return 0

    dest.mkdir()
    for p in movers:
        target = dest / p.name
        if p in plan:
            target.write_bytes(plan[p].encode("utf-8"))
            p.unlink()
        else:
            shutil.move(str(p), str(target))
    return 0


if __name__ == "__main__":
    sys.exit(main())
