---
name: write
description: Generate a multi-chapter tutorial for a codebase as a renderable Quarto book or website, or add one to an existing Quarto/quartodoc documentation site (linking to its API reference). Identifies the core abstractions, maps how they relate, orders them pedagogically, writes one chapter per abstraction in parallel via subagents, then critiques, reviews and renders. Use when asked to document, explain, or write a tutorial/onboarding guide for a repository.
argument-hint: "[target] [docs=<existing quarto folder>] [section=tutorial] [format=book|website] [audience=beginner|intermediate|<free text>|<list,of,audiences>] [theme=1980s] [language=English] [output=<dir>] [max_abstractions=10] [include=<globs>] [exclude=<globs>] [critique=on|off] [extensions=none|<list>|+add,-remove] [learning=on|off] [briefing=none|pdf|docx|pdf,docx] [config=<path>|none] [keep_work]"
---

# Codebase Tutorial (orchestrator)

You are the orchestrator. You do not write chapters yourself: you prepare inputs, delegate to subagents, validate their outputs, and assemble the Quarto project.

Pipeline: **fetch → analyse (tutorial-analyst) → validate outline → write chapters in parallel (tutorial-chapter-writer × N) → assemble index + _quarto.yml → critique in parallel (clarity, code-fidelity, accuracy) → apply fixes, review & render (tutorial-reviewer)**.

There are two modes:
- **standalone** (default): the tutorial is its own Quarto project in `<output>/`.
- **integration** (`docs=<folder>`): the tutorial is added to an existing Quarto or quartodoc site at `<docs>/<section>/`. A `tutorial-site-surveyor` step runs first, and every stage builds around what the site already contains. In integration mode, read `references/site-integration.md` before step 2; it overrides this file where they differ.

Either mode can also be **multi-audience** (`audience` lists more than one audience): one version of the tutorial per audience from a shared outline, each in its own subfolder, with a reading-level switcher on every page. If more than one audience is listed, read `references/multi-audience.md` before step 2. It overrides this file, and `site-integration.md`, where they differ.

**Stakeholder (no-code) audiences** (`stakeholder-*`) don't get one chapter per abstraction. They get their own question-led page sets, planned by `tutorial-plain-planner` (step 5c) and written by `tutorial-plain-writer` (step 6). If any audience is a stakeholder preset, read `references/stakeholder.md` before step 2. It overrides this file for those audiences: their pages, checks and critics.

**Subagent names**: this skill ships in the `codebase-tutorial` plugin, so its agents are scoped as `codebase-tutorial:<name>`. For example, `tutorial-analyst` below means subagent type `codebase-tutorial:tutorial-analyst`. Use the scoped name. Only if no scoped agent is available (a manual, non-plugin install) fall back to the bare name. If neither exists, stop and tell the user that the plugin's agents aren't installed.

Reference files and scripts live in the `references/` and `scripts/` folders next to this SKILL.md (in a plugin install: `${CLAUDE_PLUGIN_ROOT}/skills/write/`). Resolve them to **absolute paths** before passing them to subagents (subagents do not know where this skill lives):

- `references/outline-schema.md`: the outline contract between analyst and writers
- `references/chapter-guide.md`: how to write a chapter
- `references/style-presets.md`: audience presets and theme overlays
- `references/quarto-conventions.md`: rules that keep `.qmd` files valid (including how snippets are marked verbatim or illustrative)
- `references/critique-format.md`: findings format shared by the critics and the reviewer
- `references/site-integration.md`: integration mode, covering the site profile schema, navigation wiring, API links, and verification
- `references/evidence.md`: the `evidence.yaml` schema and citing rules for advanced audiences, plus the "known issues" callouts
- `references/multi-audience.md`: several audiences, covering layout, per-audience fan-out, navigation, the landing page and the switcher
- `references/stakeholder.md`: no-code stakeholder audiences, covering the zero-code rules, the page menu, the page plan for each preset, the `plain-outline.yaml` schema, and the checks
- `references/extensions.md`: the vetted Quarto extensions (pinned sources, filter order, exact usage notes), how to install them, and how to handle unvetted ones
- `references/learning.md`: opt-in learning aids (self-tests, exercises, reading paths, first-contribution list)
- `references/config.md`: the optional `.codebase-tutorial.yml` project config, and the `_generation.json` record and "generated from" footer line
- `scripts/write_record.py`: prints commit info, writes `_generation.json` (plugin version, commit, resolved options, per-chapter source hashes), and (`extend`, for `/codebase-tutorial:add-audience`) changes an existing record's audiences
- `scripts/relayout.py`: moves a flat tutorial into an audience subfolder and re-bases its relative links (used by `/codebase-tutorial:add-audience`)
- `scripts/check_drift.py`, `scripts/check_tutorial.py`: used by `/codebase-tutorial:update` and CI to find stale chapters and run every mechanical check
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
| `audience` | `beginner` | `beginner`, `intermediate`, `advanced-contributor`, `advanced-architect`, `advanced-user`, `stakeholder-decision-maker`, `stakeholder-domain-expert`, `stakeholder-product-owner`, `stakeholder-public`, or free text describing the reader. A comma-separated list (free-text entries in quotes) means multi-audience; see `multi-audience.md` |
| `theme` | none | Optional overlay, e.g. `1980s` |
| `language` | `English` | Language of all generated prose |
| `output` | `output/<project_name>` | Relative to the current working directory |
| `max_abstractions` | `10` | Upper bound; aim for 5–max |
| `include` / `exclude` | sensible defaults | Comma-separated globs. Default exclude: tests, docs, build/dist, vendored deps, `.venv`, `node_modules`, lockfiles, binary/media files |
| `critique` | `on` | `off` skips the three critics (the reviewer still runs the snippet checker) |
| `extensions` | defaults (`code-window`, `code-line-style`) | Quarto extensions to install and use. `none`, an explicit list, `+name`/`-name` to change the defaults, or `owner/repo[@tag]` for unvetted ones. See `extensions.md` |
| `learning` | `off` | `on` adds a self-test or exercise to every chapter, reading paths to each overview, and (for `advanced-contributor`) a first-contribution list. See `learning.md` |
| `briefing` | `none` | `pdf`, `docx` or `pdf,docx`: stakeholder audiences also get a short print-ready briefing document. Ignored (with a note) when no audience is a stakeholder preset. See the briefing section of `stakeholder.md` |
| `config` | `<target>/.codebase-tutorial.yml` | Path to a project config file, or `none` to ignore it. See `config.md` |
| `keep_work` | off | Keep `<output>/_work/` (outline, critiques) for debugging |

**Project config**: unless `config=none`, look for `.codebase-tutorial.yml` in the target (or at the `config=` path). If it exists, read `references/config.md` and apply it: command-line values win over the file, and the file wins over the defaults above. The file can also supply two free-text keys, `focus` (for the analyst) and `notes` (house terminology, added to every style block). For a cloned URL target, show the user what you intend to apply and ask first.

If anything essential is ambiguous (e.g. the target does not exist), ask the user before proceeding. Otherwise use defaults and state the resolved options in one line, saying which came from the config file.

**Preflight**: check the tools before starting, all in one Bash call: `python --version` (or `python3 --version`), `git --version`, `quarto --version`.
- **No Python 3.9+**: stop. The checking scripts need it.
- **No git**: stop if the target is a URL. Otherwise continue without source permalinks.
- **No Quarto**: warn that the output won't be rendered or validated, and continue.
- **Any advanced or stakeholder audience**: also run `gh --version` and `gh auth status`. If either fails, tell the user that GitHub issues and PRs won't be checked, and that the advanced pages will say so. Then continue.

Use whichever Python command worked (`python` or `python3`) in every script command you give to subagents.

**Auto-detection**: if `docs` was not given but the target contains a Quarto project (`_quarto.yml` at the root or in `docs/`, `site/` or `documentation/`), especially one with a `quartodoc:` key, ask the user once whether to add the tutorial to that site (integration mode) or build a standalone project.

**Paths in integration mode**: `<output>` means `<target>/<docs>/<section>`, and the work dir is `<output>/_work/`. Quarto ignores paths starting with `_`, so this is safe. The `output` argument is ignored.

## 2. Fetch

- **Local path**: use it in place. Do not copy it.
- **URL**: `git clone --depth 1 <url> <output>/_work/repo` and use that as the target. If any audience is advanced or stakeholder, use `git clone --filter=blob:none <url> <output>/_work/repo` instead. That keeps the full commit history, which the evidence step needs, while fetching file contents lazily.
- **project_name**: last URL segment without `.git`, or the basename of the absolute local path.
- **repo_url** (for the sidebar link): the URL argument, or `git -C <target> remote get-url origin` converted to `https://` form. If there is none, use "none".
- **source_base_url** (for per-snippet line links): if `repo_url` is on GitHub or GitLab **and** `git -C <target> branch -r --contains HEAD` shows the commit is pushed, use `<repo_url>/blob/<full HEAD sha>/`, a permalink so line numbers stay correct. If the working tree has uncommitted changes to the source files, or the conditions aren't met, use "none".

Create `<output>/` and `<output>/_work/`. (Quarto ignores paths starting with `_`, so `_work/` will not be rendered.)

**Commit info**: run `python <scripts>/write_record.py info --repo <target> --repo-url <repo_url>` and keep the result (`short`, `commit_url`, `dirty`, `date`). Step 7 uses it for the "generated from" footer line, and step 7 records it in `_generation.json`. If the target is not a git repository the script returns nulls; the footer then shows only the date.

## 2b. Survey the existing site (integration mode only)

Spawn one `tutorial-site-surveyor` with: the target, `docs`, `section`, the absolute path to `site-integration.md`, and the output path `<output>/_work/site-profile.yaml`.

Then read the profile:
- **Stop and ask the user** if the section folder already exists and isn't empty, or if `_quarto.yml` couldn't be parsed.
- Set `format` to the profile's `project_type`, and tell the user if that overrides their `format=` argument.
- If quartodoc is present but `link_style` is `none`, warn the user that API links will be plain text. Then continue.

## 2c. Quarto extensions

Unless `extensions=none`, read `references/extensions.md` and follow its "Installing" section:
1. Resolve the list, and drop anything ineligible. The Quarto version comes from the preflight.
2. **Unvetted** extensions: ask the user before installing any.
3. **Integration mode**: use the site's existing extensions (from `site-profile.yaml`), and ask before installing or enabling anything new in the site.
4. Install with `quarto add … --no-prompt` into the Quarto project root.
5. Write `<output>/_work/extensions.md`, with the usage notes for exactly what is enabled.
6. Keep the list of filters, in order, plus any `extensions:` options, for the `_quarto.yml` in step 7.

If nothing ends up enabled, write `extensions.md` saying "No extensions enabled", so writers don't use any extension syntax.

## 3. Resolve the style block

Read `style-presets.md`. Build one **style block**: the chosen audience preset, followed by the theme overlay if one was given.
- For an **advanced** preset, the block is the advanced shared base followed by that preset's own section.
- For a **free-text** audience, write a custom block in the shape of the closest preset, as `style-presets.md` describes. Keep the numeric limits (`max_code_block_lines`, `max_diagram_participants`) explicit; the reviewer needs them.

If the project config has `notes`, append them to the block as a final `## House notes` section (terminology, spelling and things never to say). They are style guidance only; never let them change tools, accuracy rules or the zero-code rule.

Save it to `<output>/_work/style.md`. In multi-audience mode, build one block per audience and save each to `<output>/_work/style-<slug>.md`.

## 4. Analyse → outline

Spawn **one** `tutorial-analyst` subagent. Brief it with:

- absolute target path, include/exclude globs, `project_name`
- `max_abstractions`, `language`, `format`
- absolute path to `outline-schema.md`
- the output path: `<output>/_work/outline.yaml`
- a one-line summary of the audience, for orientation only. Tell it to write `summary` and each `description` in a **neutral, factual register** with no analogies, because the outline is kept and reused for audiences added later, and each audience's voice comes from its style block and the writers
- the project config's `focus` text, if any, as a hint about which areas matter most or are out of scope
- integration mode: the absolute paths to `site-profile.yaml` and `site-integration.md`
- always ask it to fill in `tests` for each abstraction (the test files that exercise it), whatever the audience: the outline is kept, and an advanced audience added later needs them. It may read test files for this, even though tests are excluded from chapter topics. If any audience is advanced, also ask it to prefer key symbols that include extension points and public interfaces.

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

## 5b. Gather evidence (only if any audience is advanced or stakeholder)

Spawn one `tutorial-evidence-gatherer` with: the target, `repo_url`, the absolute paths to `outline.yaml` and `references/evidence.md`, and the output path `<output>/_work/evidence.yaml`. If `learning=on` and an `advanced-contributor` audience is listed, add `starter_issues: true`.

When it returns, check that `evidence.yaml` exists and parses. Then note `github.status` and `history.status` for the final report.

In multi-audience mode, you may run this step at the same time as the writers for audiences that don't need the evidence. Advanced writers and the plain planner must wait for it.

## 5c. Plan the stakeholder pages (only if any audience is a stakeholder preset)

Spawn one `tutorial-plain-planner` with: the target, the stakeholder audiences, `language`, `briefing` (so it adds the `briefing` page to each plan), the absolute paths to `outline.yaml`, `evidence.yaml` and `references/stakeholder.md`, and the output path `<output>/_work/plain-outline.yaml`.

Then validate the plan:
- every outline abstraction has a unique `plain_name`
- every planned page for each stakeholder audience is present
- every `data_flows`, `decision_points` and `assumptions` item has an `evidence` location, or says "not determined from the code"

On failure, resume the planner once with the errors.

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
- advanced audiences: the absolute paths to `evidence.yaml` and `references/evidence.md`, and the chapter's `tests`
- `learning: on` (with the absolute path to `learning.md`) when `learning=on`. Writers then add the prescribed section. Not for stakeholder pages.
- the absolute path to `<output>/_work/extensions.md`. Writers use only the extensions listed there. If `include-code-files` is enabled, tell them to use `include=` (with paths relative to their own chapter file) for every verbatim excerpt.

Tell each writer to write only its own file, to self-check its snippets before returning, and to return a 2–3 line summary.

**Stakeholder audiences** use `tutorial-plain-writer` instead, one per page in that audience's plan (`plain-outline.yaml` → `pages`), except `glossary`, which you write in step 7. Each brief contains:
- the preset, the page id, filename and `focus`, and the audience's full page list
- `format`, `language`, and the output path `<output>[/<slug>]/<page file>`
- the absolute paths to: the style block, `references/stakeholder.md`, `quarto-conventions.md`, `_work/extensions.md`, `plain-outline.yaml`, `evidence.yaml`, and the target repo
- the no-code self-check command: `python <check_snippets.py> --repo <target> --out <folder> --file <page> --no-code`

The `overview` page (`index.qmd`) is written by a plain writer too, not by you as for technical audiences. It includes the known-issues note from `evidence.md`, worded plainly.

**Briefing** (`briefing` set): the `briefing` page is written in a **second wave**, after every other page of that audience exists, because it summarises them. Spawn one `tutorial-plain-writer` per stakeholder audience with the page id `briefing`, the paths of that audience's finished pages, the requested formats, the generation date, and `format` of the project. Follow "The briefing" in `stakeholder.md`.

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
6. Advanced audiences only: the "Known issues" callout from `evidence.md`, placed directly after the summary. There are two versions: one for when GitHub was checked, and one for when it couldn't be (which tells readers to check the tracker themselves).

**Learning** (`learning=on`, chapter-based audiences): add `## Reading paths` after the chapter list, and for `advanced-contributor` `## Your first contribution`, as `learning.md` describes. Build the paths from the outline's `chapter_order` and `builds_on`, and the issues from `evidence.yaml` → `starter_issues`.

Give the relationship diagram `%%| label: fig-overview` and `%%| fig-cap:` lines (see `quarto-conventions.md`, Part 2 §3).

### `glossary.qmd`

Collect every term in every chapter's `introduces`. For each, read the chapter that introduces it and write a definition of 1–2 sentences that agrees with that chapter, in the target language, ending with a reference to the home chapter (`@sec-<xref>` in a book, a `[Name](<filename>)` link in a website). Lay it out as a Markdown definition list, sorted alphabetically, with the title rule from `quarto-conventions.md`. If there are more than about 40 terms, you may spawn one general-purpose subagent to draft it from the chapters and the outline.

### Stakeholder audiences

- `index.qmd` is written by a plain writer (step 6). Don't write it yourself.
- `glossary.qmd` comes from `plain-outline.yaml` → `glossary`, as a definition list sorted alphabetically. Each entry is the plain term, its plain definition, and, if present, one sentence: "Developers call this *<technical name>*." This is the **only** place technical names appear. No code formatting, and no file paths (drop the path from `technical_name`).
- **Navigation**: the `chapters` (book) or `sidebar.contents` (website) list follows the audience's page plan, in order, with `glossary.qmd` last. In a book, the glossary is a normal chapter for this audience, not an appendix.

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
    left: "<generated-from line, see config.md>"
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
    left: "<generated-from line, see config.md>"
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

**Briefing in a book** (`briefing` set, standalone mode): render the briefing explicitly **before** the project render, add `resources: [briefing.pdf, briefing.docx]` (only the requested ones) under `project:` in `_quarto.yml`, and add the download line to the audience's `index.qmd`, as `stakeholder.md` describes. In a website nothing extra is needed: the page's own front matter makes Quarto produce and link the formats.

**Extensions** (from step 2c), in either format, added to `_quarto.yml`:
```yaml
filters:                       # in the order given by extensions.md; omit if empty
  - include-code-files
  - code-line-style
  - code-window
extensions:                    # only options for enabled extensions
  code-window:
    style: macos
  highlight-text:
    styles:
      key-term:
        bg-colour: "#fff3bf"
```
If `lightbox` was requested, add `lightbox: auto` under `format: html`.

### Generation record and "generated from" line

1. **Footer**: build the `left:` footer text from the commit info of step 2, as `config.md` describes (translated, with the short sha linked to `commit_url`, and "(plus uncommitted changes)" if `dirty`). In integration mode, add it to the attribution paragraph in `index.qmd` instead.
2. **Record**: write `<output>/_work/record-info.json` (shape in the `write_record.py` docstring) from what you know: the resolved options, the audiences with their slugs, folders and kinds, the chapters with the `files` and `tests` from `outline.yaml`, and, for stakeholder audiences, the `pages` with their evidence locations from `plain-outline.yaml`. Include `source_base_url` (from step 2, "none" if there isn't one), and `learning` and `briefing` in `args`, so an update repeats them. Then run
   ```
   python <scripts>/write_record.py write --repo <target> --out <output> --info <output>/_work/record-info.json --outline <output>/_work/outline.yaml [--plain-outline <output>/_work/plain-outline.yaml] [--evidence <output>/_work/evidence.yaml] [--site-profile <output>/_work/site-profile.yaml] --styles-dir <output>/_work
   ```
   Pass `--evidence` if step 5b ran and `--site-profile` in integration mode. The record, the analysis copies (`_outline.yaml`, `_evidence.yaml`, `_plain-outline.yaml`, `_site-profile.yaml`) and the style blocks (`_styles/`) live in `<output>/` and survive the `_work/` cleanup, so a later update or new audience can reuse them. Tell the user about the warning if any listed source file was missing.

If the critics or reviewer later change which source files a chapter cites, re-run the `write` command at the end of step 9 so the record matches the final pages.

### Integration mode differences

- Write `index.qmd` and `glossary.qmd` inside `<output>/`, as above. Also add a `## Further reading` list to `index.qmd`, linking the most relevant `existing_pages` and (if quartodoc is present) the reference index.
- **Do not create a `_quarto.yml`.** Instead:
  1. Back up `<docs>/_quarto.yml` to `<output>/_work/_quarto.yml.orig`. If it isn't tracked in git, also keep a copy at `<docs>/_quarto.yml.pre-tutorial.bak`.
  2. Apply the profile's `insertion_plan` with the Edit tool, filling in the chapter list (`<section>/index.qmd`, every chapter in order, `<section>/glossary.qmd`). This must be an additive text insertion only (see `site-integration.md`).
  3. Check that the edited file still parses as YAML, and that comparing it with the backup shows only added lines. If either check fails, restore the backup and stop. Tell the user the exact snippet to add by hand.
- Leave out `page-footer`, `theme`, `lang` and source-code `tools`, because the site's own settings apply. Put the attribution as a single line at the end of `index.qmd` instead.

## 8. Critique (parallel, read-only)

For **stakeholder audiences**, run only the clarity and accuracy critics, plus the no-code check (`check_snippets.py --no-code --out <folder>`), whose output goes into the clarity critic's brief. Give both critics `references/stakeholder.md` and `plain-outline.yaml`, and give the accuracy critic `evidence.yaml` and the target repo too. Skip the code critic, because there's no code to check.

Skip this step if `critique=off`. In multi-audience mode, run this step once per audience, over that audience's folder and with that audience's style block, writing to `_work/critique/<slug>/`. Batch those calls as `multi-audience.md` describes. Create `<output>/_work/critique/`, then spawn **all three critics in a single message**. Each one only writes its own findings file and never edits the tutorial, so they can safely run concurrently.

| Subagent | Findings file | Brief also includes |
|---|---|---|
| `tutorial-critic-clarity` | `_work/critique/clarity.yaml` | output dir, `outline.yaml`, `style.md`. **Not** the repo path: it reads only what a newcomer would see |
| `tutorial-critic-code` | `_work/critique/code.yaml` | target repo, output dir, `check_snippets.py`, `quarto-conventions.md` |
| `tutorial-critic-accuracy` | `_work/critique/accuracy.yaml` | target repo, output dir, `outline.yaml` |

For advanced audiences:
- also give the accuracy critic `evidence.yaml`, so it can check that every cited commit, doc, issue and marker exists and says what the chapter claims
- tell the code critic that the style is **verbatim-first**

Give every critic the absolute paths to `critique-format.md`, to `<output>/_work/extensions.md`, and to its findings file. In integration mode, also give the clarity and accuracy critics `site-profile.yaml`. The clarity critic may read the existing site pages (a real reader sees them), but still not the source code. When all three return, check that each findings file exists and parses. Re-spawn any critic whose file is missing.

## 9. Apply fixes, review & render

In multi-audience mode:
- spawn one reviewer **per audience**, in parallel, each over its own folder
- add `render: skip` and the path to `multi-audience.md` to each brief
- render once yourself afterwards, as `multi-audience.md` describes

Otherwise, spawn **one `tutorial-reviewer`** with: the absolute output dir and target repo; `format`; `language`; `source_base_url`; the absolute paths to `outline.yaml`, `style.md`, `quarto-conventions.md`, `chapter-guide.md`, `critique-format.md`, `check_snippets.py` and `check_links.py`; `<output>/_work/extensions.md`; and the three findings files (or "none" if critique was off). In integration mode, also give it `site-profile.yaml`, `site-integration.md` and the docs folder (`--project` for the link checker). It applies the findings, runs its own checks, re-runs both checkers until they pass, and attempts `quarto render` (in integration mode, of the section folder only).

For a **stakeholder audience**, also give the reviewer `references/stakeholder.md` and `plain-outline.yaml`, and say `mode: stakeholder`. It then runs `check_snippets.py --no-code` instead of the normal snippet check.

If the reviewer reports unresolved **must-fix** findings, resume it once with that list. Anything still open after that goes in your final report to the user. Do not loop further.

## 10. Finish

- Delete `<output>/_work/` unless `keep_work` was set. (If the target was cloned there, the clone goes too.)
- Report to the user: the output path; the chapter list; the critics' verdicts (per-chapter clarity scores, verbatim/illustrative snippet counts, false claims found); what the reviewer fixed or declined; any unresolved must-fix findings; whether `quarto render` succeeded or was skipped; and the next step: `quarto preview <output>`.
- Also report the extensions installed (source and version), and those skipped (with the reason). If `include-code-files` was used, also say:
  - included snippets are hash-stamped
  - the tutorial must stay inside the repo for its includes to resolve
  - running `python check_snippets.py --repo . --out <tutorial dir>` in CI catches source changes that would leave the prose describing the wrong lines
- **Config**: if the target had no `.codebase-tutorial.yml`, print the resolved options as a ready-to-paste config (see `config.md`), and say the user can save it to make future runs reproducible. Don't write it into the repo yourself.
- If a briefing was produced, list the files (`briefing.pdf`, `briefing.docx`) and where they are. If their render failed, give the command to run.
- Mention that `<output>/_generation.json` records the commit, so the tutorial can be checked for staleness later: `/codebase-tutorial:update` refreshes just the chapters whose source changed, `/codebase-tutorial:add-audience` adds another voice or reading level later without repeating the analysis, and `scripts/check_tutorial.py` runs the no-AI checks in CI.
- Integration mode: delete only `<output>/_work/`, keeping `<docs>/_quarto.yml.pre-tutorial.bak` if one was made. Also report:
  - the `_quarto.yml` diff
  - how many API links were made, and their style
  - which existing pages are linked
  - whether `quartodoc build` ran
  - the next step: `quarto preview <docs>` (or `quartodoc build` then `quarto preview <docs>` if the reference wasn't built)
