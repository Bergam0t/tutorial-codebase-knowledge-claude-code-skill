# Changelog

All notable changes to this plugin are listed here. Each release bumps `version` in `.claude-plugin/plugin.json`. Users who installed from the marketplace only receive changes when the version changes.

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
