#!/usr/bin/env python3
"""Insert a reading-level switcher at the top of every page of a multi-audience tutorial.

Layout expected under --root (one folder per audience, same filenames in each):

  <root>/beginner/index.qmd, 01_x.qmd, ..., glossary.qmd
  <root>/intermediate/index.qmd, 01_x.qmd, ..., glossary.qmd

Each page gets a row of buttons, one per audience, linking to the same page in the
other audience's folder (or that audience's index.qmd if the page doesn't exist there).
The current audience's button is highlighted. Re-running replaces the existing switcher.

Placement: directly after the YAML front matter and, if present, after a first-line
"# Title {#sec-...}" heading (book-style chapter title), so the title stays first.

Usage:
  python add_audience_switcher.py --root <dir> --audiences "beginner=Beginner,intermediate=Intermediate"
                                  [--label "Reading level"]

Audience order sets button order. Standard library only. Exit code 1 on missing folders.
"""
import argparse
import re
import sys
from pathlib import Path

START = "<!-- audience-switcher:start -->"
END = "<!-- audience-switcher:end -->"
BLOCK_RE = re.compile(re.escape(START) + r".*?" + re.escape(END) + r"\n*", re.S)


def build_block(page, current, audiences, root, label):
    buttons = []
    for slug, name in audiences:
        target_dir = root / slug
        target = page if (target_dir / page).exists() else "index.qmd"
        href = target if slug == current else f"../{slug}/{target}"
        if slug == current:
            cls = '.btn .btn-sm .btn-primary .active aria-current="page"'
        else:
            cls = ".btn .btn-sm .btn-outline-primary"
        buttons.append(f"[{name}]({href}){{{cls}}}")
    return (f"{START}\n::: {{.audience-switcher .mb-4}}\n"
            f"[{label}:]{{.text-muted .small}} " + " ".join(buttons) + f"\n:::\n{END}\n\n")


def insert(text, block):
    text = BLOCK_RE.sub("", text)
    lines = text.splitlines(keepends=True)
    i = 0
    if lines and lines[0].strip() == "---":
        for j in range(1, len(lines)):
            if lines[j].strip() in ("---", "..."):
                i = j + 1
                break
    while i < len(lines) and not lines[i].strip():
        i += 1
    if i < len(lines) and re.match(r"^# \S", lines[i]):
        i += 1
    head = "".join(lines[:i])
    rest = "".join(lines[i:]).lstrip("\n")
    sep = "\n" if head and not head.endswith("\n\n") else ""
    return head + sep + block + rest


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", required=True, help="folder containing one subfolder per audience")
    ap.add_argument("--audiences", required=True, help='ordered "slug=Label" pairs, comma-separated')
    ap.add_argument("--label", default="Reading level", help="text before the buttons (translate if needed)")
    args = ap.parse_args()

    root = Path(args.root)
    audiences = []
    for pair in args.audiences.split(","):
        slug, _, name = pair.partition("=")
        audiences.append((slug.strip(), (name or slug).strip()))
    missing = [s for s, _ in audiences if not (root / s).is_dir()]
    if missing:
        print(f"missing audience folders: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)

    count = 0
    for slug, _ in audiences:
        for qmd in sorted((root / slug).glob("*.qmd")):
            text = qmd.read_text(encoding="utf-8")
            qmd.write_text(insert(text, build_block(qmd.name, slug, audiences, root, args.label)), encoding="utf-8")
            count += 1
    print(f"switcher added to {count} pages across {len(audiences)} audiences")


if __name__ == "__main__":
    main()
