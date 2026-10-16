---
name: add-audience
description: Add another audience (a different voice or reader level, including no-code stakeholder versions) to a tutorial that /codebase-tutorial:write already generated, reusing its stored outline, evidence and style blocks instead of analysing the code again. Works for standalone tutorials and for ones inside an existing Quarto/quartodoc site. For a single-audience tutorial it asks whether to convert to multi-audience (with a switcher) or to replace the existing voice and stay flat. Use when someone wants the same tutorial for a second reader.
argument-hint: "audience=<preset|free text|list> [target] [tutorial=<tutorial folder>] [layout=ask|convert|replace|separate] [theme=<overlay>] [critique=on|off] [dry_run] [keep_work]"
---

# Codebase Tutorial: add an audience (orchestrator)

You add one or more audiences to a tutorial that `/codebase-tutorial:write` generated earlier. The analysis is already done and stored next to the tutorial (`_outline.yaml`, `_evidence.yaml`, `_plain-outline.yaml`, `_site-profile.yaml`, `_styles/`, `_generation.json`), so you do **not** re-run the analyst, or the evidence and planning steps unless something is missing. You write only the new audience's pages, re-check only those, and update the record.

Pipeline: **locate record → check the stored analysis is current → choose the layout (ask) → prepare inputs → change the layout → write the new audience in parallel → assemble → mechanical checks → scoped critique → review & render → refresh record**.

This skill reuses the `write` skill's agents, references and scripts, which live next to this skill in `../write/` (in a plugin install: `${CLAUDE_PLUGIN_ROOT}/skills/write/`). Resolve every path to an **absolute path** before passing it to a subagent. Agent names are scoped as `codebase-tutorial:<name>` (see `write/SKILL.md`). Read `write/SKILL.md`, `write/references/multi-audience.md` and `write/references/config.md` now. Also read `write/references/site-integration.md` if the record says `mode: integration`, and `write/references/stakeholder.md` if any new audience is a `stakeholder-*` preset. Where this file says "as in write step N", follow that step of `write/SKILL.md`.

## 1. Parse arguments and preflight

| Arg | Default | Notes |
|---|---|---|
| `audience` | required | The audience(s) to add: a preset, free text describing the reader, or a comma-separated list (parsing, slugs and labels as in `multi-audience.md`) |
| `target` | `.` | The repository the tutorial describes (a local path; a cloned URL isn't supported) |
| `tutorial` | auto | The tutorial folder containing `_generation.json` |
| `layout` | `ask` | Only matters when the tutorial has a single audience: `convert` (to multi-audience), `replace` (swap the voice, stay flat), `separate` (a second, independent tutorial folder). `ask` asks you |
| `theme` | the record's | A theme applies to every audience, so it is only accepted with `layout=replace` or `separate` |
| `critique` | the record's | `on` or `off` |
| `dry_run` | off | Report the layout choices, what would change and what it would cost, then stop |
| `keep_work` | off | Keep `_work/` |

Preflight, in one Bash call: `python --version` (or `python3`), `git --version`, `quarto --version`. Python 3.9+ is required; without Quarto, say that the render will be skipped. Any advanced or stakeholder audience: also `gh --version` and `gh auth status`, and tell the user GitHub issues won't be checked if they fail.

## 2. Locate and read the record

Find the tutorial as in update step 2. If there is no `_generation.json`, or no `_outline.yaml` beside it, the tutorial predates the stored analysis (plugin < 1.5.0): tell the user and recommend a fresh `/codebase-tutorial:write` run (it keeps everything this skill needs). Stop.

From the record take `mode`, `docs`, `section`, `format`, `language`, `theme`, `extensions`, `audiences`, `args` (including `learning`, `briefing`, `notes`) and `source_base_url`. These options apply to the new audience too: **use them, not today's defaults**. `<output>` is the tutorial folder (in integration mode, `<target>/<docs>/<section>`), and the work dir is `<output>/_work/`.

Classify the layout from `audiences`:
- **flat**: one audience with `folder: "."`.
- **multi**: every audience has its own folder. This is the **add** layout; no question is needed.

Resolve the new audiences to slugs as in `multi-audience.md`. A slug already in the record means that audience exists: tell the user, suggest `/codebase-tutorial:update` to refresh it, and stop.

## 3. Check the stored analysis is current

```
python <write>/scripts/check_drift.py --repo <target> --tutorial <output> --fail-on never --json <output>/_work/drift.json
```
(Create `<output>/_work/` first.) The stored outline and the existing pages describe the code as it was. Writing a new audience from today's code beside stale pages would make the versions disagree.
- **Any chapter or page stale**: stop. Show which, and tell the user to run `/codebase-tutorial:update` first. Don't continue unless they explicitly insist.
- **Only unmapped changes** (files no chapter cites): they may be a component the tutorial doesn't cover. Mention it and continue; the new audience will match the existing chapter set.
- **Nothing changed**: continue.

## 4. Choose the layout (flat tutorials only)

What each layout does, and when it is possible:

| Layout | What happens | Possible when |
|---|---|---|
| **convert** | The existing pages move into `<old-slug>/`, the new audience goes in `<new-slug>/`, `<output>/index.qmd` becomes a landing page, every page gets the audience switcher, and navigation changes. Old chapter URLs keep working through redirects | Standalone, or integration in a **website** site. Not for an integration **book**. A standalone **book** is first rebuilt as a website, which rewrites every existing chapter in website form (one extra writer per chapter, voice kept) |
| **replace** | The new voice overwrites the existing pages. The tutorial stays flat, URLs and navigation are unchanged. The old voice is gone (it survives only in git history) | Always |
| **separate** | The new voice becomes its own tutorial in a new folder (`<output>-<slug>`, or a second section in integration mode) with its own record, and the existing one is untouched | Always. It is the way to add a voice to an integration book without replacing the first |

If `layout=ask` (the default), ask with AskUserQuestion, listing only the layouts possible here and stating the costs in the option descriptions: for convert, whether the book must be rebuilt, that page URLs gain a folder (with redirects), and, in integration mode, that the site's `_quarto.yml` navigation lines for the tutorial will change; for replace, the number of pages that will be overwritten. Recommend **convert** where it is possible. If the session can't ask the user, stop and ask them to re-run with `layout=`. Never choose `replace` for them.

**replace** with several new audiences isn't supported (the result would have more than one audience): use `convert`. Replacing one audience out of several isn't supported either.

If `dry_run`, report the chosen (or possible) layouts, the files that would move, be overwritten or created, the navigation lines that would change, and the number of agents (writers = chapters × new audiences, plus a critic trio and a reviewer per new audience, plus the book-conversion writers if any), then stop.

**Before changing anything** (convert or replace): run `git -C <target> status --porcelain -- <output>` and the same for `<docs>/_quarto.yml` or `<output>/_quarto.yml`. If the folder isn't tracked, or has uncommitted changes, copy the tutorial folder to `<output>/_backup-pre-add-audience/` (Quarto ignores `_` paths) and tell the user to delete it once they're happy. If it is tracked and clean, git is the backup.

## 5. Prepare the inputs

1. **Style blocks.** For each new audience build the block as in write step 3, with the record's `theme` and `args.notes` (as "House notes"), into `<output>/_work/style-<slug>.md` (for `replace`, `<output>/_work/style.md`). Put **only new style blocks** in `_work/`: the record copies every `style*.md` it finds there into `_styles/`.
2. **Load the stored analysis** into `_work/`: copy `_outline.yaml` to `_work/outline.yaml`, and `_evidence.yaml`, `_plain-outline.yaml` and `_site-profile.yaml` if present. These are the shared facts; don't change them.
3. **Outline readiness.**
   - If a new audience is advanced and any abstraction in the outline has no `tests` key (the outline predates 1.8), spawn `tutorial-analyst` once in **tests-only mode**: `previous_outline` = the stored outline, `tests_only: true`, the target, `outline-schema.md`, and the output `_work/outline.yaml`. It changes nothing else.
   - An outline from before 1.8 may have `description` and `summary` text written in the first audience's voice (with an analogy). Tell the new audience's writers that the outline's wording is background only and that they write in their own voice. Never edit the stored outline's text.
4. **Integration mode: refresh the site profile.** The site may have changed since the first run. Spawn `tutorial-site-surveyor` in **refresh mode**: the target, `docs`, `section`, `existing_tutorial: true`, `site-integration.md`, and the output `_work/site-profile.yaml`. Use it, not the stored copy, for `existing_pages`, `quartodoc` and `link_style`, and for the lines of `_quarto.yml` that belong to the tutorial (`navigation.tutorial_entries`). If the profile's `project_type` is `book` and the layout is `convert`, stop and offer `replace` or `separate`.
5. **Evidence**, only if a new audience is advanced or stakeholder, or `learning` is on with a new `advanced-contributor`:
   - no stored `_evidence.yaml`: run write step 5b into `_work/evidence.yaml`.
   - stored but `gathered_on` is older than 30 days: spawn `tutorial-evidence-gatherer` in update mode with `previous_evidence` = the stored file and no `changed_files`, so it refreshes the repo-wide signals and open issues cheaply.
   - `starter_issues` needed but absent: add `starter_issues: true`.
   Otherwise use the stored file as it is.
6. **Stakeholder plan**, only for new stakeholder audiences: spawn `tutorial-plain-planner` as in write step 5c. If `_plain-outline.yaml` exists, use **add-audience mode** (`previous_plain_outline` = it, `new_audiences`, `briefing` from the record's `args`), so the plain names, flows and decision rules stay identical across audiences. Otherwise run it normally. Validate as in write step 5c.
7. **Extensions.** Rebuild `_work/extensions.md` as in update step 6, from the record's list and **without reinstalling** what is already in `_extensions/`. (In integration mode, the site's own extensions.)
8. **`source_base_url`**: the record's value. If it is empty (a schema 1 record), use "none".

## 6. Change the layout

Do the part for the chosen layout. All paths are inside `<output>` unless stated.

### add (already multi-audience)

Nothing moves. The new audience gets `<new-slug>/`. Go to step 7, and in step 8 add the navigation entries for the new audience.

### convert

Let `<old>` be the existing audience's slug.

**a. Website tutorials (standalone website, or integration).** Move the pages and re-base their links:
```
python <write>/scripts/relayout.py --tutorial <output> --slug <old> --alias --json <output>/_work/relayout.json
```
Every top-level page and file not starting with `_` moves into `<old>/`. Links that pointed outside the tutorial (existing site pages, the quartodoc reference, `include=` paths) gain a `../`. Each page gets an `aliases` redirect from its old URL. Read the printed summary to the user. If the script refuses (pages without front matter), the tutorial is book-format: treat it as part b.

**b. Standalone book.** Quarto books can't hold two versions of a chapter, so the tutorial becomes a website:
1. Rewrite the existing audience in website form into `<old>/`: one `tutorial-chapter-writer` (or `tutorial-plain-writer` for stakeholder pages) per existing page, in a single message, in **format conversion** mode: `convert_format: book-to-website`, `previous_version` = the existing page, `format: website`, the stored style block `_styles/style.md` copied to `_work/style-<old>.md`, and the new output path `<old>/<filename>`. They keep voice and facts. Tell them the page is now one folder deeper, and to add `aliases: ["../<filename without .qmd>.html"]` to the front matter, so the old book URL redirects.
2. Convert `index.qmd` and `glossary.qmd` yourself into `<old>/`, changing syntax only: front matter titles instead of body H1s, no `{.unnumbered}`, `@sec-…` references to `[name](<filename>.qmd)` links, and the same kind of `aliases` entry.
3. Delete the old flat pages (everything you converted) from `<output>`.
4. In `_quarto.yml`, change `project: type: book` to `website` and rewrite the `book:` block as the `website:` block from `multi-audience.md` ("Navigation"), keeping `lang`, `format`, filters and extensions. If there was a briefing, remove the `resources:` entry and tell the user to re-render it.

Change `format` to `website` in the record (step 13).

**c. Navigation**, following "Changing an existing tutorial's navigation" in `multi-audience.md`:
- Standalone: edit `<output>/_quarto.yml` for both audiences.
- Integration: back up `<docs>/_quarto.yml` to `_work/_quarto.yml.orig` (and beside it as `_quarto.yml.pre-add-audience.bak` if it isn't tracked in git). Using the profile's `navigation.tutorial_entries`, replace **exactly those lines** with the navbar menu and per-audience sidebars. Then check that the file still parses as YAML, and diff it against the backup: every removed or added line must be a tutorial line (it mentions `<section>/`, a sidebar id `<section>`/`<section>-<slug>`, or the tutorial's menu). If either check fails, restore the backup, stop and show the user the exact lines to change by hand.

**d. The old audience's style and landing page.** The record rename (step 13) moves `_styles/style.md` to `_styles/style-<old>.md`. Write the landing page `<output>/index.qmd` as `multi-audience.md` describes, with buttons for the old audience (default, first) and the new one(s). Its `Reader` line for the old audience comes from `_styles/style.md`.

### replace

1. List the pages that will be overwritten. Ask the user to confirm (AskUserQuestion), naming the count and that the old voice is only recoverable from git or `_backup-pre-add-audience/`.
2. The page set is the outline's chapters (chapter-based) or the new audience's page plan (stakeholder). If the page *kind* changes (chapters to stakeholder or back), delete the old audience's pages first. Same-kind replacement overwrites in place.
3. If the page set changed, rewrite the navigation list for the tutorial: standalone as in write step 7 (`_quarto.yml`); integration by editing exactly the tutorial's lines in `<docs>/_quarto.yml` with the same backup, parse and diff checks as in convert part c. If the page set is the same, leave navigation alone.
4. `<new-slug>` is the flat audience (`folder: "."`); everything below writes into `<output>` itself.

### separate

The new tutorial is `<output>-<new-slug>` (integration mode: section `<section>-<new-slug>` inside `<docs>`, with its own navigation entries added exactly as in write step 7). Copy `_outline.yaml`, `_evidence.yaml`, `_plain-outline.yaml` and `_site-profile.yaml` into its `_work/`. Then follow write steps 3 and 6 to 10 for that single audience, using the stored analysis in place of steps 4 to 5c, and a fresh record from `write_record.py write` at the end (with `--outline`, `--evidence`, `--plain-outline`, `--site-profile`). Skip step 13 below.

## 7. Write the new audience

Spawn one writer per (new audience × chapter or page), all in a single message (batches of about 12 for more). Use `tutorial-chapter-writer` for chapters and `tutorial-plain-writer` for stakeholder pages (the briefing in a second wave, as in write step 6). Each brief is the write step 6 brief, with these differences:
- the new audience's style block, and the output path `<output>/<new-slug>/<filename>` (for `replace`, `<output>/<filename>`)
- the stored outline, evidence and plain-outline copies in `_work/`, the record's `format`, `language`, `source_base_url`, `learning` and `briefing`
- the self-check command with `--out <output>/<new-slug>`
- **depth**: tell them the exact output path, and that in this layout relative links to existing site pages and the reference (`link_style: relative`) start with `../../`, and `include=` paths are relative to their own folder (`multi-audience.md`, "One folder deeper"). Interlinks need no change.
- integration mode: the refreshed `site-profile.yaml`, and the chapter's `related_pages` and `api_refs` from the outline
- the note about voice in step 5.3 if the outline predates 1.8
- writers must not link to other audience folders and must not add a switcher

After they return, confirm every expected file exists and re-spawn any writer whose file is missing.

## 8. Assemble

For each new audience:
- `index.qmd` and `glossary.qmd` as in write step 7 (website form, in the audience's folder, with the glossary pitched at that audience; stakeholder glossary from `plain-outline.yaml`). Include `learning` reading paths if the record says so, and the evidence-based "Known issues" callout for advanced audiences.
- Navigation: for `add`, add the menu item and sidebar for the audience (`multi-audience.md`); for `convert` it is already done in step 6c; for `replace` it is done or unneeded.
- Landing page: for `add`, edit `<output>/index.qmd` to add a button for the audience, copying the existing buttons' pattern.
- **Switcher**, for `convert` and `add`: run over **all** audiences, existing ones first in their order:
  ```
  python <write>/scripts/add_audience_switcher.py --root <output> --audiences "<slug>=<Label>,..." --label "<label>"
  ```
  Labels and the switcher label as in `multi-audience.md` ("Reading level" only when every audience is `beginner` or `intermediate`; otherwise "Written for"). It is idempotent and refreshes the existing pages' switchers.

## 9. Mechanical checks (no AI)

Before spending critic time, prove the layout change is sound:
```
python <write>/scripts/check_links.py --out <output> --project <docs, or <output> if standalone>
python <write>/scripts/check_snippets.py --repo <target> --out <output>/<slug>      # for the moved audience and the new one
```
(add `--no-code` for stakeholder folders). Fix what the checks flag if it is yours to fix: a link that missed its `../`, a missing switcher. The existing audience's prose is not to be rewritten.

## 10. Critique (new audience only)

Skip if `critique=off`. Otherwise follow write step 8 for each new audience, over `<output>/<new-slug>` (or `<output>` for `replace`) with its style block and the stored outline, evidence and plain outline, writing to `_work/critique/<slug>/`. Existing audiences are not critiqued: they haven't changed.

## 11. Review & render

As in write step 9: one `tutorial-reviewer` per new audience, over its folder, with `render: skip` and the path to `multi-audience.md` when the layout is multi-audience, in parallel. Tell it which pages are new and that it must not restyle other audiences' pages. Resume it once for unresolved must-fix findings, then stop.

Then render once yourself: `quarto render <output>` (integration mode: `quarto render <docs>/<section>`, which renders only the tutorial with the site's config; never a full-site render). On errors, resume the reviewer for the affected audience with the error text, then render again, at most twice. Delete `_site`/`_book` afterwards only if it didn't exist before. In integration mode with quartodoc, a full-site render stays the user's call: tell them to run `quarto render <docs>` (or `quarto preview <docs>`) to see the redirects and navigation in place.

## 12. Links into the tutorial from the rest of the site (convert only)

Page URLs gained a folder. The old chapter URLs redirect, but the *source* links in the user's own pages don't. Grep the site (read-only) for `<section>/` links that aren't to `index.qmd`, in every `.qmd`, `.md`, `.ipynb` and `_quarto.yml`, outside `<output>`, and list them with the new path to use (`<section>/<old-slug>/<file>`). **Do not edit the site's pages.** Also check for the quartodoc config (`quartodoc:` in `_quarto.yml`) pointing anywhere into the section; it never should.

## 13. Refresh the record

Write the JSON inputs to `_work/` and run:
```
python <write>/scripts/write_record.py extend --repo <target> --tutorial <output> --audiences <_work/audiences.json> [--pages <_work/new-pages.json>] [--chapter-tests <_work/chapter-tests.json>] [--format website] [--source-base-url <value>] --outline <_work/outline.yaml> [--plain-outline ...] [--evidence ...] [--site-profile ...] --styles-dir <_work> [--rename-style style.md=style-<old>.md] --note "added <slugs> (<layout>)"
```
- `audiences.json`: the **complete** new list, each `{slug, preset, folder, kind}`. For `convert`, the old audience's `folder` becomes `<old>`; for `replace`, the old audience is replaced by the new one, with `folder: "."`.
- `new-pages.json`: the new stakeholder audiences' pages (`audience`, `id`, `filename`, `evidence`) from `plain-outline.yaml`, as in write step 7.
- `chapter-tests.json`: `{chapter id: [test paths]}` from the outline, only if step 5.3 filled them in.
- `--rename-style`: for `convert`, move the old flat `style.md`; `--remove-style` anything for an audience that no longer exists.
- Existing chapters keep their recorded hashes, because they were checked fresh in step 3.

Then run `python <write>/scripts/check_tutorial.py --repo <target> --tutorial <output>` and report anything it flags. It should report no stale chapters, and clean snippets and links for every audience folder.

## 14. Finish

Delete `<output>/_work/` unless `keep_work` (integration mode: only that; keep the `.bak` of `_quarto.yml` if one was made). Report:
- the layout that was used, the new audience folder(s), and the new files
- what moved or was overwritten, the pages given redirects, and the navigation lines that changed (integration mode: the `_quarto.yml` diff)
- which analysis was reused (outline, evidence, plain plan) and what had to be gathered again, if anything
- the critics' verdicts and the reviewer's changes for the new audience, and any unresolved must-fix findings
- whether the render succeeded, and the step-12 list of links elsewhere in the site that the user may want to update
- `git status` on the tutorial folder, so the user can review the diff before committing. **Never commit or push for the user.** Mention `_backup-pre-add-audience/` if one was made.
- the CI template (`TUTORIAL_DIR`) needs no change: the tutorial folder is the same, and `check_tutorial.py` now checks every audience folder.
