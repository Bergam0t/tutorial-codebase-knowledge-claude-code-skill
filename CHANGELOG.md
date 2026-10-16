# Changelog

All notable changes to this plugin are listed here. Each release bumps `version` in `.claude-plugin/plugin.json`. Users who installed from the marketplace only receive changes when the version changes. New entries go under **Unreleased** until a release is cut (see [RELEASING.md](RELEASING.md)).

## Unreleased

- The CI freshness template now pins `PLUGIN_REF` to a plugin release tag instead of `main`, for reproducible checks.
- **Keep the voice-independent analysis.** The tutorial folder now also keeps `_evidence.yaml` and (in integration mode) `_site-profile.yaml` next to `_outline.yaml`, so a later run, such as adding an audience in a different voice, needn't repeat that work. `_generation.json` moves to `schema` 2, adding `source_base_url`; `/codebase-tutorial:update` still reads schema 1 records and upgrades them when it refreshes the record.
- The analyst now always fills in each abstraction's `tests` (it used to only for advanced audiences), and writes `summary` and `description` in a neutral, factual register without analogies, so the stored outline suits any later audience. Analogies and tone come from each audience's style block and writers.
- `/codebase-tutorial:update` refreshes stored evidence incrementally (new update mode for `tutorial-evidence-gatherer`) instead of regathering it all.
- New `relayout.py` (moves a flat tutorial into an audience folder, re-basing relative links, `include=` paths and redirect aliases, tested on a quartodoc site) and `write_record.py extend` (changes the record's audiences while keeping existing chapters' hashes, and logs the change in `history`).
- Fix: `check_links.py` now recurses into audience folders. It used to read only the `.qmd` files directly in `--out`, so `check_tutorial.py` and the CI template skipped the links of every page in a multi-audience tutorial.
- Fix: multi-audience tutorials in integration mode now tell writers their pages are one folder deeper, so relative links to existing site pages and the reference start with `../../`.

## 1.7.0

- **Learning aids** (`learning=on`): a self-test at the end of every chapter (beginner, intermediate, architect, user) or a hands-on exercise with hints, a test command and a solution sketch (contributor); reading paths on each overview page; and a "first contribution" list from good-first-issue issues (new `starter_issues` evidence). Answers are verified by the accuracy critic.
- **Stakeholder briefing** (`briefing=pdf|docx|pdf,docx`): a 500-800 word, print-ready summary per stakeholder audience, written after the audience's other pages and limited to claims they make. Rendered to PDF (Typst) and/or Word; in a website the page links to the downloads, in a book they are rendered explicitly and linked from the overview.
- The record's `args` keep `learning` and `briefing`, so `/codebase-tutorial:update` repeats them and regenerates the briefing whenever any page of its audience changes.

## 1.6.0

- **`/codebase-tutorial:update`**: refreshes an existing tutorial after the code changes. It reads `_generation.json`, finds the chapters whose source files changed, updates the outline in place (stable ids, names and filenames), has the writers *revise* only those chapters, regenerates the overview, glossary entries and footer if needed, re-critiques only what changed (plus neighbouring chapters for accuracy), reviews, renders and refreshes the record. It stops and recommends a full run when the set of chapters would change, and never commits.
- **Revision mode** for the chapter writer and plain writer, **update mode** for the analyst and plain planner, and an `only:` scope for the three critics.
- **`check_drift.py`**: lists stale chapters and unmapped changes from the generation record, with no AI.
- **`check_tutorial.py`**: runs drift, snippet and link checks per audience folder, with a GitHub step summary and a `--strict` mode.
- **CI template** `skills/update/templates/tutorial-freshness.yml`.
- The record now also keeps the resolved style blocks (`_styles/`), so updates keep the original voice.

## 1.5.0

- **Project config**: an optional `.codebase-tutorial.yml` in the documented repo holds audiences, format, language, extensions, include/exclude and so on, so runs are reproducible. Command-line options override it. Two free-text keys: `focus` (a hint for the analyst) and `notes` (house terminology, added to every style block). For cloned URL targets the skill shows the config and asks before applying it. New `config=` option.
- **Generation record**: every run writes `_generation.json` (plugin version, commit, resolved options, and a blob hash of every source file each chapter or stakeholder page depends on) and a copy of the outline into the tutorial folder, surviving the `_work/` cleanup. New `write_record.py` script.
- **"Generated from" line**: the page footer (or the attribution line in integration mode) names and links the commit the tutorial describes.

## 1.4.0

- **Stakeholder audiences (no code)**: four new presets, `stakeholder-decision-maker`, `stakeholder-domain-expert`, `stakeholder-product-owner` and `stakeholder-public`. Each gets its own short set of question-led, zero-code pages (from a shared page menu) instead of one chapter per abstraction. Components get plain-English names, with technical names only in the glossary.
- New `tutorial-plain-planner` agent: translates the outline and evidence into `plain-outline.yaml` (plain names, information flows, personal data the code visibly handles, decision rules with real values, assumptions, dependencies, glossary, and page plans), with every item tied to a code location.
- New `tutorial-plain-writer` agent and `stakeholder.md` reference: zero-code rules, the page menu, the plan for each preset, and the writing style.
- `check_snippets.py --no-code`: fails on code blocks, and warns on inline code, paths and identifier-like tokens in prose.
- The evidence step also records maintenance signals (recent activity, contributor counts, latest release, CI, tests, licence).
- The critics and reviewer gained stakeholder-specific checks. Multi-audience runs can mix stakeholder and technical audiences.

## 1.3.0

- **Quarto extensions**: a new `extensions=` option, and a vetted, pinned list in `extensions.md`: `code-window` and `code-line-style` (both on by default), plus `include-code-files`, `value-box`, `highlight-text` and `fontawesome`. `lightbox` maps to Quarto's built-in feature. The skill installs them with `quarto add --no-prompt`, sets the filter order (`value-box` must precede `highlight-text`), and gives writers only the syntax for what is actually installed. Unvetted `owner/repo@tag` extensions need user confirmation. In integration mode, the site's existing extensions are used, and the skill asks before adding new ones.
- `check_snippets.py` understands `include-code-files` blocks: missing files (which render as silently empty blocks), bad ranges and caption mismatches are reported, and `--stamp`/`--restamp` record content hashes, so that later runs detect source drift.
- The site surveyor records the extensions and filters already present.

## 1.2.0

- **Advanced audiences**: three new presets, `advanced-contributor`, `advanced-architect` and `advanced-user`. They use verbatim-first code (up to 150 lines), a compressed chapter structure, a conversational expert voice, and preset-specific extra sections in every chapter (e.g. "Extending this", "Sharp edges", "Design notes", "Limitations and open questions").
- New `tutorial-evidence-gatherer` agent and `evidence.md` reference. For advanced audiences, the agent collects rationale and known issues from git history, repo docs, TODO/FIXME markers, tests, and GitHub issues/PRs (via `gh`, if available). Chapters cite this evidence and label each design explanation as documented or inferred. If GitHub couldn't be checked, advanced overview pages say so and point readers to the issue tracker.
- Remote targets are cloned with full history (`--filter=blob:none`) when an advanced audience is selected.
- The critics check advanced-specific failure modes: padded basics, boilerplate extra sections, uncited rationale stated as fact, and simplified code in verbatim-first styles.
- The multi-audience switcher label becomes "Written for" when the audiences include roles rather than only reading levels.

## 1.1.0

- **Multiple audiences**: `audience=beginner,intermediate` (or any list, free-text entries in quotes) produces one version of the tutorial per audience from a shared outline. Every page gets a reading-level switcher that opens the same chapter at another level, each level has its own sidebar, and a landing page lets readers choose their level. Output is a website. This works in integration mode for website-based docs sites.
- New script `add_audience_switcher.py`, and new reference `multi-audience.md`.
- The reviewer accepts `render: skip`, so parallel per-audience reviews don't collide. The orchestrator renders once at the end.

## 1.0.0

First release.

- `/codebase-tutorial:write` turns a repository into a multi-chapter Quarto book or website.
- Integration mode (`docs=`) adds a tutorial to an existing Quarto or quartodoc site, linking to its API reference.
- Seven subagents: analyst, chapter writer, three critics (clarity, code fidelity, accuracy), reviewer, and site surveyor.
- `check_snippets.py` and `check_links.py` provide mechanical checks for snippet fidelity and links (including quartodoc interlinks).
- Audience presets (`beginner`, `intermediate`, free text) and the `1980s` theme overlay.
