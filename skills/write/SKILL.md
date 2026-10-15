---
name: write
description: Generate a multi-chapter tutorial for a codebase as a renderable Quarto book or website, or add one to an existing Quarto/quartodoc documentation site (linking to its API reference). Identifies the core abstractions, maps how they relate, orders them pedagogically, writes one chapter per abstraction in parallel via subagents, then critiques, reviews and renders. Use when asked to document, explain, or write a tutorial/onboarding guide for a repository.
argument-hint: "[target] [docs=<existing quarto folder>] [section=tutorial] [format=book|website] [audience=beginner|intermediate|<free text>|<list,of,audiences>] [theme=1980s] [language=English] [output=<dir>] [max_abstractions=10] [include=<globs>] [exclude=<globs>] [critique=on|off] [keep_work]"
---

# Codebase Tutorial (orchestrator)

You are the orchestrator. You do not write chapters yourself: you prepare inputs, delegate to subagents, validate their outputs, and assemble the Quarto project.

Pipeline: **fetch → analyse (tutorial-analyst) → validate outline → write chapters in parallel (tutorial-chapter-writer × N) → assemble index + _quarto.yml → critique in parallel (clarity, code-fidelity, accuracy) → apply fixes, review & render (tutorial-reviewer)**.

There are two modes:
- **standalone** (default): the tutorial is its own Quarto project in `<output>/`.
- **integration** (`docs=<folder>`): the tutorial is added to an existing Quarto or quartodoc site at `<docs>/<section>/`. A `tutorial-site-surveyor` step runs first, and every stage builds around what the site already contains. In integration mode, read `references/site-integration.md` before step 2; it overrides this file where they differ.

Either mode can also be **multi-audience** (`audience` lists more than one audience): one version of the tutorial per audience from a shared outline, each in its own subfolder, with a reading-level switcher on every page. If more than one audience is listed, read `references/multi-audience.md` before step 2. It overrides this file, and `site-integration.md`, where they differ.

**Subagent names**: this skill ships in the `codebase-tutorial` plugin, so its agents are scoped as `codebase-tutorial:<name>`. For example, `tutorial-analyst` below means subagent type `codebase-tutorial:tutorial-analyst`. Use the scoped name. Only if no scoped agent is available (a manual, non-plugin install) fall back to the bare name. If neither exists, stop and tell the user that the plugin's agents aren't installed.

Reference files and scripts live in the `references/` and `scripts/` folders next to this SKILL.md (in a plugin install: `${CLAUDE_PLUGIN_ROOT}/skills/write/`). Resolve them to **absolute paths** before passing them to subagents (subagents do not know where this skill lives):

- `references/outline-schema.md`: the outline contract between analyst and writers
- `references/chapter-guide.md`: how to write a chapter
- `references/style-presets.md`: audience presets and theme overlays
- `references/quarto-conventions.md`: rules that keep `.qmd` files valid (including how snippets are marked verbatim or illustrative)
- `references/critique-format.md`: findings format shared by the critics and the reviewer
- `references/site-integration.md`: integration mode, covering the site profile schema, navigation wiring, API links, and verification
- `references/multi-audience.md`: several audiences, covering layout, per-audience fan-out, navigation, the landing page and the switcher
- `scripts/add_audience_switcher.py`: inserts or refreshes the reading-level switcher on every page of a multi-audience tutorial
- `scripts/check_snippets.py`: mechanical check that verbatim snippets match the repo (standard library only; run with `python` or `python3`)
- `scripts/check_links.py`: mechanical check of relative links, anchors, `@`-link mistakes, and quartodoc interlinks against `objects.json`

## 1. Parse arguments

Parse `$ARGUMENTS` as an optional positional `target` followed by `key=value` pairs. Defaults:

| Arg | Default | Notes |
|---|---|---|
| `target` | `.` | Local path or GitHub URL |
| `docs` | none | Existing Quarto project folder (containing `_quarto.yml`), relative to the target. Switches on integration mode |
| `section` | `tutorial` | Integration mode only: subfolder of `docs` to create the tutorial in |
| `format` | `book` | `book` or `website`. In integration mode it is forced to the site's project type |
| `audience` | `beginner` | `beginner`, `intermediate`, or free text describing the reader. A comma-separated list (free-text entries in quotes) means multi-audience; see `multi-audience.md` |
| `theme` | none | Optional overlay, e.g. `1980s` |
| `language` | `English` | Language of all generated prose |
| `output` | `output/<project_name>` | Relative to the current working directory |
| `max_abstractions` | `10` | Upper bound; aim for 5–max |
| `include` / `exclude` | sensible defaults | Comma-separated globs. Default exclude: tests, docs, build/dist, vendored deps, `.venv`, `node_modules`, lockfiles, binary/media files |
| `critique` | `on` | `off` skips the three critics (the reviewer still runs the snippet checker) |
| `keep_work` | off | Keep `<output>/_work/` (outline, critiques) for debugging |

If anything essential is ambiguous (e.g. the target does not exist), ask the user before proceeding. Otherwise use defaults and state them in one line.

**Preflight**: check the tools before starting, all in one Bash call: `python --version` (or `python3 --version`), `git --version`, `quarto --version`.
- **No Python 3.9+**: stop. The checking scripts need it.
- **No git**: stop if the target is a URL. Otherwise continue without source permalinks.
- **No Quarto**: warn that the output won't be rendered or validated, and continue.

Use whichever Python command worked (`python` or `python3`) in every script command you give to subagents.

**Auto-detection**: if `docs` was not given but the target contains a Quarto project (`_quarto.yml` at the root or in `docs/`, `site/` or `documentation/`), especially one with a `quartodoc:` key, ask the user once whether to add the tutorial to that site (integration mode) or build a standalone project.

**Paths in integration mode**: `<output>` means `<target>/<docs>/<section>`, and the work dir is `<output>/_work/`. Quarto ignores paths starting with `_`, so this is safe. The `output` argument is ignored.

## 2. Fetch

- **Local path**: use it in place. Do not copy it.
- **URL**: `git clone --depth 1 <url> <output>/_work/repo` and use that as the target.
- **project_name**: last URL segment without `.git`, or the basename of the absolute local path.
- **repo_url** (for the sidebar link): the URL argument, or `git -C <target> remote get-url origin` converted to `https://` form. If there is none, use "none".
- **source_base_url** (for per-snippet line links): if `repo_url` is on GitHub or GitLab **and** `git -C <target> branch -r --contains HEAD` shows the commit is pushed, use `<repo_url>/blob/<full HEAD sha>/`, a permalink so line numbers stay correct. If the working tree has uncommitted changes to the source files, or the conditions aren't met, use "none".

Create `<output>/` and `<output>/_work/`. (Quarto ignores paths starting with `_`, so `_work/` will not be rendered.)

## 2b. Survey the existing site (integration mode only)

Spawn one `tutorial-site-surveyor` with: the target, `docs`, `section`, the absolute path to `site-integration.md`, and the output path `<output>/_work/site-profile.yaml`.

Then read the profile:
- **Stop and ask the user** if the section folder already exists and isn't empty, or if `_quarto.yml` couldn't be parsed.
- Set `format` to the profile's `project_type`, and tell the user if that overrides their `format=` argument.
- If quartodoc is present but `link_style` is `none`, warn the user that API links will be plain text. Then continue.

## 3. Resolve the style block

Read `style-presets.md`. Build one **style block**: the chosen audience preset (or, for free-text audiences, a custom block written in the same shape as the `beginner` preset and adapted to the described reader), followed by the theme overlay if one was given. Keep the numeric limits (`max_code_block_lines`, `max_diagram_participants`) explicit; the reviewer needs them.

Save it to `<output>/_work/style.md`. In multi-audience mode, build one block per audience and save each to `<output>/_work/style-<slug>.md`.

## 4. Analyse → outline

Spawn **one** `tutorial-analyst` subagent. Brief it with:

- absolute target path, include/exclude globs, `project_name`
- `max_abstractions`, `language`, `format`
- absolute path to `outline-schema.md`
- the output path: `<output>/_work/outline.yaml`
- a one-line summary of the audience (so it pitches descriptions appropriately)
- integration mode: the absolute paths to `site-profile.yaml` and `site-integration.md`

## 5. Validate the outline

Read `outline.yaml` and check every rule below. If you can, a quick `python -c` with `yaml.safe_load` is the most reliable way. Otherwise check by reading.

1. It parses as YAML and has `project_name`, `summary`, `abstractions`, `relationships`, `chapter_order`.
2. There are between 5 and `max_abstractions` abstractions (fewer is acceptable only for tiny repos). Ids are unique.
3. Every abstraction has non-empty `name`, `description`, `files`, and every path in `files` exists under the target.
4. Every relationship's `from`/`to` is a valid abstraction id and `label` is a short string. **Every abstraction id appears in at least one relationship.**
5. `chapter_order` is a permutation of all abstraction ids: no duplicates, none missing.
6. Each `filename` is `NN_<safe_name>.qmd`, where `NN` is the 1-based zero-padded position and `safe_name` is the abstraction name with every non-alphanumeric character replaced by `_`, lowercased. Fix filenames yourself if only this rule is broken.
7. Every `builds_on` id refers to a chapter *earlier* in the order.
8. Each `xref` is `sec-` + `safe_name` with `_` replaced by `-`, and all are unique. Fix these yourself if wrong.
9. Integration mode: every `related_pages` path appears in the profile's `existing_pages`, and every `api_refs` name appears in `quartodoc.objects`. Drop any that don't, and note it.

On failure (other than trivially fixable filenames), resume or re-spawn the analyst **once** with the specific list of errors. If it still fails, fix what you can yourself and tell the user what you changed.

## 6. Write chapters (parallel)

Spawn **one `tutorial-chapter-writer` per chapter, all in a single message**, so they run concurrently. Each brief contains:

- the chapter's number, its outline entry (abstraction name, description, files, key_symbols, introduces, builds_on)
- the **full chapter list** (number, name, filename, xref, one_line_summary, introduces) so it can cross-reference other chapters correctly
- previous and next chapter (name + filename + xref), or "none"
- `project_name`, `language`, `format`, `source_base_url`
- absolute target path (to read source files)
- absolute output path: `<output>/<filename>`
- absolute paths to `chapter-guide.md`, `quarto-conventions.md`, and `<output>/_work/style.md`
- the absolute path to `check_snippets.py`, plus the exact self-check command: `python <script> --repo <target> --out <output> --file <filename>`
- integration mode: the absolute paths to `site-profile.yaml` and `site-integration.md`, and the chapter's `related_pages` and `api_refs`

Tell each writer to write only its own file, to self-check its snippets before returning, and to return a 2–3 line summary.

After they finish, confirm that every expected `.qmd` file exists. Re-spawn any writer whose file is missing.

## 7. Assemble the Quarto project

### `index.qmd`

Follow the index rules in `quarto-conventions.md` for the chosen `format`. Content:

1. The `summary` from the outline.
2. `**Source repository:** <url or local path>`
3. A relationship diagram in a ```` ```{mermaid} ```` cell:
   - first line `flowchart TD`
   - one node per abstraction: `A<i>["<name with double quotes removed>"]`, where `i` is the abstraction's position in the `abstractions` list
   - one edge per relationship: `A<from> -- "<label>" --> A<to>`, with the label's double quotes and newlines removed and the label truncated to 30 characters (27 + `...`) if longer
4. `## Chapters`, then a numbered list `N. [<name>](<filename>)` in chapter order, each followed by ` — <one_line_summary>`.
5. A closing line pointing to the [Glossary](glossary.qmd).

Give the relationship diagram `%%| label: fig-overview` and `%%| fig-cap:` lines (see `quarto-conventions.md`, Part 2 §3).

### `glossary.qmd`

Collect every term in every chapter's `introduces`. For each, read the chapter that introduces it and write a definition of 1–2 sentences that agrees with that chapter, in the target language, ending with a reference to the home chapter (`@sec-<xref>` in a book, a `[Name](<filename>)` link in a website). Lay it out as a Markdown definition list, sorted alphabetically, with the title rule from `quarto-conventions.md`. If there are more than about 40 terms, you may spawn one general-purpose subagent to draft it from the chapters and the outline.

### `_quarto.yml`

Use the attribution line `Generated by [AI Codebase Knowledge Builder](https://github.com/The-Pocket/PocketFlow-Tutorial-Codebase-Knowledge)`.

**book**:
```yaml
project:
  type: book
book:
  title: "Tutorial: <project_name>"
  chapters:
    - index.qmd
    - 01_<...>.qmd
    # ... every chapter, in order
  appendices:
    - glossary.qmd
  sidebar:
    tools:                     # omit this block if repo_url is "none"
      - icon: git              # use "github" / "gitlab" when the host matches
        href: <repo_url>
        text: Source code
  page-footer:
    center: "Generated by [AI Codebase Knowledge Builder](https://github.com/The-Pocket/PocketFlow-Tutorial-Codebase-Knowledge)"
lang: <BCP-47 code for language, e.g. en, fr, zh>
format:
  html:
    theme: cosmo
    toc: true
    code-copy: true
    code-annotations: hover
```

**website**:
```yaml
project:
  type: website
website:
  title: "Tutorial: <project_name>"
  sidebar:
    style: docked
    contents:
      - index.qmd
      - 01_<...>.qmd
      # ... every chapter, in order
      - glossary.qmd
    tools:                     # omit if repo_url is "none"
      - icon: git
        href: <repo_url>
        text: Source code
  page-navigation: true
  page-footer:
    center: "Generated by [AI Codebase Knowledge Builder](https://github.com/The-Pocket/PocketFlow-Tutorial-Codebase-Knowledge)"
lang: <code>
format:
  html:
    theme: cosmo
    toc: true
    code-copy: true
    code-annotations: hover
```

Quote the title if `project_name` contains YAML-sensitive characters.

### Integration mode differences

- Write `index.qmd` and `glossary.qmd` inside `<output>/`, as above. Also add a `## Further reading` list to `index.qmd`, linking the most relevant `existing_pages` and (if quartodoc is present) the reference index.
- **Do not create a `_quarto.yml`.** Instead:
  1. Back up `<docs>/_quarto.yml` to `<output>/_work/_quarto.yml.orig`. If it isn't tracked in git, also keep a copy at `<docs>/_quarto.yml.pre-tutorial.bak`.
  2. Apply the profile's `insertion_plan` with the Edit tool, filling in the chapter list (`<section>/index.qmd`, every chapter in order, `<section>/glossary.qmd`). This must be an additive text insertion only (see `site-integration.md`).
  3. Check that the edited file still parses as YAML, and that comparing it with the backup shows only added lines. If either check fails, restore the backup and stop. Tell the user the exact snippet to add by hand.
- Leave out `page-footer`, `theme`, `lang` and source-code `tools`, because the site's own settings apply. Put the attribution as a single line at the end of `index.qmd` instead.

## 8. Critique (parallel, read-only)

Skip this step if `critique=off`. In multi-audience mode, run this step once per audience, over that audience's folder and with that audience's style block, writing to `_work/critique/<slug>/`. Batch those calls as `multi-audience.md` describes. Create `<output>/_work/critique/`, then spawn **all three critics in a single message**. Each one only writes its own findings file and never edits the tutorial, so they can safely run concurrently.

| Subagent | Findings file | Brief also includes |
|---|---|---|
| `tutorial-critic-clarity` | `_work/critique/clarity.yaml` | output dir, `outline.yaml`, `style.md`. **Not** the repo path: it reads only what a newcomer would see |
| `tutorial-critic-code` | `_work/critique/code.yaml` | target repo, output dir, `check_snippets.py`, `quarto-conventions.md` |
| `tutorial-critic-accuracy` | `_work/critique/accuracy.yaml` | target repo, output dir, `outline.yaml` |

Give every critic the absolute paths to `critique-format.md` and to its findings file. In integration mode, also give the clarity and accuracy critics `site-profile.yaml`. The clarity critic may read the existing site pages (a real reader sees them), but still not the source code. When all three return, check that each findings file exists and parses. Re-spawn any critic whose file is missing.

## 9. Apply fixes, review & render

In multi-audience mode:
- spawn one reviewer **per audience**, in parallel, each over its own folder
- add `render: skip` and the path to `multi-audience.md` to each brief
- render once yourself afterwards, as `multi-audience.md` describes

Otherwise, spawn **one `tutorial-reviewer`** with: the absolute output dir and target repo; `format`; `language`; `source_base_url`; the absolute paths to `outline.yaml`, `style.md`, `quarto-conventions.md`, `chapter-guide.md`, `critique-format.md`, `check_snippets.py` and `check_links.py`; and the three findings files (or "none" if critique was off). In integration mode, also give it `site-profile.yaml`, `site-integration.md` and the docs folder (`--project` for the link checker). It applies the findings, runs its own checks, re-runs both checkers until they pass, and attempts `quarto render` (in integration mode, of the section folder only).

If the reviewer reports unresolved **must-fix** findings, resume it once with that list. Anything still open after that goes in your final report to the user. Do not loop further.

## 10. Finish

- Delete `<output>/_work/` unless `keep_work` was set. (If the target was cloned there, the clone goes too.)
- Report to the user: the output path; the chapter list; the critics' verdicts (per-chapter clarity scores, verbatim/illustrative snippet counts, false claims found); what the reviewer fixed or declined; any unresolved must-fix findings; whether `quarto render` succeeded or was skipped; and the next step: `quarto preview <output>`.
- Integration mode: delete only `<output>/_work/`, keeping `<docs>/_quarto.yml.pre-tutorial.bak` if one was made. Also report:
  - the `_quarto.yml` diff
  - how many API links were made, and their style
  - which existing pages are linked
  - whether `quartodoc build` ran
  - the next step: `quarto preview <docs>` (or `quartodoc build` then `quarto preview <docs>` if the reference wasn't built)
