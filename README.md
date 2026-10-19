# Codebase Tutorial: a Claude Code plugin

Point Claude Code at a repository and get back a multi-chapter tutorial that explains how the codebase works. The tutorial comes out as a **Quarto book or website** you can render straight away, or it can be **added to an existing Quarto/quartodoc documentation site**, with links into its API reference.

This is an agentic rework of [AI Codebase Knowledge Builder](https://github.com/The-Pocket/PocketFlow-Tutorial-Codebase-Knowledge) (the PocketFlow "Tutorial-Codebase-Knowledge" project). The original was a fixed pipeline of single-shot LLM prompts. This version keeps its core ideas:

- find the 5–10 core abstractions
- map how they relate
- order them for teaching
- write one chapter per abstraction, pitched at the reader you choose (intermediate by default)

The work is delegated to Claude Code subagents that explore the code themselves, write chapters in parallel, and check each other's work.

---

## Contents

- [What you get](#what-you-get)
- [Requirements](#requirements)
- [GitHub access](#github-access)
- [Installation](#installation)
- [Quick start](#quick-start)
- [Options](#options)
- [Stakeholder presets (no code)](#stakeholder-presets-no-code)
- [Learning aids](#learning-aids)
- [Stakeholder briefing](#stakeholder-briefing-pdf--word)
- [Quarto extensions](#quarto-extensions)
- [Project config and the generation record](#project-config-and-the-generation-record)
- [Keeping the tutorial up to date](#keeping-the-tutorial-up-to-date)
- [Adding another audience later](#adding-another-audience-later)
- [Adding a tutorial to an existing Quarto / quartodoc site](#adding-a-tutorial-to-an-existing-quarto--quartodoc-site)
- [How it works](#how-it-works)
- [Quality checks](#quality-checks)
- [Customising](#customising)
- [Troubleshooting](#troubleshooting)
- [Repository layout](#repository-layout)
- [Credits](#credits)
- [License](#license)

---

## What you get

A standalone run produces a ready-to-render Quarto project:

```
output/<project>/
  _quarto.yml           # book or website config
  index.qmd             # overview: summary, relationship diagram, chapter list
  01_<concept>.qmd      # one chapter per core abstraction
  02_<concept>.qmd
  ...
  glossary.qmd          # every key term, linked to the chapter that introduces it
```

Each chapter opens with a concrete use case and builds up the concepts one at a time. It then walks through what happens under the hood, with a sequence diagram, before looking at the real code. Chapters use Quarto features where they help the reader:

- cross-references between chapters
- labelled diagrams
- code annotations
- **Simplified / Real code** tabs
- collapsible "deep dive" callouts
- margin definitions
- "View source" links to the exact lines on GitHub/GitLab

Every code block is either a **verbatim** excerpt from the repo or clearly marked as **illustrative**, and a script checks this. See [Quality checks](#quality-checks).

---

## Requirements

| | Required? | Notes |
|---|---|---|
| [Claude Code](https://claude.com/claude-code) | Yes | The CLI, desktop app or IDE extension |
| Python 3.9+ | Yes | Runs the two checking scripts (standard library only) |
| `git` | Yes | Cloning URLs, source permalinks, change checks |
| [Quarto](https://quarto.org) 1.4+ | Recommended | Needed to render and validate the output. Without it, the render step is skipped |
| [quartodoc](https://machow.github.io/quartodoc/) | Optional | Only for integration with a quartodoc site, and only if the API reference isn't already built |
| [GitHub CLI](https://cli.github.com) (`gh`), signed in | Optional | Lets the advanced audiences cite open issues and PRs. Without it, advanced pages tell readers to check the issue tracker themselves. See [GitHub access](#github-access) |

---

## GitHub access

Most runs never touch GitHub. Three things can. Only the first is essential, and only when you give a URL instead of a local path:

| What | Needs | Without it |
|---|---|---|
| Cloning a repository by URL (`/codebase-tutorial:write https://github.com/owner/repo`) | `git` that can already clone that repository | The run stops, since there is nothing to read. A local path never needs this |
| Citing open **issues and pull requests** (advanced and stakeholder audiences, and the "first contribution" list with `learning=on`) | The [GitHub CLI](https://cli.github.com) `gh`, signed in, with read access to the repository | The run carries on. Advanced pages say GitHub wasn't checked and tell readers to look at the issue tracker themselves |
| **"View source" links** to exact lines | The commit you documented must be pushed to a GitHub or GitLab remote | The links are left out. Commit and push first if you want them |

### Set it up

1. Install `gh` ([cli.github.com](https://cli.github.com)) and sign in once with `gh auth login`.
2. Check it from the same terminal you start Claude Code in: `gh auth status` should say you're logged in, and `gh issue list --repo owner/repo --limit 1` should answer without an error.
3. **Private repositories:** sign in with an account that can read the repository's issues and pull requests (`gh auth login` asks for the `repo` scope by default). To clone a private repository by URL, run `gh auth setup-git` so `git` uses the same sign-in, or use an SSH URL if you have a key set up.
4. **Headless or CI runs:** there is no one to sign in, so set a token in the environment instead: `GH_TOKEN=<token>`, with read access to the repository's contents, issues and pull requests. `gh` uses it automatically.

Only `github.com` repositories are searched. GitHub Enterprise Server and other hosts are treated as "GitHub unavailable", and the rest of the run is unaffected.

### Permissions in Claude Code

`gh` and `git` run through Bash, so in the default permission mode Claude Code asks before the first call of each kind. The skill only reads: it runs `gh auth status`, `gh issue list`, `gh pr list` and `gh issue view`, and never anything that writes to GitHub or the repository. To approve them once, choose "don't ask again" when prompted, or add allow rules to your settings:

```json
{
  "permissions": {
    "allow": [
      "Bash(gh auth status:*)",
      "Bash(gh issue list:*)",
      "Bash(gh pr list:*)",
      "Bash(gh issue view:*)"
    ]
  }
}
```

A headless run can't answer a prompt, so without rules like these (or a more permissive mode) the GitHub calls are declined and the run behaves as if GitHub were unavailable.

### What it keeps

Issue and PR **titles, numbers, states and links** only, plus counts of recent commits and contributors. It never records issue bodies, comments, or the names or emails of authors. Everything it reads from GitHub is treated as untrusted data: it is summarised, and instructions inside it are not followed. The result is saved as `_evidence.yaml` beside the tutorial, with the date it was gathered.

If something isn't working, the final report says why GitHub was skipped (for example "gh not installed", "gh not authenticated", "not a GitHub repo", "rate limited"). See also [Troubleshooting](#troubleshooting).

---

## Installation

This repository is a Claude Code **plugin**, and also its own plugin **marketplace**. You install it in two commands.

**Inside a Claude Code session:**

```
/plugin marketplace add Bergam0t/tutorial-codebase-knowledge-claude-code-skill
/plugin install codebase-tutorial@bergam0t
```

**Or from your shell:**

```bash
claude plugin marketplace add Bergam0t/tutorial-codebase-knowledge-claude-code-skill
claude plugin install codebase-tutorial@bergam0t
```

Then start a new session, or run `/reload-plugins`. Type `/codebase-tutorial:write` to check it's there.

The plugin installs the skill and all ten agents together. It's installed at **user scope**, so it's available in every project on your machine.

- **Install it for a whole team on one repository**: run `claude plugin marketplace add Bergam0t/tutorial-codebase-knowledge-claude-code-skill --scope project` in that repo, then commit the `.claude/settings.json` it writes. Each teammate still runs the install command once.
- **Update**: new versions arrive when the plugin's `version` changes. To update now, run `/plugin marketplace update bergam0t` in a session, or `claude plugin update codebase-tutorial@bergam0t` in your shell. To update automatically, open `/plugin` → **Marketplaces** → `bergam0t` → **Enable auto-update**.
- **Uninstall**: `claude plugin uninstall codebase-tutorial@bergam0t`, or use `/plugin`.

### Developing locally

To try changes without publishing them, load the plugin straight from a clone:

```bash
git clone https://github.com/Bergam0t/tutorial-codebase-knowledge-claude-code-skill
claude --plugin-dir ./tutorial-codebase-knowledge-claude-code-skill
```

Edits take effect at the next session start, or when you run `/reload-plugins`. Before you push, check the manifests:

```bash
claude plugin validate ./tutorial-codebase-knowledge-claude-code-skill
```

**Releasing**: bump `version` in `.claude-plugin/plugin.json` and add an entry to [CHANGELOG.md](CHANGELOG.md). Users who installed from the marketplace don't receive commits pushed without a version bump.

---

## Quick start

Open Claude Code in the repository you want to document, then run:

```
/codebase-tutorial:write .
```

You can also just ask, for example "write an onboarding tutorial for this repo", and Claude should pick up the skill.

When it finishes, preview the result:

```bash
quarto preview output/<project>
```

More examples:

```
# A website for experienced developers, with a 1980s theme
/codebase-tutorial:write . format=website audience=intermediate theme=1980s

# Document a GitHub repository without cloning it yourself
/codebase-tutorial:write https://github.com/owner/repo

# Document another local repo, writing the output somewhere specific
/codebase-tutorial:write C:\code\my-lib output=C:\docs\my-lib-tutorial

# Narrow the scope, write in French, keep intermediate files for inspection
/codebase-tutorial:write . include=src/** exclude=src/legacy/** language=French keep_work

# Headless (no interactive session)
claude -p "/codebase-tutorial:write . format=book"
```

> **Tip:** by default the output goes to `output/` inside the repo you are in. Add `output/` to that repo's `.gitignore` if you don't want to commit it.

---

## Options

All options are `key=value` pairs after the optional target.

| Option | Default | Description |
|---|---|---|
| *target* | `.` | Local path or Git URL of the repository to document |
| `format` | `book` | `book` (numbered chapters and appendix) or `website` (sidebar navigation) |
| `audience` | `intermediate` | `beginner`, `intermediate`, `advanced-contributor`, `advanced-architect`, `advanced-user`, `stakeholder-decision-maker`, `stakeholder-domain-expert`, `stakeholder-product-owner`, `stakeholder-public`, or free text describing the reader, e.g. `audience="data scientists new to async Python"`. **List several** (comma-separated) to get switchable versions: see [Multiple audiences](#multiple-audiences) |
| `theme` | none | Optional flavour overlay. Ships with `1980s` |
| `language` | `English` | Language of all generated prose. Code and identifiers stay as-is |
| `output` | `output/<project>` | Where to write the standalone project |
| `budget` | `standard` | `low`, `standard` or `high`. Trades cost for depth: `high` runs writers, reviewer and accuracy critic on Opus; `low` uses 6 chapters, no critique |
| `max_abstractions` | `8` | Upper bound on chapters (it aims for 5 to this number) |
| `include` / `exclude` | sensible defaults | Comma-separated globs. Tests, docs, build output, vendored deps, lockfiles and binaries are excluded by default |
| `critique` | `on` | `off` skips the three critic agents (faster and cheaper; the mechanical checks still run) |
| `extensions` | `code-window`, `code-line-style` | Quarto extensions to install and use. `none`, an explicit list, `+name` / `-name` to change the defaults, or `owner/repo@tag` for others. See [Quarto extensions](#quarto-extensions) |
| `learning` | `off` | `on` adds a self-test (or, for contributors, an exercise) to every chapter, reading paths to each overview, and a first-contribution list. See [Learning aids](#learning-aids) |
| `briefing` | `none` | `pdf`, `docx` or `pdf,docx`: stakeholder audiences also get a short print-ready briefing. See [Stakeholder briefing](#stakeholder-briefing-pdf--word) |
| `config` | `.codebase-tutorial.yml` in the target | Path to a project config file, or `none` to ignore it. See [Project config](#project-config-and-the-generation-record) |
| `keep_work` | off | Keep `_work/` (working copies of the outline, evidence and style block, and the critic findings) for inspection. The outline, evidence and styles are also kept in the tutorial folder either way |
| `docs` | none | Integration mode: the path to an existing Quarto project to add the tutorial to (see below) |
| `section` | `tutorial` | Integration mode: the subfolder of `docs` to create |

### Audience presets

There are nine presets in three families. `beginner` and `intermediate` are the two **reading levels**: they cover the same ground in the same chapter structure and differ only in how much is explained, how much code is simplified and how many analogies are used. That is why they sit in a table of their own here, and why `intermediate` is the default: it assumes the reader knows the language but not this codebase. Pass `audience=beginner` if your readers are new to programming itself. The other two families change *what* is written, not just how simply, so each has its own section below:

- [**Advanced presets**](#advanced-presets) (`advanced-contributor`, `advanced-architect`, `advanced-user`): for experienced engineers. Real code, extra sections for rationale, limitations and extension points, and researched evidence from the repository's history and issues.
- [**Stakeholder presets**](#stakeholder-presets-no-code) (`stakeholder-decision-maker`, `stakeholder-domain-expert`, `stakeholder-product-owner`, `stakeholder-public`): for non-technical readers. No code at all, and a short set of question-led pages instead of one chapter per component.

You can also describe any reader in your own words (`audience="data scientists, new to async Python"`), and list several audiences to get a version for each (see [Multiple audiences](#multiple-audiences)).

| | `beginner` | `intermediate` |
|---|---|---|
| Reader | New to programming concepts as well as to this codebase | Knows the language, new to this codebase |
| Code block target | 20 lines (up to 24 accepted), aggressively simplified | 100 lines (up to 120 accepted), more real code |
| Diagrams | ≤ 5 participants | ≤ 10 participants |
| Analogies | Plenty | Sparing; never patronising |
| Tabs open on | Simplified | Real code |
| Collapsed callouts hold | Advanced internals ("Deep dive") | Background refreshers |
| Voice | Warm and welcoming | Readable, British English |

### Advanced presets

These three presets are for experienced engineers. They share:
- **verbatim-first code**: real excerpts aiming for 150 lines or fewer (up to 180 accepted); illustrative blocks only for pseudocode or usage examples
- **a compressed structure**: one-paragraph motivation, brief usage, most of the chapter on internals
- **a conversational expert voice**: peer to peer, occasional analogies, British English

Each one adds its own **extra sections** to every chapter:

| | `advanced-contributor` | `advanced-architect` | `advanced-user` |
|---|---|---|---|
| Reader | About to change the codebase | Assessing the design | Expert user pushing it to its limits |
| Main emphasis | Extension points, edge cases | Design rationale, limitations and debt | Edge cases, performance, configuration |
| Extra sections | Extending this · Sharp edges · Design notes · Limitations and open questions | Design notes · Coupling and extensibility · Failure modes · Limitations and open questions | Performance and limits · Sharp edges · Design notes · Known issues |
| Switcher label | Contributor | Architect | Power user |

**Where the "why" comes from.** For advanced audiences, an extra agent gathers evidence once, before the chapters are written:
- commit history for each abstraction's files
- design docs and ADRs, CONTRIBUTING and CHANGELOG
- TODO/FIXME/HACK markers
- the tests covering each area
- open **GitHub issues and pull requests**, if the `gh` CLI is installed and signed in

Chapters cite this evidence inline, and every design explanation is labelled either as documented (citing a commit, doc or issue) or as *inferred from the code*. If GitHub couldn't be checked, each advanced overview page says so, and suggests readers check the issue tracker themselves for known issues, limitations and work in progress. If it was checked, the page gives the date of the check.

When documenting a remote repository, the clone keeps its full commit history (`--filter=blob:none`) so this evidence is available.

```
/codebase-tutorial:write . audience=advanced-contributor
/codebase-tutorial:write . audience=beginner,advanced-contributor,advanced-architect
```

### Stakeholder presets (no code)

These four presets are for readers with **no programming knowledge**. The pages contain no code, no file paths and no technical names. Each component gets a plain-English name ("the request handler"), and its technical name appears once, in the glossary, for anyone who later needs to talk to the developers.

Instead of one chapter per component, each preset gets its **own short set of question-led pages**, and every page opens with an "In brief" summary:

| Preset | For | Pages |
|---|---|---|
| `stakeholder-decision-maker` | Managers, funders and executives | Overview · What it does · How it works · Assumptions and limits · Risks · Keeping it running · Questions to ask · Glossary |
| `stakeholder-domain-expert` | Subject-matter experts who need to trust and sanity-check it | Overview · What it does · How it works · How decisions are made · Reading the results · Assumptions and limits · Glossary |
| `stakeholder-product-owner` | People who steer priorities and scope | Overview · What it does · How it works · Information flow · Changing it · Assumptions and limits · Questions to ask · Glossary |
| `stakeholder-public` | Lay readers and end users | Overview · What it does · Your data · Reading the results · Assumptions and limits · Glossary |

How it works:
- **Planning.** A planning agent reads the code to find what stakeholders need but the technical outline doesn't capture: what information goes in and comes out, where it's stored or sent, any personal data the code visibly handles, the rules and thresholds applied (with their real values), and the assumptions built in. Every item is tied to a code location, so the accuracy critic can check it. Anything that can't be determined is stated as such, never guessed.
- **Known limitations.** These come from the same evidence step as the advanced presets. They're translated into plain language, with issue links only in a collapsed "For the technical team" box. Decision-makers also get maintenance signals: recent activity, the number of active contributors (counts only), the latest release, and whether tests and CI exist.
- **Checks.** `check_snippets.py --no-code` fails on any code block, and flags inline code, file paths and identifier-like words that slip into the text. The clarity critic reads as someone with no programming knowledge. The accuracy critic checks that the plain-language simplifications are still true, and that claims about data, security or accuracy are supported by the code. Pages never state or imply legal compliance.

They can be combined with the other audiences, e.g. `audience=intermediate,stakeholder-decision-maker`. The switcher's overview and glossary buttons map directly between versions; other pages open the other version's overview.

```
/codebase-tutorial:write . audience=stakeholder-domain-expert
/codebase-tutorial:write . audience=beginner,advanced-contributor,stakeholder-decision-maker,stakeholder-public
```

### Learning aids

`learning=on` turns the tutorial from something to read into something to work through:

| Audience | End-of-chapter section |
|---|---|
| beginner, intermediate | **Check your understanding**: 3 questions (recall, reasoning, tracing the use case), each with a collapsed answer |
| advanced-contributor | **Try it**: one hands-on exercise in the chapter's code, with collapsed hints, the test command to check it, and a solution sketch; plus 2 "where would you look?" questions |
| advanced-architect | **Design questions**: scenarios about load, failure and change |
| advanced-user | **Check your setup**: scenarios about configuring and using the area |

Every overview page also gets **Reading paths** (for example "New to the project", "Adding a new …"), built from the outline's prerequisites. For contributors, **Your first contribution** lists open "good first issue" / "help wanted" issues (via `gh`, as of the date gathered) and points to `CONTRIBUTING.md`.

Answers are checked by the accuracy critic against the code: the skill never invents output, and an exercise never claims to have been run.

### Stakeholder briefing (PDF / Word)

`briefing=pdf`, `briefing=docx` or `briefing=pdf,docx` gives each stakeholder audience a **one- to two-page briefing**: a summary of that audience's pages, written to be printed, emailed or filed. It follows the same zero-code rules and contains no claim that the audience's other pages don't make.

- **Website**: `quarto render` produces `briefing.pdf` and `briefing.docx` alongside the HTML page, and the page links to them.
- **Book**: the files are rendered explicitly and linked from the overview.
- PDF is produced with Quarto's bundled Typst, so no LaTeX installation is needed.

### Quarto extensions

The skill installs Quarto extensions into the tutorial project with `quarto add`, configures them, and tells the writers exactly how to use them. Each vetted extension is pinned to a release:

| Extension | What it adds | Default? |
|---|---|---|
| [`code-window`](https://github.com/mcanouil/quarto-code-window) | Frames code blocks as application windows, titled with the snippet's file caption. Needs Quarto ≥ 1.10.19 | ✔ |
| [`code-line-style`](https://github.com/EmilHvitfeldt/quarto-code-line-style) | Highlights, focuses or dims specific lines in a block, so excerpts can stay complete while pointing at what matters | ✔ |
| [`include-code-files`](https://github.com/quarto-ext/include-code-files) | Pulls verbatim excerpts straight from the source by line range (see below) | |
| [`value-box`](https://github.com/bergam0t/quarto-value-box) | Value boxes for a few key, verifiable figures (overview facts, performance numbers) | |
| [`highlight-text`](https://github.com/mcanouil/quarto-highlight-text) | Highlights key terms on first use. Needs Quarto ≥ 1.10.19 | |
| [`fontawesome`](https://github.com/quarto-ext/fontawesome) | Font Awesome 6 icons | |
| `lightbox` | Click-to-zoom images. Built into Quarto ≥ 1.4, so nothing is installed. Images only, not diagrams | |

```
/codebase-tutorial:write . extensions=+value-box,+fontawesome
/codebase-tutorial:write . extensions=include-code-files,code-window
/codebase-tutorial:write . extensions=none
```

- **Other extensions:** pass `owner/repo@tag`. The skill asks before installing anything outside the vetted list, because extension filters run code on every render. It then works out the usage notes from the extension's own files.
- **How writers know the syntax:** they receive notes for exactly the extensions enabled in that run, including one worked example of a code block using them together, and each audience's style says how much line highlighting suits it. The reviewer checks both.
- **Filter order:** the skill orders filters correctly. For example, `value-box` must run before `highlight-text`, or the value boxes silently lose their colours.
- **If an install fails:** the skill skips that extension, so writers never use syntax for something that isn't installed.
- **Integration mode:** the defaults are *not* installed automatically. See the next section.

**In an existing Quarto / quartodoc site.** The site's `_extensions/` folder and `filters:` list are yours, so the skill treats the defaults differently there. It surveys what the site already has, then sorts each requested extension (the defaults included) into one of three cases:

| Situation | What happens |
|---|---|
| Installed in `_extensions/` **and** listed under `filters:` | Used straight away. Writers get its usage notes. |
| Installed but **not** under `filters:` | Needs one added line in `_quarto.yml`, so the skill **asks first**. |
| **Not installed** | Needs a new `_extensions/<name>/` folder and a `filters:` line, so the skill **asks first**. |

Anything you decline is skipped, and the writers are told not to use its syntax. **If the skill can't ask** (a headless run, for example), it counts as declined. That is the usual reason a tutorial in an existing site comes out without framed code windows or line highlighting: a plain site has neither extension, so nothing was added. Also, extension *options* (such as the `code-window` style) are never added to an existing site without asking.

To get the extensions you want in an existing site:
- **Say yes when asked.** The question lists each extension and exactly what it would change in your site.
- **Or install them yourself first.** Run `quarto add mcanouil/quarto-code-window@1.6.0` (and so on, using the sources pinned in [`extensions.md`](skills/write/references/extensions.md)) in the docs folder and list the filter under `filters:`. The skill then finds them in the first row of the table and uses them without asking.
- **Check the final report.** It lists the extensions installed or used, and those skipped with the reason.

Extension filters run code at every render, which is why a pinned release is used and your site is never changed without a question. `/codebase-tutorial:add-audience` reuses the extension list recorded in `_generation.json` and doesn't install anything again.

**About `include-code-files`.** Included excerpts can't contain copying mistakes, but they need care:
- **Location:** it's only enabled when the tutorial lives inside the repository it documents, because includes are relative paths.
- **Missing files:** a wrong path renders as a silently empty block. The snippet checker catches this.
- **Drift:** the checker records a hash of each included excerpt (`--stamp`). If the source later changes under a tutorial, running `python skills/write/scripts/check_snippets.py --repo . --out <tutorial dir>` in CI fails, so prose describing the old lines doesn't go unnoticed.

### Project config and the generation record

**Config file.** To avoid retyping options, put a `.codebase-tutorial.yml` in the root of the repo you're documenting. Every key is optional and uses the option names above; command-line values win over the file.

```yaml
audience: [beginner, advanced-contributor, stakeholder-decision-maker]
format: website
language: English
exclude: ["src/legacy/**"]
extensions: [code-window, code-line-style, include-code-files]

focus: "The plugin system and the scheduler matter most; the CLI wrapper is thin."
notes: |
  Call users "operators", never "customers".
  The product name is "DataBridge", one word.
```

`focus` steers the analyst; `notes` are house terminology added to every writer's style block. Notes are style guidance only: they can't change what the agents are allowed to do. If you point the skill at a cloned URL, it shows you the config it found and asks before applying it. At the end of a run without a config, the skill prints the options it used as a ready-to-paste file.

**Generation record.** Every run writes `_generation.json` into the tutorial folder (Quarto ignores it), plus copies of the analysis it was built from (`_outline.yaml`, and `_evidence.yaml`, `_plain-outline.yaml` and `_site-profile.yaml` when those steps ran) and the style blocks (`_styles/`). Keeping these means a later update, or a new audience, doesn't repeat the analysis. It records the plugin version, the commit, the resolved options, and a content hash of every source file each chapter depends on. Every page footer also says which commit the tutorial describes ("Generated from commit `813d416` on 2026-10-15"), so readers can judge how fresh it is.

### Multiple audiences

List more than one audience to produce a version of the tutorial for each, with a **Reading level** switcher at the top of every page:

```
/codebase-tutorial:write . audience=beginner,intermediate
/codebase-tutorial:write . audience=beginner,intermediate,"data scientists, new to async Python"
```

- Every version comes from **one shared outline**, so all versions have the same chapters in the same order. Only the depth, tone, code length and analogies differ.
- Each page has a row of buttons, one per audience. Clicking one opens **the same chapter** at that level, and the current level is highlighted. Each level has its own sidebar, so readers stay at their chosen level as they move through the chapters. The navbar also lists every level.
- A landing page introduces the project and offers a "Choose your reading level" button for each audience. The first audience listed is the default.
- Free-text audiences get a short label (e.g. "Data scientists") and are written using the `beginner` preset as a template.

Things to know:
- **Output is always a website.** A Quarto book numbers chapters across the whole book, so it can't hold two versions of each chapter. To get separate books instead, run the skill once per audience.
- **Cost scales with the number of audiences.** Each audience gets its own set of chapter writers, three critics and a reviewer, while the analysis runs only once. Two audiences cost roughly twice as much as one. `critique=off` removes the most.
- **Integration mode** works with website-based docs sites. The tutorial's navbar entry becomes a menu with one item per level.

---

## Adding another audience later

You don't have to decide on every audience up front. Once a tutorial exists, add a new voice (another reading level, a contributor version, a no-code stakeholder version) without analysing the code again:

```
/codebase-tutorial:add-audience audience=advanced-contributor
/codebase-tutorial:add-audience audience=stakeholder-decision-maker tutorial=docs/tutorial
```

It reuses what the first run stored beside the tutorial (the outline, the evidence, the stakeholder plan and the style blocks), so only the new audience's writers, critics and reviewer run. It first checks that the existing pages are still current (if the code has moved on, it asks you to run `/codebase-tutorial:update` first, so the versions agree).

If the tutorial has **one audience**, it asks what you want:

| Choice | What happens |
|---|---|
| **Convert to multi-audience** (recommended) | The existing pages move into a folder for their audience, the new one sits beside it, and every page gets the reading-level switcher. Old page URLs keep working through redirects. |
| **Replace the existing voice** | The new voice overwrites the existing pages and the tutorial stays flat, with the same URLs and navigation. The old version survives only in git history. |
| **Separate tutorial** | The new voice becomes its own tutorial in a new folder (or a second section of your site), and the first is left alone. |

If the tutorial already has several audiences, the new one is simply added.

**In an existing Quarto / quartodoc site** the same choices work, with these safeguards:
- Only the tutorial's own lines in `<docs>/_quarto.yml` change (its navbar item and sidebar), by text edit, with a backup and a diff check. quartodoc's sidebar, the reference pages and `objects.json` are never touched.
- Links from the tutorial to your existing pages, to the API reference and to `include=` source files are re-based for the extra folder, and quartodoc interlinks keep resolving.
- Your own pages that link to an old chapter's source path aren't edited: you get a list of them with the new paths. (Readers following old URLs are redirected.)
- A site that is a Quarto **book** can't hold two versions of a chapter, so there you can replace the voice or make a separate section.
- A standalone **book** can be converted too, but it first becomes a website, which rewrites each existing chapter in website form (keeping its voice).

Options: `audience=` (required), `layout=ask|convert|replace|separate`, `tutorial=`, `critique=`, `dry_run`, `keep_work`. Tutorials made before this release lack some stored files; `add-audience` fills in what it needs (it may re-run the evidence step once).

---

## Keeping the tutorial up to date

Code changes; tutorials go stale. Because each run records the commit and a hash of every source file each chapter depends on, you can see exactly what has drifted, and refresh only that.

### See what's stale (no AI, no cost)

```bash
python skills/write/scripts/check_drift.py --repo . --tutorial docs/tutorial
```

```
Tutorial generated from commit 813d416 on 2026-10-15; HEAD is 12 commit(s) ahead.
  STALE  02_router.qmd: src/router.py changed
  fresh  01_overview.qmd
Changed since that commit but cited by no chapter (1):
  - src/newmod.py
1 of 2 chapters/pages stale.
```

(In a plugin install, the scripts are under the plugin's `skills/write/scripts/`.) `check_tutorial.py` runs this together with the snippet and link checks.

### Refresh it

```
/codebase-tutorial:update
```

This finds the tutorial's record, then:
1. runs the drift check
2. asks the analyst to update the outline *in place*, keeping abstraction ids, chapter names and filenames stable
3. asks the writers to **revise** just the affected chapters, keeping everything that is still true
4. regenerates the overview and glossary entries if needed, and updates the "generated from" footer
5. re-critiques only what changed (plus the neighbouring chapters, for accuracy), reviews, renders, and refreshes the record

It uses the options recorded in the original run, so you don't repeat them. It never commits for you; review the diff, then commit.

| Option | Meaning |
|---|---|
| `tutorial=<folder>` | The folder containing `_generation.json` (found automatically if there is only one) |
| `dry_run` | Show what's stale and how many agents an update would run, then stop |
| `critique=off` | Skip the critics (the checkers still run) |
| `ci=install` | Offer to add the CI workflow below |

If the changes add or remove a component (the set of chapters would change), an update would have to rename files and break links, so the skill stops and recommends a full `/codebase-tutorial:write` run instead. To add a new *audience* rather than refresh the existing ones, see [Adding another audience later](#adding-another-audience-later).

### Check freshness in CI

Copy [`skills/update/templates/tutorial-freshness.yml`](skills/update/templates/tutorial-freshness.yml) to `.github/workflows/` in the documented repo and set `TUTORIAL_DIR`. On pull requests, pushes to main and weekly, it runs the three mechanical checks. These need no AI, API keys or cost:

- **Freshness**: which chapters depend on changed files (listed in the job summary; set `STRICT: "true"` to fail on them)
- **Snippets**: verbatim code still matches the repository (fails the job)
- **Links**: relative links, anchors and quartodoc interlinks still resolve (fails the job)

The workflow pins `PLUGIN_REF` to a release tag of this plugin so checks are reproducible. Update it when you upgrade the plugin.

---

## Adding a tutorial to an existing Quarto / quartodoc site

If the project already has a Quarto documentation site, for example a [quartodoc](https://machow.github.io/quartodoc/) API reference, the skill can add the tutorial to it instead of creating a separate project:

```
/codebase-tutorial:write . docs=docs
/codebase-tutorial:write . docs=docs section=guides audience=intermediate
```

If you run the skill on a repo that has a Quarto site and don't pass `docs=`, it asks whether you want to integrate.

**What happens:**

1. **Survey.** An agent reads `docs/_quarto.yml` and the site's existing pages, and records:
   - how the navigation is built
   - which hand-written pages exist and what each covers
   - the house style
   - the quartodoc configuration and every documented API object
2. **Plan around the site.** The tutorial covers what the site is missing (how the pieces fit together, internals, the flow behind the API), instead of repeating existing guides. It links to existing pages where they already explain something.
3. **Link to the API reference.** The first mention of each public symbol links to its reference page. Interlinks such as ``[](`~mypkg.Router`)`` are used if the site has the interlinks filter; otherwise the links are plain relative ones. Chapters explain *how and why*; the reference keeps the signatures and parameters.
4. **Add the files.** New pages go in `docs/tutorial/`. The **only** existing file changed is `docs/_quarto.yml`, and only to add a navbar item and a sidebar entry (or a book part). The edit is inserted as text, so comments and formatting are preserved. A backup is taken, and the change is verified to only add lines.
5. **Verify without disturbing anything.** The skill renders only the tutorial folder, so your other pages' code is never executed. It checks that nothing else in `docs/` changed, and it never rebuilds a quartodoc reference that is committed to git.

The final report includes the exact `_quarto.yml` diff. Preview the whole site with `quarto preview docs`.

**Supported site layouts:**
- websites with quartodoc's multi-sidebar setup
- websites with a single sidebar
- websites with only a navbar
- Quarto books (the tutorial is added as a part)

---

## How it works

```
                        ┌──────────────────────┐
  (integration mode) ──▶│ tutorial-site-surveyor│──▶ site-profile.yaml
                        └──────────────────────┘
┌──────────────────┐
│ tutorial-analyst │──▶ outline.yaml  (abstractions, relationships, chapter order)
└──────────────────┘
          │   orchestrator validates the outline
          ▼                                    ┌────────────────────────────┐
          │  (advanced / stakeholder only) ──▶ │ tutorial-evidence-gatherer │──▶ evidence.yaml
          │                                    └────────────────────────────┘
          │                                    ┌────────────────────────────┐
          │  (stakeholder only) ─────────────▶ │ tutorial-plain-planner     │──▶ plain-outline.yaml
          ▼                                    └────────────────────────────┘
┌───────────────────────────────────────────┐  ┌────────────────────────────────────┐
│ tutorial-chapter-writer  × N  (parallel)  │  │ tutorial-plain-writer × pages      │
│   → 01_*.qmd … NN_*.qmd                   │  │   → question-led, zero-code pages  │
└───────────────────────────────────────────┘  └────────────────────────────────────┘
          │   orchestrator writes index.qmd, glossary.qmd, _quarto.yml
          ▼
┌────────────────┬────────────────┬─────────────────┐
│ critic-clarity │  critic-code   │ critic-accuracy │   (parallel, read-only)
└────────────────┴────────────────┴─────────────────┘
          │   findings files
          ▼
┌───────────────────┐
│ tutorial-reviewer │──▶ applies fixes, runs the checkers, quarto render
└───────────────────┘
```

The **orchestrator** is the skill itself, running in your main Claude Code session. It parses the options, briefs each agent, validates the hand-offs, and assembles the Quarto project.

Chapters are written in parallel, so writers can't read each other's text. Instead, the outline records what each chapter **introduces** and **builds on**, plus a one-line summary of every chapter. Writers use this map to link to each other instead of repeating explanations.

The critics only report and never edit, so they can run at the same time safely. The reviewer then applies all their findings in one pass. Where findings conflict, correctness beats clarity.

### Agents and models

| Agent | Role | Model | Effort |
|---|---|---|---|
| `tutorial-site-surveyor` | Survey an existing docs site (integration mode only) | Sonnet | medium |
| `tutorial-evidence-gatherer` | Collect design rationale, known issues and maintenance signals: git history, docs, TODO/FIXME, GitHub issues/PRs (advanced and stakeholder audiences only) | Sonnet | medium |
| `tutorial-plain-planner` | Translate the outline into a plain-language plan: component names, information flows, rules, assumptions, page plans (stakeholder audiences only) | Opus | medium |
| `tutorial-plain-writer` | Write one zero-code stakeholder page (one instance per page) | Opus | medium |
| `tutorial-analyst` | Choose the abstractions, relationships and chapter order | Opus | high |
| `tutorial-chapter-writer` | Write one chapter (one instance per chapter) | Opus | medium |
| `tutorial-critic-clarity` | Read the tutorial as the target reader would; flag confusion | Sonnet | medium |
| `tutorial-critic-code` | Check that every snippet is verbatim or honestly marked illustrative | Sonnet | medium |
| `tutorial-critic-accuracy` | Fact-check the prose, diagrams and API links against the code | Opus | high |
| `tutorial-reviewer` | Apply findings, enforce the rules, render | Opus | medium |

These are set in each agent's front matter (`model:` / `effort:`) in `agents/`. Once installed, each agent's full name is prefixed with the plugin name, e.g. `codebase-tutorial:tutorial-analyst`. See [Customising](#customising) to change them.

> **Cost:** a full run makes one analyst call, one writer call per chapter, three critic calls and one reviewer call, each of which explores the code. Most of the spend comes from the writers. `critique=off`, a smaller `max_abstractions`, or moving writers to Sonnet all reduce it.

---

## Quality checks

There are three layers of checks, so a tutorial that renders also reads correctly.

**1. Mechanical checks.** Two scripts in `skills/write/scripts/`, which you can also run yourself:

- **`check_snippets.py`**: every code block must be one of:
  - **verbatim**: `` ```{.python filename="src/x.py:42-58"} ``. The lines must appear in that file exactly; only indentation may differ, and code-annotation markers are ignored.
  - **illustrative**: `` ```{.python .illustrative filename="Simplified from src/x.py"} ``. These are reviewed by a critic instead.

  Executable `{python}` cells, uncaptioned blocks and bare ```` ```mermaid ```` fences all fail. A mismatch shows a diff against the closest region of the source file.

- **`check_links.py`**: checks relative links, `#anchors`, `[text](@ref)` mistakes (which render as silently broken links), and quartodoc **interlinks** against `objects.json`. An unresolved interlink also renders silently, as plain text, so this is the only way to catch one.

```bash
python check_snippets.py --repo <repo> --out <tutorial dir>
python check_links.py --out <tutorial dir> [--project <quarto project root>]
```

Both exit non-zero on failure. Writers self-check their own chapter before returning, and the reviewer must get both scripts passing.

**2. Critics.**
- **Clarity**: reads only the tutorial, as a newcomer would, without looking at the source. It flags undefined terms, leaps in logic, analogies that are unclear or patronising, and use cases left unresolved, and it scores each chapter from 1 to 5.
- **Code fidelity**: runs the snippet checker, then checks that illustrative code uses real names and signatures and isn't misleading.
- **Accuracy**: checks behaviour claims, call order, every diagram, and the API links against the source, with a `path:line` citation for every finding.

**3. Render.** `quarto render` with warnings treated as errors, so an unresolved cross-reference fails the build.

---

## Customising

Everything is plain Markdown. Edit a clone and load it with `claude --plugin-dir` (see [Developing locally](#developing-locally)). To keep your changes as your own version, fork the repository and add your fork as the marketplace instead.

| To change… | Edit |
|---|---|
| Audience presets, or to add a theme | `skills/write/references/style-presets.md`. A theme is a short persona paragraph plus where to apply it; then pass `theme=<name>` |
| How chapters are structured | `skills/write/references/chapter-guide.md` |
| Quarto conventions and recommended features | `skills/write/references/quarto-conventions.md` |
| Integration behaviour | `skills/write/references/site-integration.md` |
| Models and effort | The `model:` (`opus`, `sonnet`, `haiku`, `fable`, `inherit`) and `effort:` (`low` … `max`) fields at the top of each file in `agents/` |
| The pipeline itself | `skills/write/SKILL.md` |

---

## Troubleshooting

**`/codebase-tutorial:write` doesn't appear.** Run `claude plugin list` and check that `codebase-tutorial@bergam0t` shows as enabled. Then start a new session or run `/reload-plugins`. The `/plugin` **Errors** tab lists anything that failed to load.

**Adding the marketplace fails on a machine without a GitHub SSH key.** Set `CLAUDE_CODE_PLUGIN_PREFER_HTTPS=1` in your environment and try again. Claude Code then clones over HTTPS.

**"The plugin's agents aren't installed".** The skill was found but its agents weren't, which usually means only `skills/write/` was copied somewhere by hand. Install the plugin as shown under [Installation](#installation) so the skill and agents arrive together.

**Lots of permission prompts.** The agents run `python`, `git` and `quarto` through Bash, and each new command asks for approval in the default permission mode. To reduce the prompts, approve with "don't ask again" for the project when they first appear, or add allow rules such as `Bash(quarto render:*)` and `Bash(python:*)` to your settings.

**"Quarto not installed, render skipped".** Install Quarto from <https://quarto.org/docs/get-started/>. The tutorial is still written; it just hasn't been validated by a render.

**`quartodoc build` fails with `parse_numpy() got an unexpected keyword argument 'allow_section_blank_line'`.** Your installed griffe version is newer than quartodoc supports. Pin an older one:

```bash
pip install "griffe<1.10"
```

**My tutorial in an existing site has no code windows or line highlighting.** In an existing site the default extensions are only added if you agree (or they are already installed and enabled), and a run that can't ask counts as a "no". The final report lists what was skipped. See [In an existing Quarto / quartodoc site](#quarto-extensions).

**The advanced pages say GitHub wasn't checked.** The evidence step needs `gh` installed and signed in, a `github.com` remote, and permission to run it. Run `gh auth status` in the same terminal, then see [GitHub access](#github-access). The final report names the reason.

**An extension failed to install.** `quarto add` needs network access to GitHub. The run continues without that extension, and the final report lists it as skipped. Re-run once you're online, or install it yourself with `quarto add <source>` in the tutorial folder.

**`code-window` or `highlight-text` was skipped.** Both need Quarto 1.10.19 or newer. Update Quarto from <https://quarto.org/docs/get-started/>.

**`quartodoc build` can't find your package.** quartodoc needs the package to be importable. Install it (`pip install -e .`) or set `PYTHONPATH` to the folder that contains it.

**Interlinks show as plain code instead of links.** The name isn't in `objects.json`, either because the reference hasn't been built yet or because the name is wrong. Run `quartodoc build`, then `check_links.py` to see which names fail.

**The section folder already exists.** In integration mode the skill stops rather than overwriting it. Delete or rename the folder, or pass `section=<new name>`.

**I want to see what the agents decided.** The plan and evidence survive in the tutorial folder anyway: `_outline.yaml`, `_evidence.yaml`, `_plain-outline.yaml`, `_site-profile.yaml` and `_styles/`. Re-run with `keep_work` to also keep `_work/`, which holds:
- `outline.yaml`, `evidence.yaml` and `style.md` (working copies of the above)
- `site-profile.yaml` (in integration mode)
- `critique/*.yaml` (every critic finding)

---

## Repository layout

```
.claude-plugin/
  plugin.json                    # plugin manifest: name, version, metadata
  marketplace.json               # makes this repo its own marketplace ("bergam0t")
agents/
  tutorial-analyst.md            # outline: abstractions, relationships, order
  tutorial-chapter-writer.md     # one chapter
  tutorial-critic-clarity.md     # reader's-eye critique
  tutorial-critic-code.md        # snippet fidelity critique
  tutorial-critic-accuracy.md    # factual critique
  tutorial-reviewer.md           # apply fixes, enforce rules, render
  tutorial-site-surveyor.md      # survey an existing docs site
  tutorial-evidence-gatherer.md  # rationale, known issues & maintenance signals
  tutorial-plain-planner.md      # plain-language plan for stakeholder audiences
  tutorial-plain-writer.md       # one zero-code stakeholder page
skills/
  add-audience/                  # → /codebase-tutorial:add-audience
    SKILL.md                     # add a voice to an existing tutorial, reusing the stored analysis
  update/                        # → /codebase-tutorial:update
    SKILL.md                     # refresh only the stale chapters
    templates/
      tutorial-freshness.yml     # GitHub Actions workflow to copy into your repo
  write/                         # → /codebase-tutorial:write
    SKILL.md                     # the orchestrator
    references/
      outline-schema.md          # contract between the analyst and writers
      chapter-guide.md           # how to write a chapter
      style-presets.md           # audiences and themes
      quarto-conventions.md      # hard rules + recommended Quarto features
      critique-format.md         # findings format for critics and reviewer
      site-integration.md        # integration mode rules and site-profile schema
      multi-audience.md          # switchable versions for several audiences
      evidence.md                # evidence.yaml schema and citing rules (advanced)
      extensions.md              # vetted Quarto extensions: pins, order, usage notes
      stakeholder.md             # zero-code rules, page menu and plans, plain-outline schema
      config.md                  # .codebase-tutorial.yml and the generation record
      learning.md                # self-tests, exercises, reading paths, first contribution
    scripts/
      check_snippets.py          # verbatim / included / illustrative snippet checker (+ drift hashes)
      check_links.py             # link, anchor and interlink checker
      add_audience_switcher.py   # inserts the reading-level switcher (multi-audience)
      relayout.py                # move a flat tutorial into an audience folder, re-basing links
      write_record.py            # commit info, and write/extend the _generation.json record
      check_drift.py             # which chapters depend on changed source files
      check_tutorial.py          # drift + snippets + links in one go (CI entry point)
CHANGELOG.md
RELEASING.md                     # how to cut a release
LICENSE                          # MIT (original + this derivative)
README.md
```

---

## Credits

This skill is a derivative work of [AI Codebase Knowledge Builder](https://github.com/The-Pocket/PocketFlow-Tutorial-Codebase-Knowledge) (PocketFlow Tutorial-Codebase-Knowledge) by Zachary Huang / The Pocket, which is released under the MIT License.

The following were adapted from that project's `nodes.py` pipeline:
- the overall pipeline: identify abstractions, analyse relationships, order chapters, write chapters, combine
- the text of the prompts that identify abstractions, analyse relationships, order chapters and write chapters. These are now in `tutorial-analyst.md`, `chapter-guide.md` and `style-presets.md`
- the rules for chapter filenames and the relationship diagram

The agent orchestration, Quarto output, critique stage, checking scripts and quartodoc integration are new.

Generated tutorials keep the original project's attribution line, in the page footer (standalone mode) or at the end of the overview page (integration mode).

---

## License

[MIT](LICENSE). This applies both to the original work and to the changes made here:

```
Copyright (c) 2025 Zachary Huang
Copyright (c) 2026 Sammi Rosser
```

If you redistribute this plugin or a substantial part of it, keep the copyright and permission notice. The LICENSE file sits at the plugin root, so it's included in every plugin install.

Tutorials generated *by* the skill are output from your own repository. The license doesn't apply to them.
