# Changelog

All notable changes to this plugin are listed here. Each release bumps `version` in `.claude-plugin/plugin.json`. Users who installed from the marketplace only receive changes when the version changes.

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
