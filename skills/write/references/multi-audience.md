# Multiple audiences

This applies when `audience` lists more than one audience, e.g. `audience=beginner,intermediate`. The skill then produces one complete version of the tutorial per audience, from **one shared outline**, so every version has the same chapters, order and filenames. A reading-level switcher at the top of every page jumps to the same page at another level. Everything else in the pipeline is unchanged. This file covers only what is different.

Patterns marked **(tested)** were verified with Quarto 1.11.

## Parsing the list

- Split `audience` on commas into an ordered list. The **first** audience is the default (listed first in the switcher, navbar and landing page).
- Each entry is a preset name (`beginner`, `intermediate`) or a quoted free-text description. A comma inside quotes doesn't split. For example, `audience=beginner,"data scientists, new to async"` gives two audiences.
- Give each audience:
  - a **slug**: lowercase, hyphens only, used as its folder name. Presets use their own name; derive a short one for free-text audiences (`data-scientists`).
  - a short **label** for buttons (`Beginner`, `Data scientists`), in the target language.
- Slugs must be unique.
- One audience in the list means the normal single-audience layout: no subfolders and no switcher.

## Constraints

- **Format must be `website`.** Books number chapters across the whole book, so two versions of every chapter can't live in one book. If `format=book` was passed explicitly, ask the user whether to switch to a website or run the skill once per audience (separate books, no switcher). If no format was given, use `website` and say so.
- **Integration mode** needs a website project too. If the site is a Quarto book, stop and explain: either run once per audience into different `section=` folders, or pick one audience.
- A `theme` applies to every audience.

## Layout

```
<output>/                       # standalone; or <docs>/<section>/ in integration mode
  index.qmd                     # landing page: summary, overview diagram, "Choose your level" buttons
  _quarto.yml                   # standalone only
  beginner/
    index.qmd                   # this audience's overview (summary, diagram, chapter list)
    01_router.qmd ...           # same filenames in every audience folder
    glossary.qmd                # definitions pitched at this audience
  intermediate/
    index.qmd
    01_router.qmd ...
    glossary.qmd
  _work/
    outline.yaml                # shared by every audience
    style-beginner.md           # one style block per audience
    style-intermediate.md
    critique/<slug>/*.yaml      # critic findings per audience
```

## Pipeline changes

1. **Style blocks**: resolve one per audience into `_work/style-<slug>.md`.
2. **Analyst**: unchanged, and runs once. Tell it the outline will be written up for all listed audiences, so the chapter split and order must suit all of them, and descriptions should be pitched at the least experienced one.
3. **Writers**: one per (audience × chapter). Each brief is the usual chapter brief, plus:
   - that audience's style block
   - output path `<output>/<slug>/<filename>`
   - the self-check command with `--out <output>/<slug>`

   Links stay within the audience folder (the filenames in the chapter list are relative, so they already do). Writers must **not** link to other audience folders or add a switcher; the orchestrator adds it. Spawn writers in parallel, with up to about 12 Agent calls per message, grouping by audience when there are more.
4. **Assemble**, for each audience: write `<slug>/index.qmd` and `<slug>/glossary.qmd` exactly as in single-audience mode (in website form), with the glossary definitions pitched at that audience. Then write the landing page and config (below), then run the switcher script:
   ```
   python <scripts>/add_audience_switcher.py --root <output> --audiences "beginner=Beginner,intermediate=Intermediate" --label "Reading level"
   ```
   Translate `--label` and the labels into the target language. The script is idempotent: re-run it after any later change to the file set.
5. **Critique**: run the three critics **per audience**, each over `<output>/<slug>` with that audience's style block, writing to `_work/critique/<slug>/`. That is 3 × (number of audiences) critics, all read-only, so they can run in parallel in batches of about 12.
6. **Review**: one reviewer **per audience**, in parallel. They edit disjoint folders. Brief each with its own folder, style block and findings, plus **`render: skip`**, because concurrent renders of one project collide. Run the link checker with `--project <output>`, so that switcher links into sibling folders resolve.
7. **Render once** at the end yourself: `quarto render <output>` (in integration mode, `quarto render <docs>/<section>`). On errors, resume the reviewer for the affected audience with the error text, then render again. Do this at most twice.

## Landing page (`<output>/index.qmd`)

Use website form: front matter `title: "Tutorial: <project_name>"` (or `"Tutorial"` in integration mode). Then:

1. The outline `summary`.
2. The relationship diagram (as in single-audience `index.qmd`).
3. `## Choose your reading level`, with one button per audience in list order, each followed by the `Reader` line from its style block:
   ```markdown
   [Beginner](beginner/index.qmd){.btn .btn-primary} New to programming concepts as well as to this codebase.

   [Intermediate](intermediate/index.qmd){.btn .btn-outline-primary} Knows the language, new to this codebase.
   ```
   The first (default) audience uses `.btn-primary`, the others `.btn-outline-primary`.
4. The attribution line (integration mode only; standalone mode uses `page-footer`).

## Navigation **(tested)**

Give each audience its own sidebar, with the sidebar `id` set to the slug, plus navbar entries for switching at the top level. Quarto shows whichever sidebar contains the current page, so readers stay within their chosen level as they move through the chapters.

**Standalone `_quarto.yml`** (replacing the single-audience `website:` block, with every other key as before):
```yaml
website:
  title: "Tutorial: <project_name>"
  navbar:
    left:
      - text: Beginner
        href: beginner/index.qmd
      - text: Intermediate
        href: intermediate/index.qmd
    tools:                       # omit if repo_url is "none"
      - icon: git
        href: <repo_url>
  sidebar:
    - id: beginner
      title: Beginner
      style: docked
      contents:
        - beginner/index.qmd
        - beginner/01_<...>.qmd
        - beginner/glossary.qmd
    - id: intermediate
      title: Intermediate
      style: docked
      contents:
        - intermediate/index.qmd
        - intermediate/01_<...>.qmd
        - intermediate/glossary.qmd
  page-navigation: true
  page-footer:
    center: "Generated by [AI Codebase Knowledge Builder](https://github.com/The-Pocket/PocketFlow-Tutorial-Codebase-Knowledge)"
```

**Integration mode**: follow `site-integration.md`, with these differences:
- The navbar item becomes a menu:
  ```yaml
  - text: Tutorial
    menu:
      - text: Beginner
        href: tutorial/beginner/index.qmd
      - text: Intermediate
        href: tutorial/intermediate/index.qmd
  ```
- Add one sidebar per audience, with id `<section>-<slug>` and the contents prefixed `<section>/<slug>/`.
- `tutorial/index.qmd` is the landing page.

## The switcher **(tested)**

`add_audience_switcher.py` inserts this right after each page's front matter, between `<!-- audience-switcher:start/end -->` markers:

```markdown
::: {.audience-switcher .mb-4}
[Reading level:]{.text-muted .small} [Beginner](01_router.qmd){.btn .btn-sm .btn-primary .active aria-current="page"} [Intermediate](../intermediate/01_router.qmd){.btn .btn-sm .btn-outline-primary}
:::
```

- If a page doesn't exist at another level, that button links to that level's `index.qmd`.
- The buttons use Bootstrap classes that Quarto's HTML themes already include, so no extra CSS or JavaScript is needed.
- Never edit the switcher by hand. Re-run the script instead.

## Reviewer checks (multi-audience additions)

- Every audience folder has the same set of chapter filenames as the outline, plus `index.qmd` and `glossary.qmd`.
- Every page has exactly one switcher block. If any page lacks one, re-run the script.
- Versions agree on facts. They may differ in depth, tone and code length, but never in what the code does. If the accuracy findings for one audience reveal an error, check that chapter in the other audiences too.
